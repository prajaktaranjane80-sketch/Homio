from conflict_evidence import evidence_satisfies
from precedence_engine import precedence
from reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    Resolution,
    ResolutionKind,
)


def resolve_conflict(
    conflict: ConflictRecord,
    *,
    evidence_ids: tuple[str, ...],
    allow_precedence: bool,
) -> Resolution | None:
    if not evidence_satisfies(conflict, evidence_ids):
        return None

    if conflict.kind in {
        ConflictKind.IDENTITY_CONFLICT,
        ConflictKind.REPLAY_CONFLICT,
    }:
        return Resolution(
            conflict_id=conflict.conflict_id,
            kind=ResolutionKind.FAIL_CLOSED,
            selected_value=None,
            rationale="Unsafe identity or replay conflict.",
            evidence_ids=conflict.evidence_ids,
        )

    if allow_precedence and conflict.left_value == conflict.right_value:
        return Resolution(
            conflict_id=conflict.conflict_id,
            kind=ResolutionKind.PRECEDENCE,
            selected_value=conflict.left_value,
            rationale=f"Equivalent values resolved at precedence {precedence(conflict.kind)}.",
            evidence_ids=conflict.evidence_ids,
        )

    if allow_precedence and conflict.source_left < conflict.source_right:
        selected = conflict.left_value
    elif allow_precedence:
        selected = conflict.right_value
    else:
        return None

    return Resolution(
        conflict_id=conflict.conflict_id,
        kind=ResolutionKind.PRECEDENCE,
        selected_value=selected,
        rationale="Deterministic source precedence applied.",
        evidence_ids=conflict.evidence_ids,
    )
