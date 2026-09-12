from .boundary_classifier import classify_boundary
from .decision_models import (
    BoundaryDecision,
    DecisionPolicy,
)


def test_fail_closed_requires_human():
    result = classify_boundary(
        reconciliation_decision="FAIL_CLOSED",
        boundary_reason="CRITICAL",
        policy=DecisionPolicy(),
    )

    assert result == BoundaryDecision.HUMAN_REQUIRED
