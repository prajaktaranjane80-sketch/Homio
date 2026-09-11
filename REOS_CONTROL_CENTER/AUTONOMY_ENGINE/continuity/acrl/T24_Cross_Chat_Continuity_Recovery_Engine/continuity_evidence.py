from __future__ import annotations

from .continuity_models import (
    ContinuityEvidence,
    ContinuityStatus,
)


def select_current_evidence(
    evidence_items: tuple[
        ContinuityEvidence, ...
    ],
    required_ids: tuple[str, ...],
):
    by_id = {
        item.evidence_id: item
        for item in evidence_items
    }

    missing = tuple(
        evidence_id
        for evidence_id in required_ids
        if evidence_id not in by_id
    )

    stale = tuple(
        evidence_id
        for evidence_id in required_ids
        if evidence_id in by_id
        and by_id[evidence_id].status
        is ContinuityStatus.STALE
    )

    selected = tuple(
        by_id[evidence_id]
        for evidence_id in required_ids
        if evidence_id in by_id
        and by_id[evidence_id].status
        is ContinuityStatus.CURRENT
    )

    return (
        selected,
        missing,
        stale,
    )


def detect_identity_conflicts(
    evidence_items: tuple[
        ContinuityEvidence, ...
    ],
) -> tuple[str, ...]:
    by_subject: dict[
        str,
        set[str],
    ] = {}

    for item in evidence_items:
        by_subject.setdefault(
            item.subject,
            set(),
        ).add(
            item.content_fingerprint
        )

    conflicts = set()

    for item in evidence_items:
        fingerprints = by_subject.get(
            item.subject,
            set(),
        )

        if len(fingerprints) > 1:
            conflicts.add(
                item.evidence_id
            )

    return tuple(
        sorted(conflicts)
    )
