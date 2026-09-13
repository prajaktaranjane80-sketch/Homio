from .reconciliation_models import (
    ConflictKind,
    ConflictSeverity,
    ReconciliationDecision,
    ReconciliationPolicy,
)


def test_models():
    assert ConflictKind.STATE_MISMATCH.value == "STATE_MISMATCH"
    assert ConflictSeverity.CRITICAL.value == "CRITICAL"
    assert ReconciliationDecision.RECONCILED.value == "RECONCILED"
    assert ReconciliationPolicy().policy_version == "1.0"
