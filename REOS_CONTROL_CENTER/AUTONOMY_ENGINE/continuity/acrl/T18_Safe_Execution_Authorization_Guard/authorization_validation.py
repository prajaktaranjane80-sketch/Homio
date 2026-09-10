from __future__ import annotations

from ..T15_AI_Operator_Autonomy.operator_policy import (
    OperatorActionType,
)
from ..T15_AI_Operator_Autonomy.operator_autonomy import (
    OperatorDecision,
)
from ..T17_Change_Impact_Dependency_Analysis.impact_identity import (
    fingerprint_report,
)

from .authorization_errors import (
    SafeAuthorizationCompatibilityError,
    SafeAuthorizationIntegrityError,
    SafeAuthorizationInputError,
    SafeAuthorizationSecurityError,
)
from .authorization_identity import (
    approval_scope_fingerprint,
)
from .authorization_models import (
    AuthorizationRequest,
)
from .authorization_policy import (
    SafeAuthorizationPolicy,
)


def validate_request_structure(
    request: AuthorizationRequest,
) -> None:
    if not isinstance(
        request,
        AuthorizationRequest,
    ):
        raise SafeAuthorizationInputError(
            "Invalid T18 AuthorizationRequest."
        )

    if not isinstance(request.nonce, str):
        raise SafeAuthorizationInputError(
            "T18 nonce must be a string."
        )

    if not request.nonce.strip():
        raise SafeAuthorizationInputError(
            "T18 nonce must be non-empty."
        )

    if len(request.nonce) > 256:
        raise SafeAuthorizationInputError(
            "T18 nonce exceeds maximum length."
        )


def validate_upstream_contracts(
    request: AuthorizationRequest,
    policy: SafeAuthorizationPolicy,
) -> None:
    operator_report = request.operator_report
    impact_report = request.impact_report

    if operator_report.schema_version != "1.0":
        raise SafeAuthorizationCompatibilityError(
            "Unsupported T15 operator report schema."
        )

    if operator_report.authority != "REOS_CONTROL_CENTER":
        raise SafeAuthorizationSecurityError(
            "T15 authority boundary is invalid."
        )

    if operator_report.state_mutated:
        raise SafeAuthorizationSecurityError(
            "T15 report indicates state mutation."
        )

    if operator_report.execution_authorized:
        raise SafeAuthorizationSecurityError(
            "T15 report is already execution-authorized."
        )

    if operator_report.decision is not OperatorDecision.PROPOSE:
        raise SafeAuthorizationSecurityError(
            "T18 requires a T15 PROPOSE decision."
        )

    if operator_report.proposal is None:
        raise SafeAuthorizationSecurityError(
            "T18 requires a bounded T15 proposal."
        )

    if impact_report.schema_version != "1.0":
        raise SafeAuthorizationCompatibilityError(
            "Unsupported T17 report schema."
        )

    if impact_report.state_mutated:
        raise SafeAuthorizationSecurityError(
            "T17 report indicates state mutation."
        )

    if impact_report.execution_authorized:
        raise SafeAuthorizationSecurityError(
            "T17 cannot authorize execution."
        )

    expected_impact_fingerprint = fingerprint_report(
        impact_report
    )

    if expected_impact_fingerprint != impact_report.fingerprint:
        raise SafeAuthorizationIntegrityError(
            "T17 impact report fingerprint mismatch."
        )

    policy.validate()


def validate_authorization_scope(
    request: AuthorizationRequest,
    policy: SafeAuthorizationPolicy,
) -> None:
    proposal = request.operator_report.proposal

    if proposal is None:
        raise SafeAuthorizationSecurityError(
            "Missing T15 proposal."
        )

    if proposal.action_type is not OperatorActionType.PROPOSE_CHANGE:
        raise SafeAuthorizationSecurityError(
            "T18 only authorizes bounded change proposals."
        )

    if not policy.permits(
        proposal.action_type,
        proposal.risk,
    ):
        raise SafeAuthorizationSecurityError(
            "Requested action exceeds T18 policy."
        )

    impact = request.impact_report

    if policy.require_t17_analyze:
        decision = impact.decision.value

        if decision != "ANALYZE":
            raise SafeAuthorizationSecurityError(
                "T17 impact analysis is not in ANALYZE state."
            )

    if policy.reject_unknown_paths and impact.unknown_paths:
        raise SafeAuthorizationSecurityError(
            "T17 contains unknown paths."
        )

    if (
        policy.reject_protected_impacts
        and impact.protected_paths
    ):
        raise SafeAuthorizationSecurityError(
            "T17 contains protected impacts."
        )


def validate_human_approval(
    request: AuthorizationRequest,
    policy: SafeAuthorizationPolicy,
) -> None:
    proposal = request.operator_report.proposal

    if proposal is None:
        raise SafeAuthorizationSecurityError(
            "Missing proposal for approval validation."
        )

    if (
        policy.require_human_approval_for_change
        and proposal.action_type is OperatorActionType.PROPOSE_CHANGE
    ):
        approval = request.approval

        if approval is None:
            raise SafeAuthorizationSecurityError(
                "Explicit human approval is required."
            )

        if not approval.approved:
            raise SafeAuthorizationSecurityError(
                "Human approval is not granted."
            )

        if not approval.approval_id.strip():
            raise SafeAuthorizationInputError(
                "Approval ID must be non-empty."
            )

        if not approval.authority.strip():
            raise SafeAuthorizationInputError(
                "Approval authority must be non-empty."
            )

        if not approval.evidence:
            raise SafeAuthorizationSecurityError(
                "Approval evidence is required."
            )

        expected_scope = approval_scope_fingerprint(
            request
        )

        if approval.scope_fingerprint != expected_scope:
            raise SafeAuthorizationIntegrityError(
                "Approval scope fingerprint mismatch."
            )


def validate_read_only_invariant(
    authorization,
) -> None:
    if authorization.state_mutated:
        raise SafeAuthorizationSecurityError(
            "T18 authorization artifact cannot mutate state."
        )

    if authorization.requires_external_executor is not True:
        raise SafeAuthorizationSecurityError(
            "T18 authorization must require an external executor."
        )


__all__ = [
    "validate_request_structure",
    "validate_upstream_contracts",
    "validate_authorization_scope",
    "validate_human_approval",
    "validate_read_only_invariant",
]
