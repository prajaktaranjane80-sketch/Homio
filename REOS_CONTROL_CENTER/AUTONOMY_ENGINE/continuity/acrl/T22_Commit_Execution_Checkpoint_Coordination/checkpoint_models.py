from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CheckpointKind(str, Enum):
    EXECUTION = "EXECUTION"
    DEPLOYMENT = "DEPLOYMENT"
    RELEASE = "RELEASE"


class CheckpointDecision(str, Enum):
    CHECKPOINT_CREATED = "CHECKPOINT_CREATED"
    READ_ONLY = "READ_ONLY"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    FAIL_CLOSED = "FAIL_CLOSED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class ExecutionCheckpoint:
    schema_version: str
    checkpoint_version: str
    checkpoint_id: str

    kind: CheckpointKind
    execution_intent: str

    transaction_id: str
    repair_id: str

    repository_root: str
    branch: str
    commit_sha: str

    authorization_fingerprint: str
    authorization_nonce: str
    repair_fingerprint: str
    transaction_fingerprint: str

    expected_branch: str
    expected_commit_sha: str

    created_from_head: str
    protected_state_fingerprint: str

    checkpoint_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_version": self.checkpoint_version,
            "checkpoint_id": self.checkpoint_id,
            "kind": self.kind.value,
            "execution_intent": self.execution_intent,
            "transaction_id": self.transaction_id,
            "repair_id": self.repair_id,
            "repository_root": self.repository_root,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "authorization_fingerprint": self.authorization_fingerprint,
            "authorization_nonce": self.authorization_nonce,
            "repair_fingerprint": self.repair_fingerprint,
            "transaction_fingerprint": self.transaction_fingerprint,
            "expected_branch": self.expected_branch,
            "expected_commit_sha": self.expected_commit_sha,
            "created_from_head": self.created_from_head,
            "protected_state_fingerprint": self.protected_state_fingerprint,
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class CheckpointRequest:
    checkpoint_id: str
    checkpoint_kind: CheckpointKind

    execution_intent: str

    repository_root: str
    expected_branch: str
    expected_commit_sha: str

    transaction_id: str
    repair_id: str
    repair_fingerprint: str
    transaction_fingerprint: str

    authorization_fingerprint: str
    authorization_nonce: str

    protected_state_fingerprint: str

    allow_replay: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_kind": self.checkpoint_kind.value,
            "execution_intent": self.execution_intent,
            "repository_root": self.repository_root,
            "expected_branch": self.expected_branch,
            "expected_commit_sha": self.expected_commit_sha,
            "transaction_id": self.transaction_id,
            "repair_id": self.repair_id,
            "repair_fingerprint": self.repair_fingerprint,
            "transaction_fingerprint": self.transaction_fingerprint,
            "authorization_fingerprint": self.authorization_fingerprint,
            "authorization_nonce": self.authorization_nonce,
            "protected_state_fingerprint": self.protected_state_fingerprint,
            "allow_replay": self.allow_replay,
        }


@dataclass(frozen=True, slots=True)
class CheckpointResult:
    schema_version: str
    decision: CheckpointDecision
    reason: str

    checkpoint: ExecutionCheckpoint | None

    checkpoint_fingerprint: str
    request_fingerprint: str

    replay: bool

    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason,
            "checkpoint": (
                self.checkpoint.to_dict()
                if self.checkpoint is not None
                else None
            ),
            "checkpoint_fingerprint": self.checkpoint_fingerprint,
            "request_fingerprint": self.request_fingerprint,
            "replay": self.replay,
            "explanation": self.explanation,
        }
