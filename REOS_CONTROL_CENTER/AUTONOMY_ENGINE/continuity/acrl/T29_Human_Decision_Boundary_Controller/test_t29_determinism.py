from .boundary_classifier import classify_boundary
from .decision_models import DecisionPolicy


def test_boundary_is_deterministic():
    policy = DecisionPolicy()

    a = classify_boundary(
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        boundary_reason="HIGH",
        policy=policy,
    )

    b = classify_boundary(
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        boundary_reason="HIGH",
        policy=policy,
    )

    assert a == b
