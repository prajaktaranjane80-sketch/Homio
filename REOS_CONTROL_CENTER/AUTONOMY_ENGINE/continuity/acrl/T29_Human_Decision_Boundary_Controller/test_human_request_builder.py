from .decision_models import (
    DecisionPolicy,
    DecisionRequest,
)
from .human_request_builder import build_human_request


def test_human_request():
    request = DecisionRequest(
        decision_id="D1",
        reconciliation_fingerprint="R1",
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=DecisionPolicy(),
        boundary_reason="CRITICAL",
    )

    result = build_human_request(request)

    assert result["decision_id"] == "D1"
    assert result["status"] == "WAITING_FOR_HUMAN"
