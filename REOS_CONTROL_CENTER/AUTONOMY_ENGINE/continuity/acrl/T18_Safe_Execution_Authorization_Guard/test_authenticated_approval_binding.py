from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from AUTONOMY_ENGINE.security.authentication.oidc_verifier import (
    AuthenticatedPrincipal,
    AuthenticationError,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_errors import (
    SafeAuthorizationPolicyError,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    AuthorizationRequest,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_policy import (
    SafeAuthorizationPolicy,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.execution_authorization import (
    ExecutionAuthorizationGuard,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.test_execution_authorization import (
    TEST_ACCESS_TOKEN,
    TEST_ISSUER,
    TEST_SUBJECT,
    _test_guard,
    _test_policy,
    build_approved_request,
)


class _FixedPrincipalVerifier:
    """Controlled adapter for testing T18's OIDC-verifier boundary."""

    def __init__(
        self,
        principal: AuthenticatedPrincipal,
        *,
        expected_token: str = TEST_ACCESS_TOKEN,
        fail: bool = False,
    ) -> None:
        self.principal = principal
        self.expected_token = expected_token
        self.fail = fail

    def verify_access_token(self, token: str) -> AuthenticatedPrincipal:
        if self.fail or token != self.expected_token:
            raise AuthenticationError("invalid_access_token")
        return self.principal


def _request(tmp_path) -> AuthorizationRequest:
    return build_approved_request(tmp_path)


def test_claimed_approver_must_match_oidc_verified_principal(tmp_path):
    request = _request(tmp_path)
    assert request.approval is not None

    forged_approval = replace(
        request.approval,
        principal_subject="forged-subject",
    )
    forged_request = replace(request, approval=forged_approval)

    result = _test_guard().authorize(forged_request)

    assert result.decision is AuthorizationDecision.BLOCK
    assert result.reason is AuthorizationReason.APPROVAL_INVALID
    assert result.execution_authorized is False


def test_authenticated_principal_must_be_allowlisted(tmp_path):
    request = _request(tmp_path)
    assert request.approval is not None

    outsider_subject = "unlisted-approver"
    outsider = AuthenticatedPrincipal(
        issuer=TEST_ISSUER,
        subject=outsider_subject,
        audiences=("homio-api",),
    )
    outsider_approval = replace(
        request.approval,
        principal_subject=outsider_subject,
    )
    outsider_request = replace(request, approval=outsider_approval)

    verifier = _FixedPrincipalVerifier(outsider)
    guard = ExecutionAuthorizationGuard(
        policy=_test_policy(),
        principal_verifier=verifier,
    )
    result = guard.authorize(outsider_request)

    assert result.decision is AuthorizationDecision.BLOCK
    assert result.reason is AuthorizationReason.APPROVAL_INVALID
    assert result.execution_authorized is False


def test_missing_oidc_verifier_fails_closed(tmp_path):
    request = _request(tmp_path)

    result = ExecutionAuthorizationGuard(
        policy=_test_policy(),
    ).authorize(request)

    assert result.decision is AuthorizationDecision.BLOCK
    assert result.reason is AuthorizationReason.APPROVAL_INVALID
    assert result.execution_authorized is False


def test_oidc_verification_failure_fails_closed(tmp_path):
    request = _request(tmp_path)
    verifier = _FixedPrincipalVerifier(
        AuthenticatedPrincipal(
            issuer=TEST_ISSUER,
            subject=TEST_SUBJECT,
            audiences=("homio-api",),
        ),
        fail=True,
    )
    guard = ExecutionAuthorizationGuard(
        policy=_test_policy(),
        principal_verifier=verifier,
    )

    result = guard.authorize(request)

    assert result.decision is AuthorizationDecision.BLOCK
    assert result.reason is AuthorizationReason.APPROVAL_INVALID
    assert result.execution_authorized is False
    assert "invalid_access_token" not in str(result.to_dict())


def test_bearer_token_is_never_in_serialized_approval_or_request(tmp_path):
    request = _request(tmp_path)
    assert request.approval is not None

    serialized_approval = json.dumps(request.approval.to_dict())
    serialized_request = json.dumps(request.to_dict())

    assert TEST_ACCESS_TOKEN not in serialized_approval
    assert TEST_ACCESS_TOKEN not in serialized_request
    assert TEST_ACCESS_TOKEN not in repr(request.approval)
    assert (
        request.approval.to_dict()["authentication_proof_present"]
        is True
    )


def test_approval_flag_requires_true_boolean(tmp_path):
    request = _request(tmp_path)
    assert request.approval is not None

    forged_approval = replace(
        request.approval,
        approved="yes",
    )
    forged_request = replace(request, approval=forged_approval)

    result = _test_guard().authorize(forged_request)

    assert result.decision is AuthorizationDecision.BLOCK
    assert result.reason is AuthorizationReason.APPROVAL_INVALID


def test_t18_policy_cannot_disable_explicit_human_approval():
    policy = SafeAuthorizationPolicy(
        require_human_approval_for_change=False,
    )

    try:
        policy.validate()
    except SafeAuthorizationPolicyError:
        pass
    else:
        raise AssertionError(
            "T18 must not authorize executable changes without human approval."
        )


def test_contract_requires_oidc_verified_approver():
    contract_path = (
        Path(__file__).resolve().parent
        / "t18.contract.json"
    )
    contract = json.loads(
        contract_path.read_text(encoding="utf-8")
    )

    assert any(
        "OIDC-verified approver principal" in item
        for item in contract["required_inputs"]
    )
