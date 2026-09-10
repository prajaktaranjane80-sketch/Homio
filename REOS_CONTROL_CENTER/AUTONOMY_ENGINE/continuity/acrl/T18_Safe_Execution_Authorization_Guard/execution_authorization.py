from __future__ import annotations

from ..T15_AI_Operator_Autonomy.operator_policy import (
    OperatorActionType,
)

from .authorization_errors import (
    SafeAuthorizationError,
)
from .authorization_identity import (
    authorization_fingerprint,
    request_fingerprint,
)
from .authorization_models import (
    AuthorizationRequest,
    ExecutionAuthorization,
)
from .authorization_policy import (
    SafeAuthorizationPolicy,
)
from .authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)
from .authorization_validation import (
    validate_authorization_scope,
    validate_human_approval,
    validate_read_only_invariant,
    validate_request_structure,
    validate_upstream_contracts,
)


class ExecutionAuthorizationGuard:
    """Deterministic, non-executing T18 authorization guard."""

    SCHEMA_VERSION = "1.0"
    AUTHORITY = "REOS_CONTROL_CENTER"

    def __init__(
        self,
        policy: SafeAuthorizationPolicy | None = None,
    ) -> None:
        self.policy = (
            policy
            if policy is not None
            else SafeAuthorizationPolicy()
        )

        self.policy.validate()

    @staticmethod
    def _blocked(
        request_fp: str,
        operator_request_fp: str,
        impact_fp: str,
        reason: AuthorizationReason,
        action_type,
        risk,
    ) -> ExecutionAuthorization:
        payload = {
            "schema_version": "1.0",
            "decision": AuthorizationDecision.BLOCK.value,
            "reason": reason.value,
            "request_fingerprint": request_fp,
            "operator_request_fingerprint": operator_request_fp,
            "impact_fingerprint": impact_fp,
            "action_type": (
                action_type.value
                if action_type is not None
                else None
            ),
            "risk": (
                risk.value
                if risk is not None
                else None
            ),
        }

        return ExecutionAuthorization(
            schema_version="1.0",
            decision=AuthorizationDecision.BLOCK,
            reason=reason,
            authorization_fingerprint=authorization_fingerprint(
                payload
            ),
            request_fingerprint=request_fp,
            operator_request_fingerprint=operator_request_fp,
            impact_fingerprint=impact_fp,
            action_type=action_type,
            risk=risk,
            execution_authorized=False,
            state_mutated=False,
            requires_external_executor=True,
        )

    def authorize(
        self,
        request: AuthorizationRequest,
    ) -> ExecutionAuthorization:
        validate_request_structure(request)

        request_fp = request_fingerprint(request)

        operator_report = request.operator_report
        impact_report = request.impact_report

        operator_request_fp = (
            operator_report.request_fingerprint
        )
        impact_fp = impact_report.fingerprint

        proposal = operator_report.proposal

        try:
            validate_upstream_contracts(
                request,
                self.policy,
            )

            validate_authorization_scope(
                request,
                self.policy,
            )

            validate_human_approval(
                request,
                self.policy,
            )

        except SafeAuthorizationError as exc:
            reason = AuthorizationReason.POLICY_BLOCKED

            text = str(exc).lower()

            if "human approval" in text:
                reason = AuthorizationReason.APPROVAL_REQUIRED
            elif "protected" in text:
                reason = AuthorizationReason.PROTECTED_IMPACT
            elif "unknown" in text:
                reason = AuthorizationReason.T17_UNKNOWN_PATH
            elif "t17" in text:
                reason = AuthorizationReason.T17_IMPACT_BLOCKED
            elif "fingerprint" in text:
                reason = AuthorizationReason.INTEGRITY_FAILURE
            elif "t15" in text:
                reason = AuthorizationReason.INVALID_T15_PROPOSAL

            return self._blocked(
                request_fp,
                operator_request_fp,
                impact_fp,
                reason,
                (
                    proposal.action_type
                    if proposal is not None
                    else None
                ),
                (
                    proposal.risk
                    if proposal is not None
                    else None
                ),
            )

        if proposal is None:
            raise SafeAuthorizationError(
                "T18 authorization reached an invalid proposal state."
            )

        if (
            proposal.action_type
            is not OperatorActionType.PROPOSE_CHANGE
        ):
            raise SafeAuthorizationError(
                "T18 reached an unsupported executable action."
            )

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "decision": AuthorizationDecision.AUTHORIZE.value,
            "reason": AuthorizationReason.VALIDATED.value,
            "request_fingerprint": request_fp,
            "operator_request_fingerprint": operator_request_fp,
            "impact_fingerprint": impact_fp,
            "action_type": proposal.action_type.value,
            "risk": proposal.risk.value,
            "external_executor_required": True,
        }

        artifact = ExecutionAuthorization(
            schema_version=self.SCHEMA_VERSION,
            decision=AuthorizationDecision.AUTHORIZE,
            reason=AuthorizationReason.VALIDATED,
            authorization_fingerprint=authorization_fingerprint(
                payload
            ),
            request_fingerprint=request_fp,
            operator_request_fingerprint=operator_request_fp,
            impact_fingerprint=impact_fp,
            action_type=proposal.action_type,
            risk=proposal.risk,
            execution_authorized=True,
            state_mutated=False,
            requires_external_executor=True,
        )

        validate_read_only_invariant(
            artifact
        )

        return artifact


def authorize_execution(
    request: AuthorizationRequest,
    policy: SafeAuthorizationPolicy | None = None,
) -> ExecutionAuthorization:
    """Convenience API for T18 authorization."""

    return ExecutionAuthorizationGuard(
        policy
    ).authorize(
        request
    )


__all__ = [
    "ExecutionAuthorizationGuard",
    "authorize_execution",
]
