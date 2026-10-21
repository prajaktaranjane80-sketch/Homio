from __future__ import annotations

from collections import Counter

from .evidence_models import (
    EvidenceReference,
    EvidenceStatus,
    ResolutionDecision,
    ResolutionRequest,
)
from .evidence_policy import (
    EvidencePolicy,
    authority_weight,
    validate_policy,
)
from .evidence_ranker import sort_evidence
from .evidence_validation import (
    validate_evidence,
    validate_resolution_request,
)


def resolve_references(
    *,
    request: ResolutionRequest,
    evidence_items: tuple[EvidenceReference, ...],
    policy: EvidencePolicy,
):
    """Resolve only requested evidence under mandatory safety policy."""

    validate_policy(policy)
    validate_resolution_request(request)

    for item in evidence_items:
        validate_evidence(item, policy)

    # A request can strengthen the default rules, but cannot weaken them.
    if not request.require_current:
        return (
            ResolutionDecision.BLOCKED,
            None,
            tuple(),
            tuple(),
            tuple(),
            tuple(),
            "Policy requires current evidence; the request cannot disable it.",
        )

    requested_ids = tuple(request.evidence_ids)
    requested_id_set = set(requested_ids)

    duplicate_counts = Counter(
        item.evidence_id
        for item in evidence_items
        if item.evidence_id in requested_id_set
    )
    duplicate_ids = tuple(
        sorted(
            evidence_id
            for evidence_id, count in duplicate_counts.items()
            if count > 1
        )
    )

    if duplicate_ids:
        duplicate_items = tuple(
            item
            for item in evidence_items
            if item.evidence_id in duplicate_ids
        )
        return (
            ResolutionDecision.CONFLICT,
            None,
            duplicate_items,
            tuple(),
            tuple(),
            tuple(),
            "Duplicate requested evidence IDs are ambiguous.",
        )

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

    missing = tuple(
        evidence_id
        for evidence_id in requested_ids
        if evidence_id not in candidate_ids
    )

    non_current = tuple(
        item
        for item in candidates
        if item.status is not EvidenceStatus.CURRENT
    )

    if missing:
        return (
            ResolutionDecision.MISSING,
            None,
            candidates,
            tuple(),
            non_current,
            missing,
            (
                "One or more requested evidence references are missing "
                "for the requested subject."
            ),
        )

    canonical_candidates = tuple(
        item
        for item in candidates
        if item.canonical
    )

    if (
        canonical_candidates
        and not request.require_canonical_when_available
    ):
        return (
            ResolutionDecision.BLOCKED,
            None,
            candidates,
            tuple(),
            non_current,
            tuple(),
            (
                "The request cannot disable the canonical-evidence "
                "requirement when canonical evidence is available."
            ),
        )

    # Canonical evidence takes precedence when it exists. The policy
    # validator prevents unsafe non-canonical overrides.
    selection_pool = (
        canonical_candidates
        if canonical_candidates
        else candidates
    )

    selectable = tuple(
        item
        for item in selection_pool
        if item.status is EvidenceStatus.CURRENT
    )

    if not selectable:
        if non_current:
            return (
                ResolutionDecision.STALE,
                None,
                tuple(),
                tuple(),
                non_current,
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
            tuple(),
            tuple(),
            "No evidence remains selectable after policy constraints.",
        )

    selectable = sort_evidence(
        selectable,
        preferred_authorities=request.preferred_authorities,
        policy=policy,
    )

    selected = selectable[0]

    highest_weight = authority_weight(
        selected.authority,
        policy,
    )

    top_authority = tuple(
        item
        for item in selectable
        if authority_weight(item.authority, policy)
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
            non_current,
            tuple(),
            "Authoritative evidence contains contradictory identities.",
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
        non_current,
        tuple(),
        "Deterministic authoritative evidence resolved.",
    )
