from .reconciliation_engine import reconcile_conflicts
from .reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
    ReconciliationDecision,
    ReconciliationPolicy,
)


def test_reconciles_safe_conflict():
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

    decision, resolutions, unresolved = reconcile_conflicts(
        (conflict,),
        policy=ReconciliationPolicy(),
        evidence_ids=("E1",),
    )

    assert decision == ReconciliationDecision.RECONCILED
    assert len(resolutions) == 1
    assert unresolved == ()
