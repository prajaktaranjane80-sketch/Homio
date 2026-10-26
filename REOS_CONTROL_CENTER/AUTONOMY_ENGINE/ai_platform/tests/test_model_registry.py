from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    AIRequest,
    ModelRoute,
    ProviderRequest,
    ProviderResponse,
    RequestContext,
)
from AUTONOMY_ENGINE.ai_platform.errors import ModelResolutionError
from AUTONOMY_ENGINE.ai_platform.model_gateway import ModelGateway
from AUTONOMY_ENGINE.ai_platform.model_registry import (
    ModelDefinition,
    ModelRegistry,
    ProviderRegistry,
)
from AUTONOMY_ENGINE.ai_platform.settings import GatewaySettings


class FakeProvider:
    def generate(self, request: ProviderRequest) -> ProviderResponse:
        raise AssertionError("This registry test must not call a provider")


def make_definition(
    *,
    model_id: str = "model-a",
    provider_id: str = "provider-a",
    enabled: bool = True,
    capabilities: tuple[str, ...] = ("text_generation",),
    aliases: tuple[str, ...] = (),
    provider_version: str = "adapter-v1",
    model_version: str = "model-v1",
) -> ModelDefinition:
    return ModelDefinition(
        route=ModelRoute(
            provider_id=provider_id,
            model_id=model_id,
            max_input_chars=200,
            max_output_tokens=128,
            enabled=enabled,
        ),
        provider_version=provider_version,
        model_version=model_version,
        capabilities=capabilities,
        aliases=aliases,
    )


def make_registry(
    *definitions: ModelDefinition,
    allowed_provider_ids: tuple[str, ...] = ("provider-a",),
) -> ModelRegistry:
    return ModelRegistry(
        definitions,
        allowed_provider_ids=allowed_provider_ids,
    )


def test_resolves_explicit_model_allowlist() -> None:
    definition = make_definition()
    registry = make_registry(definition)

    assert registry.resolve("model-a") == definition.route
    assert registry.model_ids == ("model-a",)
    assert registry.allowed_provider_ids == ("provider-a",)


def test_unknown_model_is_rejected() -> None:
    registry = make_registry(make_definition())

    with pytest.raises(ModelResolutionError):
        registry.resolve("unlisted-model")


def test_disabled_model_is_rejected() -> None:
    registry = make_registry(make_definition(enabled=False))

    with pytest.raises(ModelResolutionError):
        registry.resolve("model-a")


def test_alias_resolves_deterministically_and_preserves_versions() -> None:
    definition = make_definition(
        aliases=("stable-chat",),
        provider_version="adapter-v2",
        model_version="model-release-2026-10",
    )
    registry = make_registry(definition)

    resolved = registry.resolve_definition("stable-chat")

    assert resolved is definition
    assert resolved.route.model_id == "model-a"
    assert resolved.provider_version == "adapter-v2"
    assert resolved.model_version == "model-release-2026-10"
    assert registry.resolve("stable-chat") == definition.route


def test_alias_cannot_shadow_another_canonical_model() -> None:
    first = make_definition(
        model_id="model-a",
        aliases=("model-b",),
    )
    second = make_definition(model_id="model-b")

    with pytest.raises(ValueError, match="globally unique"):
        make_registry(first, second)


def test_duplicate_canonical_model_ids_are_rejected() -> None:
    first = make_definition(model_id="model-a")
    second = make_definition(model_id="model-a", model_version="model-v2")

    with pytest.raises(ValueError, match="duplicate"):
        make_registry(first, second)


def test_model_route_must_reference_an_allowed_provider() -> None:
    definition = make_definition(provider_id="provider-a")

    with pytest.raises(ValueError, match="provider allowlist"):
        make_registry(
            definition,
            allowed_provider_ids=("provider-b",),
        )


def test_registry_rejects_an_unconfigured_capability() -> None:
    with pytest.raises(ValueError, match="unsupported model capability"):
        make_definition(capabilities=("shell_execution",))


def test_duplicate_capabilities_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate model capabilities"):
        make_definition(
            capabilities=("text_generation", "text_generation"),
        )


def test_embedding_only_model_is_not_a_text_generation_route() -> None:
    definition = make_definition(
        model_id="embedding-a",
        capabilities=("embeddings",),
    )
    registry = make_registry(definition)

    with pytest.raises(ModelResolutionError):
        registry.resolve("embedding-a")

    assert (
        registry.resolve_definition(
            "embedding-a",
            required_capability="embeddings",
        )
        is definition
    )


def test_gateway_fails_closed_for_model_without_generation_capability() -> None:
    registry = make_registry(
        make_definition(
            model_id="embedding-a",
            capabilities=("embeddings",),
        )
    )
    gateway = ModelGateway(
        settings=GatewaySettings(
            enabled=True,
            default_model_id="embedding-a",
        ),
        model_registry=registry,
        provider_resolver=ProviderRegistry({}),
        authorization=object(),
        usage_control=object(),
        observability=object(),
    )
    request = AIRequest(
        request_id="request-1",
        operation="property.search",
        input_text="Find a two bedroom apartment.",
        context=RequestContext(
            principal_id="user-1",
            tenant_id="tenant-1",
            authentication_context_ref="auth-1",
            correlation_id="trace-1",
        ),
    )

    with pytest.raises(ModelResolutionError):
        gateway.complete(request)


def test_provider_registry_returns_only_registered_adapters() -> None:
    provider = FakeProvider()
    registry = ProviderRegistry({"provider-a": provider})

    assert registry.get("provider-a") is provider
    assert registry.provider_ids == ("provider-a",)
    assert registry.get("provider-b") is None


def test_model_selection_is_separate_from_provider_availability() -> None:
    model_registry = make_registry(make_definition())
    provider_registry = ProviderRegistry({})

    assert model_registry.resolve("model-a").model_id == "model-a"
    assert provider_registry.get("provider-a") is None


def test_provider_registry_rejects_adapter_without_generate() -> None:
    with pytest.raises(TypeError, match="callable generate"):
        ProviderRegistry({"provider-a": object()})


def test_provider_registry_rejects_normalized_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="duplicate normalized"):
        ProviderRegistry(
            {
                "provider-a": FakeProvider(),
                " provider-a ": FakeProvider(),
            }
        )


def test_invalid_model_identifier_fails_closed() -> None:
    registry = make_registry(make_definition())

    with pytest.raises(ModelResolutionError):
        registry.resolve("  ")
