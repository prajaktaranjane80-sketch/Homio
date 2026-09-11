from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionDecision,
    ResolutionRequest,
)
from .evidence_registry import (
    EvidenceRegistry,
)
from .resolution_coordinator import (
    resolve_evidence,
)
from .resolution_store import (
    ResolutionStore,
)


def make():
    return EvidenceReference(
        evidence_id="ev-1",
        subject="repository:HEAD",
        evidence_type=EvidenceType.GIT,
        authority=EvidenceAuthority.GIT_TRANSACTION,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="GitTransactionResult",
        content_fingerprint="a" * 64,
        sequence=1,
    )


def test_resolution_coordinator():
    evidence = make()

    request = ResolutionRequest(
        resolution_id="r1",
        subject="repository:HEAD",
        evidence_ids=("ev-1",),
    )

    result = resolve_evidence(
        request=request,
        evidence_references=(evidence,),
        registry=EvidenceRegistry(),
        store=ResolutionStore(),
    )

    assert (
        result.decision
        is ResolutionDecision.RESOLVED
    )

    assert (
        result.selected_evidence
        is not None
    )
