from .reconciliation_models import ConflictKind


_PRECEDENCE = {
    ConflictKind.IDENTITY_CONFLICT: 100,
    ConflictKind.REPLAY_CONFLICT: 95,
    ConflictKind.CONTINUITY_CONFLICT: 90,
    ConflictKind.EVIDENCE_CONFLICT: 80,
    ConflictKind.DEPENDENCY_CONFLICT: 70,
    ConflictKind.STATE_MISMATCH: 60,
    ConflictKind.RESOURCE_CONFLICT: 50,
    ConflictKind.PRIORITY_CONFLICT: 40,
    ConflictKind.UNKNOWN: 10,
    ConflictKind.NONE: 0,
}


def precedence(kind: ConflictKind) -> int:
    return _PRECEDENCE[kind]
