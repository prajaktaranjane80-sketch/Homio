from reconciliation_controller import reconcile
from reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
    ReconciliationPolicy,
    ReconciliationRequest,
)
from reconciliation_store import ReconciliationStore


def test_t27_to_t28_boundary():
    conflict = ConflictRecord(
        conflict_id="T27-C1",
        kind=ConflictKind.DEPENDENCY_CONFLICT,
        severity=ConflictSeverity.HIGH,
        subject_id="WORK-A",
        left_value="READY",
        right_value="WAITING",
        source_left="T27",
        source_right="T26",
        evidence_ids=("E-T27",),
    )

    request = ReconciliationRequest(
        reconciliation_id="R-T27-T28",
        scheduler_fingerprint="T27-FP",
        continuity_fingerprint="T24-FP",
        evidence_fingerprint="T23-FP",
        policy=ReconciliationPolicy(),
        conflicts=(conflict,),
    )

    result = reconcile(
        request,
        store=ReconciliationStore(),
    )

    assert result.snapshot.reconciliation_id == "R-T27-T28"
    assert result.audit["identity"]
