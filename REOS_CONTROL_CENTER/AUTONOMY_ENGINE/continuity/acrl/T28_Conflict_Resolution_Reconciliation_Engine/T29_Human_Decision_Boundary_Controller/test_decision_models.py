from .decision_models import (
    BoundaryDecision,
    DecisionPolicy,
    DecisionStatus,
    DecisionType,
)


def test_models():
    assert DecisionType.APPROVE.value == "APPROVE"
    assert BoundaryDecision.HUMAN_REQUIRED.value == "HUMAN_REQUIRED"
    assert DecisionStatus.WAITING.value == "WAITING"
    assert DecisionPolicy().policy_version == "1.0"
