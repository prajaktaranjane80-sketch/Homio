from .decision_models import (
    BoundaryDecision,
    DecisionRecord,
    DecisionStatus,
    DecisionType,
    HumanDecision,
)


def build_record(
    *,
    decision_id: str,
    boundary: BoundaryDecision,
    decision: HumanDecision | None,
    rationale: str,
    fingerprint_value: str,
) -> DecisionRecord:
    if boundary == BoundaryDecision.HUMAN_APPROVED:
        status = DecisionStatus.APPROVED
    elif boundary == BoundaryDecision.HUMAN_REJECTED:
        status = DecisionStatus.REJECTED
    elif boundary == BoundaryDecision.WAITING_FOR_HUMAN:
        status = DecisionStatus.WAITING
    elif boundary == BoundaryDecision.HUMAN_EXPIRED:
        status = DecisionStatus.EXPIRED
    else:
        status = DecisionStatus.FAILED

    return DecisionRecord(
        decision_id=decision_id,
        status=status,
        boundary_decision=boundary,
        decision_type=(
            decision.decision_type
            if decision
            else DecisionType.NONE
        ),
        decided_by=(
            decision.decided_by
            if decision
            else None
        ),
        rationale=rationale,
        fingerprint=fingerprint_value,
    )
