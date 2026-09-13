from .reconciliation_controller import reconcile
from .reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
    ReconciliationPolicy,
    ReconciliationRequest,
)
from .reconciliation_store import ReconciliationStore


def test_controller_reconciles():
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

    request = ReconciliationRequest(
        reconciliation_id="R1",
        scheduler_fingerprint="S1",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=ReconciliationPolicy(),
        conflicts=(conflict,),
    )

    result = reconcile(request, store=ReconciliationStore())

    assert result.snapshot.decision.value == "RECONCILED"
