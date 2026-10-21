from .evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionDecision,
    ResolutionRequest,
)
from .evidence_policy import EvidencePolicy
from .evidence_resolver import resolve_references


def make_evidence(
    *,
    evidence_id: str,
    subject: str = "repository:HEAD",
    authority: EvidenceAuthority = EvidenceAuthority.GENERAL_EVIDENCE,
    status: EvidenceStatus = EvidenceStatus.CURRENT,
    canonical: bool = False,
    fingerprint: str = "a" * 64,
) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=evidence_id,
        subject=subject,
        evidence_type=EvidenceType.GIT,
        authority=authority,
        status=status,
        source_layer="T21",
        source_name="RequestedEvidenceScopeTest",
        content_fingerprint=fingerprint,
        sequence=1,
        immutable=True,
        canonical=canonical,
    )


def test_unrequested_high_authority_evidence_is_never_selected():
    requested = make_evidence(
        evidence_id="requested",
        authority=EvidenceAuthority.GENERAL_EVIDENCE,
        fingerprint="a" * 64,
    )
    unrelated = make_evidence(
        evidence_id="unrequested-canonical",
        authority=EvidenceAuthority.CANONICAL_STATE,
        canonical=True,
        fingerprint="b" * 64,
    )

    result = resolve_references(
        request=ResolutionRequest(
            resolution_id="requested-scope",
            subject="repository:HEAD",
            evidence_ids=("requested",),
        ),
        evidence_items=(requested, unrelated),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.RESOLVED
    assert result[1] is not None
    assert result[1].evidence_id == "requested"
    assert tuple(item.evidence_id for item in result[2]) == (
        "requested",
    )


def test_requested_id_for_another_subject_is_missing_not_an_index_error():
    wrong_subject = make_evidence(
        evidence_id="requested",
        subject="state.json",
    )

    result = resolve_references(
        request=ResolutionRequest(
            resolution_id="wrong-subject",
            subject="repository:HEAD",
            evidence_ids=("requested",),
            require_current=False,
        ),
        evidence_items=(wrong_subject,),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.MISSING
    assert result[1] is None
    assert result[5] == ("requested",)


def test_canonical_requested_evidence_takes_precedence_when_available():
    high_authority_noncanonical = make_evidence(
        evidence_id="noncanonical",
        authority=EvidenceAuthority.CANONICAL_STATE,
        canonical=False,
        fingerprint="a" * 64,
    )
    canonical = make_evidence(
        evidence_id="canonical",
        authority=EvidenceAuthority.GENERAL_EVIDENCE,
        canonical=True,
        fingerprint="b" * 64,
    )

    result = resolve_references(
        request=ResolutionRequest(
            resolution_id="canonical-precedence",
            subject="repository:HEAD",
            evidence_ids=("noncanonical", "canonical"),
            require_canonical_when_available=True,
        ),
        evidence_items=(
            high_authority_noncanonical,
            canonical,
        ),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.RESOLVED
    assert result[1] is not None
    assert result[1].evidence_id == "canonical"


def test_unknown_evidence_cannot_be_selected_as_current():
    unknown = make_evidence(
        evidence_id="unknown",
        status=EvidenceStatus.UNKNOWN,
    )

    result = resolve_references(
        request=ResolutionRequest(
            resolution_id="unknown-freshness",
            subject="repository:HEAD",
            evidence_ids=("unknown",),
            require_current=True,
        ),
        evidence_items=(unknown,),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.STALE
    assert result[1] is None
