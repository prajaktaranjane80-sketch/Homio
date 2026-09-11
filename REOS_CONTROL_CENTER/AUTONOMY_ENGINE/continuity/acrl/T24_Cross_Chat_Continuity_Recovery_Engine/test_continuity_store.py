from .continuity_models import (
    ContinuityDecision,
    ContinuityResult,
)
from .continuity_store import (
    ContinuityReplayError,
    ContinuityStore,
)


def make_result():
    return ContinuityResult(
        schema_version="1.0",
        decision=ContinuityDecision.RECOVERED,
        reason="VALID",
        recovery_id="r",
        project_id="HOMIO",
        snapshot=None,
        selected_evidence=(),
        missing_evidence_ids=(),
        stale_evidence_ids=(),
        conflicting_evidence_ids=(),
        request_fingerprint="a" * 64,
        recovery_fingerprint="b" * 64,
        explanation="ok",
    )


def test_replay():
    store = ContinuityStore()

    result = make_result()

    store.put(result)

    try:
        store.put(result)
        assert False
    except ContinuityReplayError:
        assert True
