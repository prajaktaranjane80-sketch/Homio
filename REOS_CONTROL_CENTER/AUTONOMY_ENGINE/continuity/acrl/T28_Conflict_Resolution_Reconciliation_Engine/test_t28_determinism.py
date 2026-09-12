from reconciliation_engine import reconcile_conflicts
from reconciliation_models import ReconciliationPolicy


def test_empty_reconciliation_is_deterministic():
    a = reconcile_conflicts(
        (),
        policy=ReconciliationPolicy(),
        evidence_ids=(),
    )
    b = reconcile_conflicts(
        (),
        policy=ReconciliationPolicy(),
        evidence_ids=(),
    )

    assert a == b
