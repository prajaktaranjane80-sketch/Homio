from reconciliation_engine import reconcile_conflicts
from reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
    ReconciliationDecision,
    ReconciliationPolicy,
)


def test_unresolved_conflict_requires_human():
    conflict = ConflictRecord(
        conflict_id="C1",
        kind=ConflictKind.UNKNOWN,
        severity=ConflictSeverity.CRITICAL,
        subject_id="W1",
        left_value="A",
        right_value="B",
        source_left="A",
        source_right="B",
        evidence_ids=(),
    )

    decision, _, unresolved = reconcile_conflicts(
        (conflict,),
        policy=ReconciliationPolicy(),
        evidence_ids=(),
    )

    assert decision == ReconciliationDecision.HUMAN_DECISION_REQUIRED
    assert unresolved == ("C1",)
