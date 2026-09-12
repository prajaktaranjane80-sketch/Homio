import pytest

from reconciliation_controller import reconcile
from reconciliation_models import ReconciliationPolicy, ReconciliationRequest
from reconciliation_store import (
    ReconciliationReplayError,
    ReconciliationStore,
)


def test_replay_detected():
    request = ReconciliationRequest(
        reconciliation_id="R1",
        scheduler_fingerprint="S1",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=ReconciliationPolicy(),
    )

    store = ReconciliationStore()

    reconcile(request, store=store)

    with pytest.raises(ReconciliationReplayError):
        reconcile(request, store=store)
