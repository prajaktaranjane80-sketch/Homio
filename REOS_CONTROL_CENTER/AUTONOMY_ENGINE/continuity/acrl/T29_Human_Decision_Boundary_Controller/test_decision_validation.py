import pytest

from .decision_models import (
    DecisionPolicy,
    DecisionRequest,
    DecisionType,
    HumanDecision,
)
from .decision_validation import (
    validate_human_decision,
    validate_request,
)


def test_request_validation():
    request = DecisionRequest(
        decision_id="D1",
        reconciliation_fingerprint="R1",
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=DecisionPolicy(),
        boundary_reason="CRITICAL",
    )

    validate_request(request)


def test_request_requires_id():
    request = DecisionRequest(
        decision_id="",
        reconciliation_fingerprint="R1",
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=DecisionPolicy(),
        boundary_reason="CRITICAL",
    )

    with pytest.raises(ValueError):
        validate_request(request)


def test_human_decision_validation():
    decision = HumanDecision(
        decision_id="D1",
        decision_type=DecisionType.APPROVE,
        decided_by="human-1",
        decision_timestamp=100,
        rationale="Approved",
        nonce="N1",
    )

    validate_human_decision(decision)
