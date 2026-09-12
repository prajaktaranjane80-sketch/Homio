from .boundary_classifier import classify_boundary
from .decision_models import (
    BoundaryDecision,
    DecisionPolicy,
)


def test_unresolved_requires_human():
    result = classify_boundary(
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        boundary_reason="HIGH",
        policy=DecisionPolicy(),
    )

    assert result == BoundaryDecision.HUMAN_REQUIRED


def test_safe_result_allows_autonomy():
    result = classify_boundary(
        reconciliation_decision="RECONCILED",
        boundary_reason="NORMAL",
        policy=DecisionPolicy(),
    )

    assert result == BoundaryDecision.AUTONOMY_ALLOWED
