from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class TruthRole(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    DERIVED = "DERIVED"
    CONTEXTUAL = "CONTEXTUAL"
    UNTRUSTED = "UNTRUSTED"


class SyncStatus(str, Enum):
    SYNCHRONIZED = "SYNCHRONIZED"
    DRIFTED = "DRIFTED"
    CONFLICT = "CONFLICT"
    INVALID = "INVALID"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"


class ConflictSeverity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class ArtifactTruth:
    artifact_id: str
    path: str
    role: TruthRole
    present: bool
    digest: str | None
    semantic_digest: str | None
    claims: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Conflict:
    conflict_id: str
    severity: ConflictSeverity
    subject: str
    authoritative_value: Any
    observed_value: Any
    source_path: str
    reason: str


@dataclass(frozen=True)
class CanonicalManifest:
    schema_version: str
    project: str
    branch: str
    authority_id: str
    canonical_state_path: str
    state_digest: str
    state_revision: str
    current_gate: str
    current_task: str
    current_subtask: str | None
    execution_status: str
    derived_artifacts: tuple[ArtifactTruth, ...]
    conflicts: tuple[Conflict, ...]
    manifest_digest: str


@dataclass(frozen=True)
class ReconciliationPlan:
    plan_id: str
    base_state_digest: str
    actions: tuple[str, ...]
    targets: tuple[str, ...]
    blocked: bool
    reason: str


@dataclass(frozen=True)
class SyncReceipt:
    receipt_id: str
    manifest_digest: str
    plan_id: str
    status: SyncStatus
    synchronized_targets: tuple[str, ...]
    blocked_targets: tuple[str, ...]
    receipt_digest: str
