from __future__ import annotations

from collections import Counter

from .continuity_evidence import (
    detect_identity_conflicts,
    select_current_evidence,
)
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
    ContinuityStatus,
)
from .continuity_policy import ContinuityPolicy


def evaluate_recovery(
    *,
    request: ContinuityRequest,
    evidence_items: tuple[ContinuityEvidence, ...],
    policy: ContinuityPolicy,
):
    """Evaluate requested continuity evidence and fail closed on ambiguity."""

    requested_ids = set(request.evidence_ids)

    scoped_evidence = tuple(
        item
        for item in evidence_items
        if item.evidence_id in requested_ids
    )

    duplicate_counts = Counter(
        item.evidence_id
        for item in scoped_evidence
    )
    duplicate_ids = tuple(
        sorted(
            evidence_id
            for evidence_id, count in duplicate_counts.items()
            if count > 1
        )
    )

    if duplicate_ids:
        return (
            ContinuityDecision.BLOCKED,
            duplicate_ids,
            tuple(),
            tuple(),
            (
                "Duplicate continuity evidence IDs cannot establish "
                "an unambiguous recovery."
            ),
        )

    conflicts = detect_identity_conflicts(scoped_evidence)

    if conflicts:
        return (
            ContinuityDecision.AMBIGUOUS,
            conflicts,
            tuple(),
            tuple(),
            (
                "Equally ranked continuity evidence contains "
                "contradictory identities."
            ),
        )

    selected, missing, stale = select_current_evidence(
        evidence_items,
        request.evidence_ids,
    )

    if missing:
        return (
            ContinuityDecision.BLOCKED,
            tuple(),
            missing,
            stale,
            "Required continuity evidence is missing.",
        )

    unknown_ids = tuple(
        sorted(
            {
                item.evidence_id
                for item in scoped_evidence
                if item.status is ContinuityStatus.UNKNOWN
            }
        )
    )

    if unknown_ids:
        return (
            ContinuityDecision.BLOCKED,
            tuple(),
            tuple(),
            stale,
            (
                "Required continuity evidence has UNKNOWN status and "
                "cannot establish current context: "
                f"{', '.join(unknown_ids)}."
            ),
        )

    if stale and policy.require_current_evidence:
        return (
            ContinuityDecision.STALE,
            tuple(),
            tuple(),
            stale,
            "Required continuity evidence is stale.",
        )

    if not selected:
        return (
            ContinuityDecision.FAIL_CLOSED,
            tuple(),
            tuple(),
            stale,
            "No recoverable current authoritative evidence exists.",
        )

    return (
        ContinuityDecision.RECOVERED,
        tuple(),
        tuple(),
        tuple(),
        "Continuity evidence is sufficient for reconstruction.",
    )
