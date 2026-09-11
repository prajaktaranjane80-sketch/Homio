from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionDecision,
    ResolutionResult,
)
from .resolution_store import (
    ResolutionReplayError,
    ResolutionStore,
)


def make_result():
    evidence = EvidenceReference(
        evidence_id="ev",
        subject="x",
        evidence_type=EvidenceType.GIT,
        authority=EvidenceAuthority.GIT_TRANSACTION,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="test",
        content_fingerprint="a" * 64,
        sequence=1,
    )

    return ResolutionResult(
        schema_version="1.0",
        decision=ResolutionDecision.RESOLVED,
        resolution_id="r1",
        subject="x",
        selected_evidence=evidence,
        candidates=(evidence,),
        rejected_evidence=(),
        conflicting_evidence=(),
        stale_evidence=(),
        missing_evidence_ids=(),
        request_fingerprint="b" * 64,
        resolution_fingerprint="c" * 64,
        explanation="ok",
    )


def test_store_replay():
    store = ResolutionStore()

    result = make_result()

    store.put(result)

    try:
        store.put(result)
        assert False
    except ResolutionReplayError:
        assert True
