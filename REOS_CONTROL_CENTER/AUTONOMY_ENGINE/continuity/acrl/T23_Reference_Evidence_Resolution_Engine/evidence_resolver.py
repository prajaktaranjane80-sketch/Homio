from __future__ import annotations

from .evidence_models import (
    EvidenceReference,
    EvidenceStatus,
    ResolutionDecision,
    ResolutionRequest,
)
from .evidence_policy import (
    EvidencePolicy,
    authority_weight,
)
from .evidence_ranker import (
    sort_evidence,
)


def resolve_references(
    *,
    request: ResolutionRequest,
    evidence_items: tuple[
        EvidenceReference, ...
    ],
    policy: EvidencePolicy,
):
    """Resolve only the evidence explicitly requested for this subject.

    Fail closed when requested evidence is missing, unusable, stale, or
    ambiguous. Canonical evidence takes precedence when the request
    requires it and matching canonical evidence is available.
    """

    requested_ids = tuple(request.evidence_ids)
    requested_id_set = set(requested_ids)

    # Scope selection before ranking: unrelated evidence must never win
    # merely because it has greater authority or a canonical flag.
    candidates = tuple(
        item
        for item in evidence_items
        if item.evidence_id in requested_id_set
        and item.subject == request.subject
    )

    candidate_ids = {
        item.evidence_id
        for item in candidates
    }

    # An ID belonging to a different subject is not valid evidence for
    # this request. Treat it as unavailable instead of allowing an empty
    # selection to reach an unsafe candidates[0] access.
    missing = tuple(
        evidence_id
        for evidence_id in requested_ids
        if evidence_id not in candidate_ids
    )

    stale = tuple(
        item
        for item in candidates
        if item.status is EvidenceStatus.STALE
    )

    unknown = tuple(
        item
        for item in candidates
        if item.status is EvidenceStatus.UNKNOWN
    )

    if missing:
        return (
            ResolutionDecision.MISSING,
            None,
            candidates,
            tuple(),
            stale,
            missing,
            (
                "One or more requested evidence references are missing "
                "for the requested subject."
            ),
        )

    selection_pool = candidates

    if request.require_canonical_when_available:
        canonical_candidates = tuple(
            item
            for item in selection_pool
            if item.canonical
        )

        if canonical_candidates:
            selection_pool = canonical_candidates

    stale = tuple(
        item
        for item in selection_pool
        if item.status is EvidenceStatus.STALE
    )

    unknown = tuple(
        item
        for item in selection_pool
        if item.status is EvidenceStatus.UNKNOWN
    )

    if request.require_current:
        selectable = tuple(
            item
            for item in selection_pool
            if item.status is EvidenceStatus.CURRENT
        )
    else:
        selectable = selection_pool

    if not selectable:
        if request.require_current and (stale or unknown):
            return (
                ResolutionDecision.STALE,
                None,
                tuple(),
                tuple(),
                stale + unknown,
                tuple(),
                (
                    "No current selectable evidence is available. "
                    "Stale or unknown evidence cannot establish a "
                    "current resolution."
                ),
            )

        return (
            ResolutionDecision.FAIL_CLOSED,
            None,
            tuple(),
            selection_pool,
            stale + unknown,
            tuple(),
            (
                "No evidence remains selectable after applying the "
                "requested IDs, subject, canonical, and freshness "
                "constraints."
            ),
        )

    selectable = sort_evidence(
        selectable,
        preferred_authorities=request.preferred_authorities,
        policy=policy,
    )

    # The empty-selection guards above intentionally precede this access.
    selected = selectable[0]

    highest_weight = authority_weight(
        selected.authority,
        policy,
    )

    same_subject = tuple(
        item
        for item in selectable
        if item.subject == selected.subject
    )

    top_authority = tuple(
        item
        for item in same_subject
        if authority_weight(
            item.authority,
            policy,
        )
        == highest_weight
    )

    identities = {
        item.content_fingerprint
        for item in top_authority
    }

    if len(identities) > 1:
        return (
            ResolutionDecision.CONFLICT,
            None,
            selectable,
            tuple(),
            stale,
            tuple(),
            (
                "Authoritative evidence contains contradictory "
                "identities."
            ),
        )

    rejected = tuple(
        item
        for item in selectable
        if item.evidence_id != selected.evidence_id
    )

    return (
        ResolutionDecision.RESOLVED,
        selected,
        selectable,
        rejected,
        stale,
        tuple(),
        "Deterministic authoritative evidence resolved.",
    )
