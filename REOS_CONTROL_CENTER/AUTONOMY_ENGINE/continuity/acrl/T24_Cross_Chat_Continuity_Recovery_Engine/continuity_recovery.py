from __future__ import annotations

from .continuity_evidence import (
    detect_identity_conflicts,
    select_current_evidence,
)
from .continuity_models import (
    ContinuityDecision,
    ContinuityEvidence,
    ContinuityRequest,
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
    conflicts = detect_identity_conflicts(
        evidence_items
    )

    if conflicts:
        return (
            ContinuityDecision.AMBIGUOUS,
            conflicts,
            tuple(),
            tuple(),
            "Contradictory continuity evidence detected.",
        )

    selected, missing, stale = (
        select_current_evidence(
            evidence_items,
            request.evidence_ids,
        )
    )

    if missing:
        return (
            ContinuityDecision.BLOCKED,
            tuple(),
            missing,
            stale,
            "Required continuity evidence is missing.",
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
            "No recoverable authoritative evidence exists.",
        )

    return (
        ContinuityDecision.RECOVERED,
        tuple(),
        tuple(),
        tuple(),
        "Continuity evidence is sufficient for reconstruction.",
    )
