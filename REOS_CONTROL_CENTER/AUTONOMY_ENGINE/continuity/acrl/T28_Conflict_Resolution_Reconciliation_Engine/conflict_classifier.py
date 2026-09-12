from .reconciliation_models import (
    ConflictKind,
    ConflictRecord,
    ConflictSeverity,
)


def classify(
    *,
    conflict_id: str,
    subject_id: str,
    left_value,
    right_value,
    source_left: str,
    source_right: str,
    reason: str,
) -> ConflictRecord:
    mapping = {
        "state": ConflictKind.STATE_MISMATCH,
        "dependency": ConflictKind.DEPENDENCY_CONFLICT,
        "evidence": ConflictKind.EVIDENCE_CONFLICT,
        "continuity": ConflictKind.CONTINUITY_CONFLICT,
        "replay": ConflictKind.REPLAY_CONFLICT,
        "priority": ConflictKind.PRIORITY_CONFLICT,
        "resource": ConflictKind.RESOURCE_CONFLICT,
        "identity": ConflictKind.IDENTITY_CONFLICT,
    }

    kind = mapping.get(reason, ConflictKind.UNKNOWN)

    severity = (
        ConflictSeverity.CRITICAL
        if kind in {
            ConflictKind.IDENTITY_CONFLICT,
            ConflictKind.REPLAY_CONFLICT,
            ConflictKind.CONTINUITY_CONFLICT,
        }
        else ConflictSeverity.HIGH
    )

    return ConflictRecord(
        conflict_id=conflict_id,
        kind=kind,
        severity=severity,
        subject_id=subject_id,
        left_value=left_value,
        right_value=right_value,
        source_left=source_left,
        source_right=source_right,
    )
