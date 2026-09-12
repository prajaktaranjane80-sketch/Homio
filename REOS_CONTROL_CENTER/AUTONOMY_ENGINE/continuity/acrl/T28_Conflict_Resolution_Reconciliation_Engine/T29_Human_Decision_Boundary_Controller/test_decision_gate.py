from .decision_gate import evaluate_human_decision
from .decision_models import (
    BoundaryDecision,
    DecisionType,
    HumanDecision,
)


def test_approve():
    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Approved",
        nonce="N1",
    )

    result = evaluate_human_decision(
        boundary=BoundaryDecision.HUMAN_REQUIRED,
        decision=decision,
    )

    assert result == BoundaryDecision.HUMAN_APPROVED


def test_reject():
    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.REJECT,
        decided_by="human",
        decision_timestamp=100,
        rationale="Rejected",
        nonce="N1",
    )

    result = evaluate_human_decision(
        boundary=BoundaryDecision.HUMAN_REQUIRED,
        decision=decision,
    )

    assert result == BoundaryDecision.HUMAN_REJECTED
