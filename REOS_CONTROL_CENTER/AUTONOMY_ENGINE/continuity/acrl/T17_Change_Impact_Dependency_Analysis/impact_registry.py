from __future__ import annotations

from enum import Enum


class ImpactLevel(str, Enum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"


class T17Decision(str, Enum):
    ANALYZE = "ANALYZE"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


class ImpactReason(str, Enum):
    DIRECT_MATCH = "DIRECT_MATCH"
    DEPENDENCY_OF_CHANGED_MODULE = "DEPENDENCY_OF_CHANGED_MODULE"
    PROTECTED_FILE = "PROTECTED_FILE"
    UNKNOWN_PATH = "UNKNOWN_PATH"
    SECURITY_BOUNDARY = "SECURITY_BOUNDARY"
    GRAPH_UNAVAILABLE = "GRAPH_UNAVAILABLE"


IMPACT_LEVELS = tuple(
    item.value
    for item in ImpactLevel
)

IMPACT_REASONS = tuple(
    item.value
    for item in ImpactReason
)

DECISIONS = tuple(
    item.value
    for item in T17Decision
)


__all__ = [
    "ImpactLevel",
    "T17Decision",
    "ImpactReason",
    "IMPACT_LEVELS",
    "IMPACT_REASONS",
    "DECISIONS",
]
