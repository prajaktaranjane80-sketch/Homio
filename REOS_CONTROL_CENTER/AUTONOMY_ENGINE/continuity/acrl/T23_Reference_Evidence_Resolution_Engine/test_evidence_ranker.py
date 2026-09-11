from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
)
from .evidence_policy import (
    EvidencePolicy,
)
from .evidence_ranker import (
    sort_evidence,
)


def make(
    evidence_id,
    authority,
):
    return EvidenceReference(
        evidence_id=evidence_id,
        subject="repo",
        evidence_type=EvidenceType.GENERAL,
        authority=authority,
        status=EvidenceStatus.CURRENT,
        source_layer="T23",
        source_name="test",
        content_fingerprint=(
            "a" * 64
        ),
        sequence=1,
    )


def test_higher_authority_wins():
    items = sort_evidence(
        (
            make(
                "general",
                EvidenceAuthority.GENERAL_EVIDENCE,
            ),
            make(
                "state",
                EvidenceAuthority.CANONICAL_STATE,
            ),
        ),
        preferred_authorities=(),
        policy=EvidencePolicy(),
    )

    assert (
        items[0].evidence_id
        == "state"
    )
