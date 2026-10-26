from __future__ import annotations

from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.ai_platform.authorization import (
    AIPlatformAuthorization,
)
from AUTONOMY_ENGINE.ai_platform.contracts import (
    AuthorizationDecision,
    RequestContext,
)
from AUTONOMY_ENGINE.ai_platform.errors import (
    AuthorizationServiceUnavailableError,
    RequestContextMissingError,
)


CONTEXT = RequestContext(
    principal_id="user-1",
    tenant_id="tenant-1",
    authentication_context_ref="auth-context-1",
    correlation_id="trace-1",
)


class FakeTrustedContextVerifier:
    def __init__(
        self,
        *,
        trusted: bool = True,
        result: object | None = None,
        error: Exception | None = None,
    ) -> None:
        self.trusted = trusted
        self.result = result
        self.error = error
        self.calls = []

    def verify_context(self, context):
        self.calls.append(context)
        if self.error is not None:
            raise self.error
        if self.result is not None:
            return self.result
        return self.trusted


class FakeDomainPolicy:
    """Test double for an existing owner, not a production policy engine."""

    def __init__(
        self,
        *,
        resource_tenants: dict[str, str] | None = None,
        denied_operations: tuple[str, ...] = (),
        error: Exception | None = None,
        result: object | None = None,
    ) -> None:
        self.resource_tenants = resource_tenants or {}
        self.denied_operations = set(denied_operations)
        self.error = error
        self.result = result
        self.calls = []

    def authorize(
        self,
        context,
        *,
        operation: str,
        resource_id: str | None = None,
    ):
        self.calls.append(
            (context, operation, resource_id)
        )

        if self.error is not None:
            raise self.error

        if self.result is not None:
            return self.result

        if operation in self.denied_operations:
            return AuthorizationDecision(
                False,
                "decision-denied",
                "OPERATION_DENIED",
            )

        if resource_id is not None:
            owner_tenant = self.resource_tenants.get(resource_id)
            if owner_tenant != context.tenant_id:
                return AuthorizationDecision(
                    False,
                    "decision-tenant-denied",
                    "TENANT_SCOPE_DENIED",
                )

        return AuthorizationDecision(
            True,
            "decision-allowed",
            "ALLOW",
        )


def make_authorization(
    *,
    trusted: bool = True,
    verifier_result: object | None = None,
    verifier_error: Exception | None = None,
    policy: FakeDomainPolicy | None = None,
    enabled: bool = True,
):
    verifier = FakeTrustedContextVerifier(
        trusted=trusted,
        result=verifier_result,
        error=verifier_error,
    )
    selected_policy = policy or FakeDomainPolicy(
        resource_tenants={
            "inventory-1": "tenant-1",
            "inventory-2": "tenant-2",
        }
    )
    authorization = AIPlatformAuthorization(
        identity_verifier=verifier,
        domain_policy=selected_policy,
        enabled=enabled,
    )
    return authorization, verifier, selected_policy


def test_authorization_is_disabled_by_default_and_denies() -> None:
    verifier = FakeTrustedContextVerifier()
    policy = FakeDomainPolicy()
    authorization = AIPlatformAuthorization(
        identity_verifier=verifier,
        domain_policy=policy,
    )

    result = authorization.authorize_request(
        CONTEXT,
        operation="property.search",
    )

    assert not result.allowed
    assert result.reason_code == "AUTHORIZATION_DISABLED"
    assert verifier.calls == []
    assert policy.calls == []


def test_enabled_configuration_requires_existing_trusted_boundaries() -> None:
    with pytest.raises(ValueError):
        AIPlatformAuthorization(enabled=True)

    with pytest.raises(ValueError):
        AIPlatformAuthorization(
            identity_verifier=FakeTrustedContextVerifier(),
            enabled=True,
        )


def test_request_authorization_delegates_to_domain_policy() -> None:
    authorization, verifier, policy = make_authorization()

    result = authorization.authorize_request(
        CONTEXT,
        operation="property.search",
    )

    assert result.allowed is True
    assert verifier.calls == [CONTEXT]
    assert policy.calls == [(CONTEXT, "property.search", None)]


def test_untrusted_context_is_denied_before_domain_policy() -> None:
    authorization, verifier, policy = make_authorization(
        trusted=False
    )

    result = authorization.authorize_request(
        CONTEXT,
        operation="property.search",
    )

    assert not result.allowed
    assert result.reason_code == "IDENTITY_UNTRUSTED"
    assert len(verifier.calls) == 1
    assert policy.calls == []


def test_verifier_exception_fails_closed_without_leaking_details() -> None:
    authorization, _, policy = make_authorization(
        verifier_error=RuntimeError("private auth-provider detail")
    )

    with pytest.raises(AuthorizationServiceUnavailableError) as exc:
        authorization.authorize_request(
            CONTEXT,
            operation="property.search",
        )

    assert "private auth-provider detail" not in str(exc.value)
    assert policy.calls == []


def test_non_boolean_verification_result_is_not_allowed() -> None:
    authorization, _, policy = make_authorization(
        verifier_result="true"
    )

    with pytest.raises(AuthorizationServiceUnavailableError):
        authorization.authorize_request(
            CONTEXT,
            operation="property.search",
        )

    assert policy.calls == []


def test_cross_tenant_inventory_resource_is_denied() -> None:
    authorization, _, policy = make_authorization()

    result = authorization.authorize_inventory(
        CONTEXT,
        inventory_id="inventory-2",
    )

    assert not result.allowed
    assert result.reason_code == "TENANT_SCOPE_DENIED"
    assert policy.calls == [
        (CONTEXT, "inventory.read", "inventory-2")
    ]


def test_same_tenant_inventory_resource_can_be_allowed() -> None:
    authorization, _, _ = make_authorization()

    result = authorization.authorize_inventory(
        CONTEXT,
        inventory_id="inventory-1",
    )

    assert result.allowed


def test_retrieval_search_is_restricted_to_canonical_operation() -> None:
    authorization, _, policy = make_authorization()

    denied = authorization.authorize_search(
        CONTEXT,
        operation="inventory.delete",
    )

    assert not denied.allowed
    assert denied.reason_code == "OPERATION_NOT_ALLOWED"
    assert policy.calls == []

    allowed = authorization.authorize_search(
        CONTEXT,
        operation="inventory.search",
    )

    assert allowed.allowed
    assert policy.calls == [
        (CONTEXT, "inventory.search", None)
    ]


def test_tool_call_uses_server_allowlisted_tool_name_and_resource_policy() -> None:
    authorization, _, policy = make_authorization()

    result = authorization.authorize_tool_call(
        CONTEXT,
        tool_name="search_properties",
        resource_id="inventory-2",
    )

    assert not result.allowed
    assert result.reason_code == "TENANT_SCOPE_DENIED"
    assert policy.calls == [
        (
            CONTEXT,
            "agent.tool.search_properties",
            "inventory-2",
        )
    ]


def test_invalid_tool_name_is_denied_without_policy_call() -> None:
    authorization, _, policy = make_authorization()

    result = authorization.authorize_tool_call(
        CONTEXT,
        tool_name="run-shell",
    )

    assert not result.allowed
    assert result.reason_code == "INVALID_TOOL_NAME"
    assert policy.calls == []


def test_malformed_domain_decision_fails_closed() -> None:
    authorization, _, _ = make_authorization(
        policy=FakeDomainPolicy(result={"allowed": True})
    )

    with pytest.raises(AuthorizationServiceUnavailableError):
        authorization.authorize_request(
            CONTEXT,
            operation="property.search",
        )


def test_domain_policy_exception_is_sanitized() -> None:
    authorization, _, _ = make_authorization(
        policy=FakeDomainPolicy(
            error=RuntimeError("secret domain policy data")
        )
    )

    with pytest.raises(AuthorizationServiceUnavailableError) as exc:
        authorization.authorize_request(
            CONTEXT,
            operation="property.search",
        )

    assert "secret domain policy data" not in str(exc.value)


def test_missing_context_never_reaches_identity_or_domain_policy() -> None:
    authorization, verifier, policy = make_authorization()

    with pytest.raises(RequestContextMissingError):
        authorization.authorize_request(
            None,  # type: ignore[arg-type]
            operation="property.search",
        )

    assert verifier.calls == []
    assert policy.calls == []


def test_invalid_operation_is_denied_without_policy_call() -> None:
    authorization, _, policy = make_authorization()

    result = authorization.authorize_request(
        CONTEXT,
        operation="Property Delete",
    )

    assert not result.allowed
    assert result.reason_code == "INVALID_OPERATION"
    assert policy.calls == []


def test_tool_bridge_callback_returns_true_only_for_allowed_policy_decision() -> None:
    authorization, _, policy = make_authorization()

    allowed = authorization.check_tool_call(
        SimpleNamespace(name="search_properties"),
        SimpleNamespace(tool_name="search_properties"),
        CONTEXT,
    )

    assert allowed is True
    assert policy.calls == [
        (CONTEXT, "agent.tool.search_properties", None)
    ]


def test_tool_bridge_callback_denies_when_domain_policy_denies() -> None:
    authorization, _, policy = make_authorization(
        policy=FakeDomainPolicy(
            denied_operations=("agent.tool.search_properties",)
        )
    )

    allowed = authorization.check_tool_call(
        SimpleNamespace(name="search_properties"),
        SimpleNamespace(tool_name="search_properties"),
        CONTEXT,
    )

    assert allowed is False
    assert policy.calls == [
        (CONTEXT, "agent.tool.search_properties", None)
    ]


def test_tool_bridge_callback_rejects_model_tool_name_mismatch_before_policy() -> None:
    authorization, verifier, policy = make_authorization()

    allowed = authorization.check_tool_call(
        SimpleNamespace(name="search_properties"),
        SimpleNamespace(tool_name="run_shell"),
        CONTEXT,
    )

    assert allowed is False
    assert verifier.calls == []
    assert policy.calls == []
