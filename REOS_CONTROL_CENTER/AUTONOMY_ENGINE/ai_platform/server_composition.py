"""Trusted server-side composition for the HOMIO AI model gateway.

This module wires the existing provider adapters and registries into the
existing ModelGateway. Authentication, tenant verification, domain policy,
usage accounting and observability remain owned by their existing runtime
owners and must be injected by the server composition root.

No provider is enabled by default. This module never makes a network request
while constructing the gateway and never logs or returns provider secrets.
"""

from __future__ import annotations

from collections.abc import Mapping
import os

from .contracts import ModelRoute
from .errors import GatewayDisabledError
from .model_gateway import ModelGateway
from .model_registry import (
    ModelDefinition,
    ModelRegistry,
    ProviderRegistry,
)
from .ports import (
    AuthorizationPort,
    ObservabilityPort,
    UsageControlPort,
)
from .provider_adapters import (
    OpenAIChatProvider,
    VLLMChatProvider,
)
from .settings import GatewaySettings


class AICompositionConfigurationError(RuntimeError):
    """Safe configuration error that never includes environment values."""


def _read_text(
    environ: Mapping[str, str],
    name: str,
    *,
    required: bool = False,
    maximum: int = 2048,
) -> str | None:
    value = environ.get(name)

    if value is None:
        if required:
            raise AICompositionConfigurationError(
                f"Required AI configuration is missing: {name}"
            )
        return None

    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(char) < 32 for char in value)
    ):
        raise AICompositionConfigurationError(
            f"AI configuration is invalid: {name}"
        )

    return value


def _read_enabled(environ: Mapping[str, str]) -> bool:
    value = _read_text(environ, "HOMIO_AI_ENABLED")

    if value is None:
        return False

    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False

    raise AICompositionConfigurationError(
        "HOMIO_AI_ENABLED must be explicitly set to true or false"
    )


def _read_positive_int(
    environ: Mapping[str, str],
    name: str,
    *,
    default: int,
    maximum: int,
) -> int:
    value = _read_text(environ, name)

    if value is None:
        return default

    if not value.isdecimal():
        raise AICompositionConfigurationError(
            f"AI configuration must be a positive integer: {name}"
        )

    parsed = int(value)
    if parsed < 1 or parsed > maximum:
        raise AICompositionConfigurationError(
            f"AI configuration is outside its permitted range: {name}"
        )

    return parsed


def _read_timeout(environ: Mapping[str, str]) -> float:
    value = _read_text(environ, "HOMIO_AI_TIMEOUT_SECONDS")

    if value is None:
        return 30.0

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise AICompositionConfigurationError(
            "HOMIO_AI_TIMEOUT_SECONDS is invalid"
        ) from None

    if parsed <= 0 or parsed > 120:
        raise AICompositionConfigurationError(
            "HOMIO_AI_TIMEOUT_SECONDS must be greater than 0 and at most 120"
        )

    return parsed


def _read_fallbacks(environ: Mapping[str, str]) -> tuple[str, ...]:
    value = _read_text(
        environ,
        "HOMIO_AI_FALLBACK_MODEL_IDS",
        maximum=4096,
    )

    if value is None or value == "":
        return ()

    parts = value.split(",")
    normalized = tuple(part.strip() for part in parts)

    if any(not part for part in normalized):
        raise AICompositionConfigurationError(
            "HOMIO_AI_FALLBACK_MODEL_IDS contains an empty entry"
        )

    if any(part != original for part, original in zip(normalized, parts)):
        # Surrounding whitespace is normalized only for this list.
        pass

    if len(set(normalized)) != len(normalized):
        raise AICompositionConfigurationError(
            "HOMIO_AI_FALLBACK_MODEL_IDS contains duplicates"
        )

    return normalized


def _require_port_methods(
    dependency: object,
    *,
    name: str,
    methods: tuple[str, ...],
) -> None:
    if dependency is None or any(
        not callable(getattr(dependency, method, None))
        for method in methods
    ):
        raise AICompositionConfigurationError(
            f"The existing {name} dependency is missing or incomplete"
        )


def build_model_gateway_from_environment(
    *,
    authorization: AuthorizationPort,
    usage_control: UsageControlPort,
    observability: ObservabilityPort,
    environ: Mapping[str, str] | None = None,
) -> ModelGateway:
    """Build one configured gateway using explicit server-owned settings.

    Required existing dependencies:
      * authorization: trusted identity and existing domain-policy adapter
      * usage_control: durable reservation and settlement implementation
      * observability: approved redacted event sink

    Environment variables:
      HOMIO_AI_ENABLED=true
      HOMIO_AI_DEFAULT_MODEL_ID=<configured model ID>

      HOMIO_AI_OPENAI_API_KEY=<server secret>
      HOMIO_AI_OPENAI_MODEL_ID=<provider model ID>

      HOMIO_AI_VLLM_BASE_URL=https://<private-host>/v1
      HOMIO_AI_VLLM_API_KEY=<server secret>
      HOMIO_AI_VLLM_MODEL_ID=<provider model ID>

      HOMIO_AI_FALLBACK_MODEL_IDS=<comma-separated configured model IDs>
      HOMIO_AI_MAX_INPUT_CHARS=12000
      HOMIO_AI_MAX_OUTPUT_TOKENS=512
      HOMIO_AI_MAX_OUTPUT_CHARS=24000
      HOMIO_AI_TIMEOUT_SECONDS=30

    Providers are configured as complete pairs; partial configuration fails
    closed. vLLM always requires an API key and the adapter rejects insecure
    HTTP by default. Neither provider is contacted during construction.
    """
    source = os.environ if environ is None else environ

    if not isinstance(source, Mapping):
        raise AICompositionConfigurationError(
            "AI environment configuration must be a mapping"
        )

    # Keep disabled deployments safe even when provider credentials are present.
    if not _read_enabled(source):
        raise GatewayDisabledError()

    _require_port_methods(
        authorization,
        name="authorization",
        methods=("authorize_request",),
    )
    _require_port_methods(
        usage_control,
        name="usage control",
        methods=("reserve", "settle", "release"),
    )
    _require_port_methods(
        observability,
        name="observability",
        methods=("emit",),
    )

    max_input_chars = _read_positive_int(
        source,
        "HOMIO_AI_MAX_INPUT_CHARS",
        default=12_000,
        maximum=1_000_000,
    )
    max_output_tokens = _read_positive_int(
        source,
        "HOMIO_AI_MAX_OUTPUT_TOKENS",
        default=512,
        maximum=32_768,
    )
    max_output_chars = _read_positive_int(
        source,
        "HOMIO_AI_MAX_OUTPUT_CHARS",
        default=24_000,
        maximum=1_000_000,
    )
    timeout = _read_timeout(source)
    fallback_model_ids = _read_fallbacks(source)

    providers: dict[str, object] = {}
    definitions: list[ModelDefinition] = []

    openai_key = _read_text(
        source,
        "HOMIO_AI_OPENAI_API_KEY",
        maximum=8192,
    )
    openai_model = _read_text(
        source,
        "HOMIO_AI_OPENAI_MODEL_ID",
        maximum=256,
    )

    if (openai_key is None) != (openai_model is None):
        raise AICompositionConfigurationError(
            "OpenAI requires both its server API key and model ID"
        )

    if openai_key is not None and openai_model is not None:
        try:
            providers["openai"] = OpenAIChatProvider(api_key=openai_key)
            definitions.append(
                ModelDefinition(
                    route=ModelRoute(
                        provider_id="openai",
                        model_id=openai_model,
                        max_input_chars=max_input_chars,
                        max_output_tokens=max_output_tokens,
                    ),
                    provider_version="openai-compatible-v1",
                    model_version=openai_model,
                    capabilities=("text_generation",),
                )
            )
        except (TypeError, ValueError):
            raise AICompositionConfigurationError(
                "OpenAI provider configuration is invalid"
            ) from None

    vllm_url = _read_text(
        source,
        "HOMIO_AI_VLLM_BASE_URL",
        maximum=2048,
    )
    vllm_key = _read_text(
        source,
        "HOMIO_AI_VLLM_API_KEY",
        maximum=8192,
    )
    vllm_model = _read_text(
        source,
        "HOMIO_AI_VLLM_MODEL_ID",
        maximum=256,
    )

    vllm_values = (vllm_url, vllm_key, vllm_model)
    if any(value is not None for value in vllm_values) and not all(
        value is not None for value in vllm_values
    ):
        raise AICompositionConfigurationError(
            "vLLM requires its HTTPS endpoint, API key and model ID"
        )

    if vllm_url is not None and vllm_key is not None and vllm_model is not None:
        try:
            providers["vllm"] = VLLMChatProvider(
                base_url=vllm_url,
                api_key=vllm_key,
            )
            definitions.append(
                ModelDefinition(
                    route=ModelRoute(
                        provider_id="vllm",
                        model_id=vllm_model,
                        max_input_chars=max_input_chars,
                        max_output_tokens=max_output_tokens,
                    ),
                    provider_version="vllm-openai-compatible-v1",
                    model_version=vllm_model,
                    capabilities=("text_generation",),
                )
            )
        except (TypeError, ValueError):
            raise AICompositionConfigurationError(
                "vLLM provider configuration is invalid"
            ) from None

    if not definitions:
        raise AICompositionConfigurationError(
            "At least one complete provider and model configuration is required"
        )

    default_model_id = _read_text(
        source,
        "HOMIO_AI_DEFAULT_MODEL_ID",
        required=True,
        maximum=256,
    )
    configured_model_ids = {definition.route.model_id for definition in definitions}

    if default_model_id not in configured_model_ids:
        raise AICompositionConfigurationError(
            "HOMIO_AI_DEFAULT_MODEL_ID must match a configured model ID"
        )

    if default_model_id in fallback_model_ids:
        raise AICompositionConfigurationError(
            "The default model cannot also be a fallback model"
        )

    if not set(fallback_model_ids).issubset(configured_model_ids):
        raise AICompositionConfigurationError(
            "Every fallback model must be explicitly configured"
        )

    try:
        settings = GatewaySettings(
            enabled=True,
            default_model_id=default_model_id,
            max_input_chars=max_input_chars,
            max_output_tokens=max_output_tokens,
            max_output_chars=max_output_chars,
            request_timeout_seconds=timeout,
            fallback_model_ids=fallback_model_ids,
        )
        model_registry = ModelRegistry(
            definitions,
            allowed_provider_ids=tuple(providers),
        )
        provider_registry = ProviderRegistry(providers)
    except (TypeError, ValueError):
        raise AICompositionConfigurationError(
            "AI model registry or gateway settings are invalid"
        ) from None

    return ModelGateway(
        settings=settings,
        model_registry=model_registry,
        provider_resolver=provider_registry,
        authorization=authorization,
        usage_control=usage_control,
        observability=observability,
    )


__all__ = (
    "AICompositionConfigurationError",
    "build_model_gateway_from_environment",
)
