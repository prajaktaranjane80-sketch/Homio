import pytest

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


def make_request():
    return DecisionRequest(
        decision_id="D1",
        reconciliation_fingerprint="R1",
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=DecisionPolicy(),
        boundary_reason="CRITICAL",
    )


def test_boundary_created():
    result = create_decision_boundary(
        make_request(),
        store=DecisionStore(),
    )

    assert result.record.status.value == "WAITING"


def test_decision_approved():
    store = DecisionStore()
    request = make_request()

    create_decision_boundary(
        request,
        store=store,
    )

    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Approved",
        evidence_ids=(),
        nonce="N1",
    )

    result = resolve_decision(
        request,
        decision,
        store=store,
    )

    assert result.record.boundary_decision.value == "HUMAN_APPROVED"


def test_id_mismatch():
    request = make_request()

    decision = HumanDecision(
        decision_id="D2",
        decision_type=DecisionType.APPROVE,
        decided_by="human",
        decision_timestamp=100,
        rationale="Approved",
        nonce="N1",
    )

    with pytest.raises(ValueError):
        resolve_decision(
            request,
            decision,
            store=DecisionStore(),
        )
