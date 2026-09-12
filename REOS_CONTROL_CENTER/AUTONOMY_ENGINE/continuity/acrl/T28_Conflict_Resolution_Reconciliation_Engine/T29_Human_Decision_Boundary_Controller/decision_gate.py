from .decision_models import (
    BoundaryDecision,
    DecisionType,
    HumanDecision,
)


def evaluate_human_decision(
    *,
    boundary: BoundaryDecision,
    decision: HumanDecision,
) -> BoundaryDecision:
    if boundary != BoundaryDecision.HUMAN_REQUIRED:
        return BoundaryDecision.INVALID_DECISION

    if decision.decision_type == DecisionType.APPROVE:
        return BoundaryDecision.HUMAN_APPROVED

    if decision.decision_type == DecisionType.REJECT:
        return BoundaryDecision.HUMAN_REJECTED

    return BoundaryDecision.INVALID_DECISION
