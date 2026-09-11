from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionDecision,
    ResolutionRequest,
)
from .evidence_policy import (
    EvidencePolicy,
)
from .evidence_resolver import (
    resolve_references,
)


def make(
    evidence_id,
    authority,
    fingerprint,
):
    return EvidenceReference(
        evidence_id=evidence_id,
        subject="repository:HEAD",
        evidence_type=EvidenceType.GIT,
        authority=authority,
        status=EvidenceStatus.CURRENT,
        source_layer="T21",
        source_name="test",
        content_fingerprint=fingerprint,
        sequence=1,
    )


def test_authoritative_evidence_selected():
    result = resolve_references(
        request=ResolutionRequest(
            resolution_id="r1",
            subject="repository:HEAD",
            evidence_ids=(
                "ev1",
                "ev2",
            ),
        ),
        evidence_items=(
            make(
                "ev1",
                EvidenceAuthority.GENERAL_EVIDENCE,
                "a" * 64,
            ),
            make(
                "ev2",
                EvidenceAuthority.GIT_TRANSACTION,
                "b" * 64,
            ),
        ),
        policy=EvidencePolicy(),
    )

    assert (
        result[0]
        is ResolutionDecision.RESOLVED
    )

    assert (
        result[1].evidence_id
        == "ev2"
    )
