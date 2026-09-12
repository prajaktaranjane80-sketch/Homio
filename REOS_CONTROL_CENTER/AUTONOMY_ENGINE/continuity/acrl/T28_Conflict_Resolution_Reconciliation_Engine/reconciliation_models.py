from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConflictKind(str, Enum):
    NONE = "NONE"
    STATE_MISMATCH = "STATE_MISMATCH"
    DEPENDENCY_CONFLICT = "DEPENDENCY_CONFLICT"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    CONTINUITY_CONFLICT = "CONTINUITY_CONFLICT"
    REPLAY_CONFLICT = "REPLAY_CONFLICT"
    PRIORITY_CONFLICT = "PRIORITY_CONFLICT"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    UNKNOWN = "UNKNOWN"


class ConflictSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResolutionKind(str, Enum):
    NONE = "NONE"
    PRECEDENCE = "PRECEDENCE"
    EVIDENCE_BACKED = "EVIDENCE_BACKED"
    STATE_RECONCILIATION = "STATE_RECONCILIATION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FAIL_CLOSED = "FAIL_CLOSED"


class ReconciliationStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    RECONCILED = "RECONCILED"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class ReconciliationDecision(str, Enum):
    RECONCILED = "RECONCILED"
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
    BLOCKED = "BLOCKED"
    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    NO_SAFE_RESOLUTION = "NO_SAFE_RESOLUTION"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class ConflictRecord:
    conflict_id: str
    kind: ConflictKind
    severity: ConflictSeverity
    subject_id: str
    left_value: Any
    right_value: Any
    source_left: str
    source_right: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReconciliationPolicy:
    policy_version: str = "1.0"
    require_evidence_for_high_conflict: bool = True
    allow_precedence_resolution: bool = True
    allow_human_boundary: bool = True


@dataclass(frozen=True)
class ReconciliationRequest:
    reconciliation_id: str
    scheduler_fingerprint: str
    continuity_fingerprint: str
    evidence_fingerprint: str
    policy: ReconciliationPolicy
    conflicts: tuple[ConflictRecord, ...] = ()


@dataclass(frozen=True)
class Resolution:
    conflict_id: str
    kind: ResolutionKind
    selected_value: Any
    rationale: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReconciliationSnapshot:
    reconciliation_id: str
    status: ReconciliationStatus
    decision: ReconciliationDecision
    resolutions: tuple[Resolution, ...]
    unresolved_conflicts: tuple[str, ...]
    fingerprint: str


@dataclass(frozen=True)
class ReconciliationResult:
    snapshot: ReconciliationSnapshot
    audit: dict[str, Any] = field(default_factory=dict)
