from __future__ import annotations

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
from .continuity_policy import (
    ContinuityPolicy,
)


def evaluate_recovery(
    *,
    request: ContinuityRequest,
    evidence_items: tuple[
        ContinuityEvidence, ...
    ],
    policy: ContinuityPolicy,
):
    """Evaluate only requested evidence and fail closed on unknown status."""

    requested_ids = frozenset(request.evidence_ids)

    # Unrequested evidence must not create an unrelated conflict or
    # influence the decision for this particular recovery request.
    scoped_evidence = tuple(
        item
        for item in evidence_items
        if item.evidence_id in requested_ids
    )

    conflicts = detect_identity_conflicts(
        scoped_evidence
    )

    selected, missing, stale = select_current_evidence(
        evidence_items,
        request.evidence_ids,
    )

    if conflicts:
        return (
            ContinuityDecision.AMBIGUOUS,
            conflicts,
            tuple(),
            tuple(),
            "Contradictory requested continuity evidence detected.",
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
