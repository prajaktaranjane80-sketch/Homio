import pytest

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


def make_request(
    *,
    resolution_id: str = "requested-scope",
    evidence_ids: tuple[str, ...] = ("requested",),
    require_current: bool = True,
    require_canonical_when_available: bool = True,
) -> ResolutionRequest:
    return ResolutionRequest(
        resolution_id=resolution_id,
        subject="repository:HEAD",
        evidence_ids=evidence_ids,
        require_current=require_current,
        require_canonical_when_available=(
            require_canonical_when_available
        ),
    )


def test_unrequested_high_authority_evidence_is_never_selected():
    requested = make_evidence(
        evidence_id="requested",
        fingerprint="a" * 64,
    )
    unrelated = make_evidence(
        evidence_id="unrequested-canonical",
        authority=EvidenceAuthority.CANONICAL_STATE,
        canonical=True,
        fingerprint="b" * 64,
    )

    result = resolve_references(
        request=make_request(),
        evidence_items=(requested, unrelated),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.RESOLVED
    assert result[1] is not None
    assert result[1].evidence_id == "requested"
    assert tuple(item.evidence_id for item in result[2]) == (
        "requested",
    )


def test_requested_id_for_another_subject_is_missing():
    wrong_subject = make_evidence(
        evidence_id="requested",
        subject="state.json",
    )

    result = resolve_references(
        request=make_request(),
        evidence_items=(wrong_subject,),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.MISSING
    assert result[1] is None
    assert result[5] == ("requested",)


def test_canonical_evidence_takes_precedence_when_available():
    noncanonical = make_evidence(
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
        request=make_request(
            evidence_ids=("noncanonical", "canonical"),
        ),
        evidence_items=(noncanonical, canonical),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.RESOLVED
    assert result[1] is not None
    assert result[1].evidence_id == "canonical"


def test_request_cannot_disable_canonical_requirement():
    noncanonical = make_evidence(
        evidence_id="noncanonical",
    )
    canonical = make_evidence(
        evidence_id="canonical",
        canonical=True,
        fingerprint="b" * 64,
    )

    result = resolve_references(
        request=make_request(
            evidence_ids=("noncanonical", "canonical"),
            require_canonical_when_available=False,
        ),
        evidence_items=(noncanonical, canonical),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.BLOCKED
    assert result[1] is None
    assert "cannot disable" in result[6]


def test_request_cannot_disable_current_evidence_requirement():
    stale = make_evidence(
        evidence_id="requested",
        status=EvidenceStatus.STALE,
    )

    result = resolve_references(
        request=make_request(require_current=False),
        evidence_items=(stale,),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.BLOCKED
    assert result[1] is None
    assert "cannot disable" in result[6]


def test_unknown_evidence_cannot_be_selected_as_current():
    unknown = make_evidence(
        evidence_id="requested",
        status=EvidenceStatus.UNKNOWN,
    )

    result = resolve_references(
        request=make_request(),
        evidence_items=(unknown,),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.STALE
    assert result[1] is None


def test_duplicate_evidence_ids_fail_closed():
    first = make_evidence(
        evidence_id="requested",
        fingerprint="a" * 64,
    )
    second = make_evidence(
        evidence_id="requested",
        fingerprint="b" * 64,
    )

    result = resolve_references(
        request=make_request(),
        evidence_items=(first, second),
        policy=EvidencePolicy(),
    )

    assert result[0] is ResolutionDecision.CONFLICT
    assert result[1] is None
    assert "Duplicate" in result[6]


def test_invalid_policy_is_rejected_by_direct_resolver():
    evidence = make_evidence(
        evidence_id="requested",
        status=EvidenceStatus.CURRENT,
    )

    with pytest.raises(ValueError, match="unknown evidence"):
        resolve_references(
            request=make_request(),
            evidence_items=(evidence,),
            policy=EvidencePolicy(
                allow_unknown_status=True,
            ),
        )
