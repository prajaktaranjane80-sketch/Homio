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
    candidates = tuple(
        item
        for item in evidence_items
        if item.subject
        == request.subject
    )

    stale = tuple(
        item
        for item in candidates
        if item.status
        is EvidenceStatus.STALE
    )

    unknown = tuple(
        item
        for item in candidates
        if item.status
        is EvidenceStatus.UNKNOWN
    )

    if request.require_current:
        selectable = tuple(
            item
            for item in candidates
            if item.status
            is EvidenceStatus.CURRENT
        )
    else:
        selectable = candidates

    selectable = sort_evidence(
        selectable,
        preferred_authorities=(
            request.preferred_authorities
        ),
        policy=policy,
    )

    missing = tuple(
        evidence_id
        for evidence_id in request.evidence_ids
        if not any(
            item.evidence_id == evidence_id
            for item in evidence_items
        )
    )

    if missing:
        return (
            ResolutionDecision.MISSING,
            None,
            selectable,
            tuple(),
            stale,
            missing,
            "One or more requested evidence references are missing.",
        )

    if request.require_current and not selectable:
        return (
            ResolutionDecision.STALE,
            None,
            tuple(),
            tuple(),
            stale + unknown,
            tuple(),
            "No current evidence is available.",
        )

    selected = selectable[0]

    highest_weight = authority_weight(
        selected.authority,
        policy,
    )

    same_subject = tuple(
        item
        for item in selectable
        if item.subject
        == selected.subject
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
            tuple(top_authority),
            stale,
            tuple(),
            "Authoritative evidence contains contradictory identities.",
        )

    rejected = tuple(
        item
        for item in selectable
        if item.evidence_id
        != selected.evidence_id
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
