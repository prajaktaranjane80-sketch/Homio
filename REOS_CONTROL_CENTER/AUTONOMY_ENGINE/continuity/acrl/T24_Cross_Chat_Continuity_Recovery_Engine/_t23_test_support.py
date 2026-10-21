from __future__ import annotations

from ..T23_Reference_Evidence_Resolution_Engine.evidence_models import (
    EvidenceAuthority,
    EvidenceReference,
    EvidenceStatus,
    EvidenceType,
    ResolutionDecision,
    ResolutionRequest,
)
from ..T23_Reference_Evidence_Resolution_Engine.evidence_registry import (
    EvidenceRegistry,
)
from ..T23_Reference_Evidence_Resolution_Engine.resolution_coordinator import (
    resolve_evidence,
)
from ..T23_Reference_Evidence_Resolution_Engine.resolution_store import (
    ResolutionStore,
)
from .continuity_models import (
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)


_AUTHORITY_PLAN = (
    (EvidenceAuthority.CANONICAL_STATE, EvidenceType.STATE),
    (EvidenceAuthority.RESUME_SAFETY, EvidenceType.RESUME),
    (EvidenceAuthority.EXECUTION_CHECKPOINT, EvidenceType.CHECKPOINT),
    (
        EvidenceAuthority.EXECUTION_AUTHORIZATION,
        EvidenceType.AUTHORIZATION,
    ),
    (EvidenceAuthority.GIT_TRANSACTION, EvidenceType.GIT),
    (EvidenceAuthority.VERIFIED_REPAIR, EvidenceType.REPAIR),
    (EvidenceAuthority.CHANGE_IMPACT, EvidenceType.IMPACT),
    (EvidenceAuthority.TEST_DIAGNOSIS, EvidenceType.DIAGNOSIS),
    (EvidenceAuthority.GENERAL_EVIDENCE, EvidenceType.GENERAL),
)


def build_t23_source_store(
    request: ContinuityRequest,
    evidence_items: tuple[ContinuityEvidence, ...],
) -> ResolutionStore:
    """Create an actual T23 resolution store for positive-path tests."""

    evidence_by_id = {
        item.evidence_id: item
        for item in evidence_items
    }

    if len(evidence_by_id) != len(evidence_items):
        raise ValueError(
            "T23 test fixtures cannot contain duplicate evidence IDs."
        )

    missing_ids = tuple(
        evidence_id
        for evidence_id in request.evidence_ids
        if evidence_id not in evidence_by_id
    )

    if missing_ids:
        raise ValueError(
            "T23 test fixtures are missing requested evidence: "
            + ", ".join(missing_ids)
        )

    if len(request.evidence_ids) > len(_AUTHORITY_PLAN):
        raise ValueError(
            "The T23 test fixture authority plan is too small."
        )

    references: list[EvidenceReference] = []

    for index, evidence_id in enumerate(request.evidence_ids):
        evidence = evidence_by_id[evidence_id]

        if evidence.status is not ContinuityStatus.CURRENT:
            raise ValueError(
                "Positive-path T23 fixtures require CURRENT evidence."
            )

        if not evidence.immutable:
            raise ValueError(
                "Positive-path T23 fixtures require immutable evidence."
            )

        authority, evidence_type = _AUTHORITY_PLAN[index]

        references.append(
            EvidenceReference(
                evidence_id=evidence.evidence_id,
                subject=f"continuity:{request.project_id}",
                evidence_type=evidence_type,
                authority=authority,
                status=EvidenceStatus.CURRENT,
                source_layer=evidence.source_layer,
                source_name=evidence.source_name,
                content_fingerprint=evidence.content_fingerprint,
                sequence=evidence.sequence,
                immutable=evidence.immutable,
                canonical=evidence.canonical,
            )
        )

    t23_request = ResolutionRequest(
        resolution_id=request.source_resolution_id,
        subject=f"continuity:{request.project_id}",
        evidence_ids=request.evidence_ids,
        require_current=True,
        require_canonical_when_available=True,
    )

    registry = EvidenceRegistry()
    store = ResolutionStore()

    result = resolve_evidence(
        request=t23_request,
        evidence_references=tuple(references),
        registry=registry,
        store=store,
    )

    if result.decision is not ResolutionDecision.RESOLVED:
        raise AssertionError(
            "Expected the test T23 resolver to return RESOLVED; "
            f"received {result.decision.value}: {result.explanation}"
        )

    stored_result = store.get(request.source_resolution_id)

    if stored_result is None:
        raise AssertionError(
            "The T23 resolver did not persist its successful resolution."
        )

    return store
