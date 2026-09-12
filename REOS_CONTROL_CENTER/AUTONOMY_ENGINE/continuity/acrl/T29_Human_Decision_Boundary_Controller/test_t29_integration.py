from .decision_controller import (
    create_decision_boundary,
    resolve_decision,
)
from .decision_models import (
    DecisionPolicy,
    DecisionRequest,
    DecisionType,
    HumanDecision,
)
from .decision_store import DecisionStore


def test_t28_to_t29_boundary():
    store = DecisionStore()

    request = DecisionRequest(
        decision_id="T28-T29-D1",
        reconciliation_fingerprint="T28-FP",
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        continuity_fingerprint="T24-FP",
        evidence_fingerprint="T23-FP",
        policy=DecisionPolicy(),
        boundary_reason="CRITICAL",
    )

    waiting = create_decision_boundary(
        request,
        store=store,
    )

    assert waiting.record.status.value == "WAITING"

    decision = HumanDecision(
        decision_id="T28-T29-D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Human approval received",
        evidence_ids=(),
        nonce="N1",
    )

    result = resolve_decision(
        request,
        decision,
        store=store,
    )

    assert result.record.boundary_decision.value == "HUMAN_APPROVED"
    assert result.audit["decision"] == "HUMAN_APPROVED"
