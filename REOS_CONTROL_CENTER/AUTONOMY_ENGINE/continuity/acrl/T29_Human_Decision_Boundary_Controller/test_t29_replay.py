
import pytest

from .decision_controller import create_decision_boundary
from .decision_models import (
    DecisionPolicy,
    DecisionRequest,
)
from .decision_store import (
    DecisionReplayError,
    DecisionStore,
)


def test_replay_detected():
    request = DecisionRequest(
        decision_id="D1",
        reconciliation_fingerprint="R1",
        reconciliation_decision="HUMAN_DECISION_REQUIRED",
        continuity_fingerprint="C1",
        evidence_fingerprint="E1",
        policy=DecisionPolicy(),
        boundary_reason="CRITICAL",
    )

    store = DecisionStore()

    create_decision_boundary(
        request,
        store=store,
    )

    with pytest.raises(DecisionReplayError):
        create_decision_boundary(
            request,
            store=store,
        )
