from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.ai_platform.errors import GatewayDisabledError
from AUTONOMY_ENGINE.ai_platform.provider_adapters import (
    OpenAIChatProvider,
    VLLMChatProvider,
)
from AUTONOMY_ENGINE.ai_platform.server_composition import (
    AICompositionConfigurationError,
    build_model_gateway_from_environment,
)


class FakeAuthorization:
    def authorize_request(self, *args, **kwargs):
        raise AssertionError("Authorization is injected, not called at build time")


class FakeUsageControl:
    def reserve(self, *args, **kwargs):
        raise AssertionError("Usage control is injected, not called at build time")

    def settle(self, *args, **kwargs):
        raise AssertionError("Usage control is injected, not called at build time")

    def release(self, *args, **kwargs):
        raise AssertionError("Usage control is injected, not called at build time")


class FakeObservability:
    def emit(self, *args, **kwargs):
        raise AssertionError("Observability is injected, not called at build time")


def dependencies():
    return {
        "authorization": FakeAuthorization(),
        "usage_control": FakeUsageControl(),
        "observability": FakeObservability(),
    }


def openai_environment() -> dict[str, str]:
    return {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "gpt-test-model",
        "HOMIO_AI_OPENAI_API_KEY": "test-secret-do-not-log",
        "HOMIO_AI_OPENAI_MODEL_ID": "gpt-test-model",
    }


def build(environ: dict[str, str]):
    return build_model_gateway_from_environment(
        **dependencies(),
        environ=environ,
    )


def test_ai_gateway_stays_disabled_without_explicit_opt_in() -> None:
    with pytest.raises(GatewayDisabledError):
        build({})


def test_ai_gateway_stays_disabled_when_explicitly_false() -> None:
    with pytest.raises(GatewayDisabledError):
        build({"HOMIO_AI_ENABLED": "false"})


def test_openai_provider_is_registered_without_network_activity() -> None:
    gateway = build(openai_environment())

    assert gateway._settings.enabled is True
    assert gateway._settings.default_model_id == "gpt-test-model"
    assert gateway._model_registry.model_ids == ("gpt-test-model",)
    assert gateway._model_registry.resolve("gpt-test-model").provider_id == "openai"

    provider = gateway._provider_resolver.get("openai")
    assert isinstance(provider, OpenAIChatProvider)
    assert "test-secret-do-not-log" not in repr(provider)


def test_provider_key_without_model_id_is_rejected() -> None:
    environ = openai_environment()
    environ.pop("HOMIO_AI_OPENAI_MODEL_ID")

    with pytest.raises(
        AICompositionConfigurationError,
        match="both its server API key and model ID",
    ):
        build(environ)


def test_model_id_without_provider_key_is_rejected() -> None:
    environ = openai_environment()
    environ.pop("HOMIO_AI_OPENAI_API_KEY")

    with pytest.raises(
        AICompositionConfigurationError,
        match="both its server API key and model ID",
    ):
        build(environ)


def test_unknown_default_model_is_rejected() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_DEFAULT_MODEL_ID"] = "unconfigured-model"

    with pytest.raises(
        AICompositionConfigurationError,
        match="must match a configured model ID",
    ):
        build(environ)


def test_unknown_fallback_model_is_rejected() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_FALLBACK_MODEL_IDS"] = "not-configured"

    with pytest.raises(
        AICompositionConfigurationError,
        match="Every fallback model must be explicitly configured",
    ):
        build(environ)


def test_duplicate_fallback_models_are_rejected() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_FALLBACK_MODEL_IDS"] = (
        "gpt-test-model,gpt-test-model"
    )

    with pytest.raises(
        AICompositionConfigurationError,
        match="contains duplicates",
    ):
        build(environ)


def test_default_model_cannot_also_be_fallback() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_FALLBACK_MODEL_IDS"] = "gpt-test-model"

    with pytest.raises(
        AICompositionConfigurationError,
        match="default model cannot also be a fallback",
    ):
        build(environ)


def test_invalid_enable_flag_fails_closed() -> None:
    with pytest.raises(
        AICompositionConfigurationError,
        match="must be explicitly set",
    ):
        build({"HOMIO_AI_ENABLED": "yes"})


def test_provider_credentials_are_not_enough_to_enable_ai() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_ENABLED"] = "false"

    with pytest.raises(GatewayDisabledError):
        build(environ)


def test_incomplete_vllm_configuration_is_rejected() -> None:
    environ = {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "local-test-model",
        "HOMIO_AI_VLLM_BASE_URL": "https://vllm.internal/v1",
        "HOMIO_AI_VLLM_MODEL_ID": "local-test-model",
    }

    with pytest.raises(
        AICompositionConfigurationError,
        match="endpoint, API key and model ID",
    ):
        build(environ)


def test_vllm_http_endpoint_is_rejected() -> None:
    environ = {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "local-test-model",
        "HOMIO_AI_VLLM_BASE_URL": "http://vllm.internal/v1",
        "HOMIO_AI_VLLM_API_KEY": "test-vllm-secret",
        "HOMIO_AI_VLLM_MODEL_ID": "local-test-model",
    }

    with pytest.raises(
        AICompositionConfigurationError,
        match="vLLM provider configuration is invalid",
    ):
        build(environ)


def test_vllm_provider_is_registered_without_network_activity() -> None:
    environ = {
        "HOMIO_AI_ENABLED": "true",
        "HOMIO_AI_DEFAULT_MODEL_ID": "local-test-model",
        "HOMIO_AI_VLLM_BASE_URL": "https://vllm.internal/v1",
        "HOMIO_AI_VLLM_API_KEY": "test-vllm-secret",
        "HOMIO_AI_VLLM_MODEL_ID": "local-test-model",
    }

    gateway = build(environ)

    assert gateway._model_registry.model_ids == ("local-test-model",)
    assert gateway._model_registry.resolve("local-test-model").provider_id == "vllm"

    provider = gateway._provider_resolver.get("vllm")
    assert isinstance(provider, VLLMChatProvider)
    assert "test-vllm-secret" not in repr(provider)


def test_missing_authorization_dependency_fails_closed() -> None:
    environ = openai_environment()

    with pytest.raises(
        AICompositionConfigurationError,
        match="authorization dependency",
    ):
        build_model_gateway_from_environment(
            authorization=object(),
            usage_control=FakeUsageControl(),
            observability=FakeObservability(),
            environ=environ,
        )


def test_invalid_token_limit_fails_closed() -> None:
    environ = openai_environment()
    environ["HOMIO_AI_MAX_OUTPUT_TOKENS"] = "0"

    with pytest.raises(
        AICompositionConfigurationError,
        match="positive integer",
    ):
        build(environ)
