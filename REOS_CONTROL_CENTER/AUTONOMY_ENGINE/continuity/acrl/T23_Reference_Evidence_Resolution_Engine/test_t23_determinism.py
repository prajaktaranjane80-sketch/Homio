from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionRequest,
)
from .resolution_coordinator import (
    resolve_evidence,
)
from .evidence_registry import (
    EvidenceRegistry,
)
from .resolution_store import (
    ResolutionStore,
)


def make_evidence():
    return EvidenceReference(
        evidence_id="ev",
        subject="commit",
        evidence_type=EvidenceType.GIT,
        authority=EvidenceAuthority.GIT_TRANSACTION,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="GitTransaction",
        content_fingerprint="a" * 64,
        sequence=1,
    )


def make_request():
    return ResolutionRequest(
        resolution_id="resolution",
        subject="commit",
        evidence_ids=("ev",),
    )


def test_same_inputs_produce_same_identity():
    first = resolve_evidence(
        request=make_request(),
        evidence_references=(
            make_evidence(),
        ),
        registry=EvidenceRegistry(),
        store=ResolutionStore(),
    )

    second = resolve_evidence(
        request=make_request(),
        evidence_references=(
            make_evidence(),
        ),
        registry=EvidenceRegistry(),
        store=ResolutionStore(),
    )

    assert (
        first.resolution_fingerprint
        == second.resolution_fingerprint
    )
