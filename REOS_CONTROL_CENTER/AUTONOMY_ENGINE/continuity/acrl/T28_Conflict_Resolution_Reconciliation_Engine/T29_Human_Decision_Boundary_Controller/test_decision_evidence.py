from .decision_evidence import evidence_is_sufficient
from .decision_models import (
    DecisionType,
    HumanDecision,
)


def test_evidence_is_sufficient():
    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Approved",
        evidence_ids=("E1", "E2"),
        nonce="N1",
    )

    assert evidence_is_sufficient(
        decision,
        ("E1", "E2"),
    )


def test_evidence_missing():
    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Approved",
        evidence_ids=("E1",),
        nonce="N1",
    )

    assert not evidence_is_sufficient(
        decision,
        ("E1", "E2"),
    )
