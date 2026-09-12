from conflict_evidence import evidence_satisfies
from reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
)


def test_high_conflict_needs_evidence():
    conflict = ConflictRecord(
        conflict_id="C1",
        kind=ConflictKind.EVIDENCE_CONFLICT,
        severity=ConflictSeverity.HIGH,
        subject_id="W1",
        left_value="A",
        right_value="B",
        source_left="L",
        source_right="R",
        evidence_ids=("E1",),
    )

    assert evidence_satisfies(conflict, ("E1",))
    assert not evidence_satisfies(conflict, ("E2",))
