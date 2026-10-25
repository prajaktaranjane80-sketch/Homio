from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.ai_platform.contracts import (
    AIRequest,
    ModelRoute,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    RequestContext,
)
from AUTONOMY_ENGINE.ai_platform.settings import GatewaySettings


def make_context() -> RequestContext:
    return RequestContext(
        principal_id="user-1",
        tenant_id="tenant-1",
        authentication_context_ref="auth-context-1",
        correlation_id="trace-1",
    )


def test_request_and_context_are_immutable_and_normalized() -> None:
    context = make_context()
    request = AIRequest(
        request_id="request-1",
        operation="property.search",
        input_text="  two bedroom apartment  ",
        context=context,
    )
    assert request.input_text == "two bedroom apartment"
    assert request.context is context

    with pytest.raises((AttributeError, TypeError)):
        request.request_id = "other"  # type: ignore[misc]


def test_request_rejects_empty_prompt_and_invalid_operation() -> None:
    with pytest.raises(ValueError, match="input_text"):
        AIRequest("r1", "property.search", "  ", make_context())

    with pytest.raises(ValueError, match="operation"):
        AIRequest("r1", "Property Search", "hello", make_context())


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "10"])
def test_request_rejects_invalid_output_token_limit(value: object) -> None:
    with pytest.raises(ValueError, match="max_output_tokens"):
        AIRequest(
            "r1",
            "property.search",
            "hello",
            make_context(),
            max_output_tokens=value,  # type: ignore[arg-type]
        )


def test_request_context_rejects_missing_identity_references() -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        RequestContext("user-1", " ", "auth-1", "trace-1")


def test_model_route_rejects_boolean_limits_and_invalid_enabled_flag() -> None:
    with pytest.raises(ValueError, match="max_input_chars"):
        ModelRoute(
            "provider-a",
            "model-a",
            True,
            100,
        )  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="enabled"):
        ModelRoute(
            "provider-a",
            "model-a",
            100,
            100,
            enabled="yes",
        )  # type: ignore[arg-type]


def test_provider_request_rejects_infinite_or_nonpositive_timeout() -> None:
    with pytest.raises(ValueError, match="<= 120"):
        ProviderRequest(
            "r1", "property.search", "prompt", "model-a", 100, float("inf")
        )

    with pytest.raises(ValueError, match="<= 120"):
        ProviderRequest(
            "r1", "property.search", "prompt", "model-a", 100, 121
        )

    with pytest.raises(ValueError, match="> 0"):
        ProviderRequest(
            "r1", "property.search", "prompt", "model-a", 100, 0
        )


def test_provider_usage_rejects_bool_and_inconsistent_total() -> None:
    with pytest.raises(ValueError, match="input_tokens"):
        ProviderUsage(input_tokens=True)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="total_tokens"):
        ProviderUsage(
            input_tokens=4,
            output_tokens=5,
            total_tokens=8,
        )


def test_provider_response_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="text"):
        ProviderResponse(" ", "provider-a", "model-a")


def test_gateway_settings_are_disabled_by_default_and_validate_bounds() -> None:
    assert GatewaySettings().enabled is False

    with pytest.raises(ValueError, match="request_timeout_seconds"):
        GatewaySettings(request_timeout_seconds=121)

    with pytest.raises(TypeError, match="enabled"):
        GatewaySettings(enabled=1)  # type: ignore[arg-type]
