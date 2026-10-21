from __future__ import annotations

from collections import Counter, defaultdict

from .continuity_models import (
    ContinuityEvidence,
    ContinuityStatus,
)


_STATUS_RANK = {
    ContinuityStatus.CURRENT: 3,
    ContinuityStatus.STALE: 2,
    ContinuityStatus.UNKNOWN: 1,
    ContinuityStatus.INVALID: 0,
}


def _evidence_rank(
    item: ContinuityEvidence,
) -> tuple[int, int, int]:
    """Rank by freshness first, then canonicality and immutability."""

    return (
        _STATUS_RANK[item.status],
        int(item.canonical),
        int(item.immutable),
    )


def _duplicate_ids(
    evidence_items: tuple[ContinuityEvidence, ...],
    required_ids: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    required = (
        set(required_ids)
        if required_ids is not None
        else None
    )

    counts = Counter(
        item.evidence_id
        for item in evidence_items
        if required is None or item.evidence_id in required
    )

    return tuple(
        sorted(
            evidence_id
            for evidence_id, count in counts.items()
            if count > 1
        )
    )


def select_current_evidence(
    evidence_items: tuple[ContinuityEvidence, ...],
    required_ids: tuple[str, ...],
):
    """Select current evidence, preferring canonical records per subject.

    Required IDs must be unique in the supplied evidence collection. The
    coordinator checks duplicates first and returns a typed blocked result.
    This lower-level helper raises rather than silently overwriting an ID.
    """

    duplicates = _duplicate_ids(
        evidence_items,
        required_ids,
    )
    if duplicates:
        raise ValueError(
            "Duplicate continuity evidence IDs: "
            + ", ".join(duplicates)
        )

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
        and by_id[evidence_id].status is ContinuityStatus.STALE
    )

    current_requested = tuple(
        by_id[evidence_id]
        for evidence_id in required_ids
        if evidence_id in by_id
        and by_id[evidence_id].status is ContinuityStatus.CURRENT
    )

    best_rank_by_subject: dict[str, tuple[int, int, int]] = {}

    for item in current_requested:
        rank = _evidence_rank(item)
        previous = best_rank_by_subject.get(item.subject)

        if previous is None or rank > previous:
            best_rank_by_subject[item.subject] = rank

    selected = tuple(
        item
        for item in current_requested
        if _evidence_rank(item)
        == best_rank_by_subject[item.subject]
    )

    return selected, missing, stale


def detect_identity_conflicts(
    evidence_items: tuple[ContinuityEvidence, ...],
) -> tuple[str, ...]:
    """Detect duplicate IDs and disagreements among equally ranked records."""

    conflicts = set(
        _duplicate_ids(evidence_items)
    )

    by_subject: dict[
        str,
        list[ContinuityEvidence],
    ] = defaultdict(list)

    for item in evidence_items:
        by_subject[item.subject].append(item)

    for subject_items in by_subject.values():
        highest_rank = max(
            _evidence_rank(item)
            for item in subject_items
        )

        strongest = tuple(
            item
            for item in subject_items
            if _evidence_rank(item) == highest_rank
        )

        fingerprints = {
            item.content_fingerprint
            for item in strongest
        }

        if len(fingerprints) > 1:
            conflicts.update(
                item.evidence_id
                for item in strongest
            )

    return tuple(sorted(conflicts))
