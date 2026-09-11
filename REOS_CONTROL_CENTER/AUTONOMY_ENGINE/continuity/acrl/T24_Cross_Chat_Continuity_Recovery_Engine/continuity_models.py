from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ContinuityStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    INVALID = "INVALID"


class ContinuityDecision(str, Enum):
    RECOVERED = "RECOVERED"
    READ_ONLY = "READ_ONLY"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"
    STALE = "STALE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class ContinuityEvidence:
    evidence_id: str
    subject: str
    source_layer: str
    source_name: str
    status: ContinuityStatus
    content_fingerprint: str
    sequence: int
    canonical: bool = False
    immutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "subject": self.subject,
            "source_layer": self.source_layer,
            "source_name": self.source_name,
            "status": self.status.value,
            "content_fingerprint": self.content_fingerprint,
            "sequence": self.sequence,
            "canonical": self.canonical,
            "immutable": self.immutable,
        }


@dataclass(frozen=True, slots=True)
class ContinuitySnapshot:
    schema_version: str
    continuity_version: str

    project_id: str
    project_fingerprint: str

    state_fingerprint: str
    branch: str
    commit_sha: str

    phase: str
    gate_id: str
    gate_status: str
    current_task: str
    current_subtask: str
    current_subtask_status: str

    completed_subtasks: tuple[str, ...]
    pending_subtasks: tuple[str, ...]

    execution_checkpoint_id: str | None
    execution_checkpoint_fingerprint: str | None

    evidence_fingerprints: tuple[str, ...]

    source_resolution_id: str
    recovery_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "continuity_version": self.continuity_version,
            "project_id": self.project_id,
            "project_fingerprint": self.project_fingerprint,
            "state_fingerprint": self.state_fingerprint,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "phase": self.phase,
            "gate_id": self.gate_id,
            "gate_status": self.gate_status,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "current_subtask_status": self.current_subtask_status,
            "completed_subtasks": list(self.completed_subtasks),
            "pending_subtasks": list(self.pending_subtasks),
            "execution_checkpoint_id": (
                self.execution_checkpoint_id
            ),
            "execution_checkpoint_fingerprint": (
                self.execution_checkpoint_fingerprint
            ),
            "evidence_fingerprints": list(
                self.evidence_fingerprints
            ),
            "source_resolution_id": self.source_resolution_id,
            "recovery_fingerprint": self.recovery_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ContinuityRequest:
    recovery_id: str
    project_id: str
    source_resolution_id: str

    expected_project_fingerprint: str
    expected_state_fingerprint: str

    expected_branch: str
    expected_commit_sha: str

    evidence_ids: tuple[str, ...]

    execution_checkpoint_id: str | None = None
    execution_checkpoint_fingerprint: str | None = None

    recovery_nonce: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "project_id": self.project_id,
            "source_resolution_id": (
                self.source_resolution_id
            ),
            "expected_project_fingerprint": (
                self.expected_project_fingerprint
            ),
            "expected_state_fingerprint": (
                self.expected_state_fingerprint
            ),
            "expected_branch": self.expected_branch,
            "expected_commit_sha": (
                self.expected_commit_sha
            ),
            "evidence_ids": list(self.evidence_ids),
            "execution_checkpoint_id": (
                self.execution_checkpoint_id
            ),
            "execution_checkpoint_fingerprint": (
                self.execution_checkpoint_fingerprint
            ),
            "recovery_nonce": self.recovery_nonce,
        }


@dataclass(frozen=True, slots=True)
class ContinuityResult:
    schema_version: str
    decision: ContinuityDecision
    reason: str

    recovery_id: str
    project_id: str

    snapshot: ContinuitySnapshot | None

    selected_evidence: tuple[
        ContinuityEvidence, ...
    ]

    missing_evidence_ids: tuple[str, ...]
    stale_evidence_ids: tuple[str, ...]
    conflicting_evidence_ids: tuple[str, ...]

    request_fingerprint: str
    recovery_fingerprint: str

    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason,
            "recovery_id": self.recovery_id,
            "project_id": self.project_id,
            "snapshot": (
                self.snapshot.to_dict()
                if self.snapshot
                else None
            ),
            "selected_evidence": [
                item.to_dict()
                for item in self.selected_evidence
            ],
            "missing_evidence_ids": list(
                self.missing_evidence_ids
            ),
            "stale_evidence_ids": list(
                self.stale_evidence_ids
            ),
            "conflicting_evidence_ids": list(
                self.conflicting_evidence_ids
            ),
            "request_fingerprint": (
                self.request_fingerprint
            ),
            "recovery_fingerprint": (
                self.recovery_fingerprint
            ),
            "explanation": self.explanation,
        }
