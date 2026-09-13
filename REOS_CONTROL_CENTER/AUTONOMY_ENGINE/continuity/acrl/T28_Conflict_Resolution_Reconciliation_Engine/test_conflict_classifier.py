from .conflict_classifier import classify
from .reconciliation_models import ConflictKind


def test_classifies_dependency_conflict():
    result = classify(
        conflict_id="C1",
        subject_id="W1",
        left_value="READY",
        right_value="BLOCKED",
        source_left="T27",
        source_right="T26",
        reason="dependency",
    )

    assert result.kind == ConflictKind.DEPENDENCY_CONFLICT
