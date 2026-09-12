from reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
    ResolutionKind,
)
from resolution_engine import resolve_conflict


def test_equal_values_resolve():
    conflict = ConflictRecord(
        conflict_id="C1",
        kind=ConflictKind.STATE_MISMATCH,
        severity=ConflictSeverity.HIGH,
        subject_id="W1",
        left_value="READY",
        right_value="READY",
        source_left="A",
        source_right="B",
        evidence_ids=("E1",),
    )

    result = resolve_conflict(
        conflict,
        evidence_ids=("E1",),
        allow_precedence=True,
    )

    assert result is not None
    assert result.kind == ResolutionKind.PRECEDENCE
