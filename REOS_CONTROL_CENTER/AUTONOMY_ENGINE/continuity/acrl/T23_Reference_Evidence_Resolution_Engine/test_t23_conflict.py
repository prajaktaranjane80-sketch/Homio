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
    fingerprint,
):
    return EvidenceReference(
        evidence_id=evidence_id,
        subject="state",
        evidence_type=EvidenceType.STATE,
        authority=EvidenceAuthority.CANONICAL_STATE,
        status=EvidenceStatus.CURRENT,
        source_layer="T03",
        source_name="State",
        content_fingerprint=fingerprint,
        sequence=1,
        canonical=True,
    )


def test_conflicting_same_authority_evidence_fails_closed():
    result = resolve_references(
        request=ResolutionRequest(
            resolution_id="r",
            subject="state",
            evidence_ids=(
                "a",
                "b",
            ),
        ),
        evidence_items=(
            make(
                "a",
                "a" * 64,
            ),
            make(
                "b",
                "b" * 64,
            ),
        ),
        policy=EvidencePolicy(),
    )

    assert (
        result[0]
        is ResolutionDecision.CONFLICT
    )

    assert result[1] is None
