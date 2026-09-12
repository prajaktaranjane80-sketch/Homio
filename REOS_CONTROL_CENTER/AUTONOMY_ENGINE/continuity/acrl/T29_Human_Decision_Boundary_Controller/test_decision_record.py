from .decision_models import (
    BoundaryDecision,
    DecisionStatus,
    DecisionType,
    HumanDecision,
)
from .decision_record import build_record


def test_approved_record():
    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Approved",
        nonce="N1",
    )

    record = build_record(
        decision_id="D1",
        boundary=BoundaryDecision.HUMAN_APPROVED,
        decision=decision,
        rationale="Approved",
        fingerprint_value="FP1",
    )

    assert record.status == DecisionStatus.APPROVED
    assert record.decided_by == "human"
