from .decision_models import BoundaryDecision, DecisionPolicy


def classify_boundary(
    *,
    reconciliation_decision: str,
    boundary_reason: str,
    policy: DecisionPolicy,
) -> BoundaryDecision:
    decision = reconciliation_decision.upper()

    if decision in {
        "FAIL_CLOSED",
        "NO_SAFE_RESOLUTION",
        "CONFLICT_UNRESOLVED",
        "HUMAN_DECISION_REQUIRED",
    }:
        return (
            BoundaryDecision.HUMAN_REQUIRED
            if policy.require_human_for_unresolved
            else BoundaryDecision.FAIL_CLOSED
        )

    if boundary_reason.upper() == "CRITICAL":
        return (
            BoundaryDecision.HUMAN_REQUIRED
            if policy.require_human_for_critical
            else BoundaryDecision.AUTONOMY_ALLOWED
        )

    return BoundaryDecision.AUTONOMY_ALLOWED
