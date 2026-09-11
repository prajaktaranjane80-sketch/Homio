from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class GitDecision(str, Enum):
    READ_ONLY = "READ_ONLY"
    READY_TO_WRITE = "READY_TO_WRITE"
    COMMITTED = "COMMITTED"
    PUSHED = "PUSHED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    FAIL_CLOSED = "FAIL_CLOSED"


class GitOperation(str, Enum):
    READ = "READ"
    CREATE_BRANCH = "CREATE_BRANCH"
    STAGE = "STAGE"
    COMMIT = "COMMIT"
    PUSH = "PUSH"


class GitReason(str, Enum):
    VALID = "VALID"
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    NOT_A_GIT_REPOSITORY = "NOT_A_GIT_REPOSITORY"
    GIT_UNAVAILABLE = "GIT_UNAVAILABLE"
    DIRTY_WORKTREE = "DIRTY_WORKTREE"
    BASELINE_DRIFT = "BASELINE_DRIFT"
    BRANCH_MISMATCH = "BRANCH_MISMATCH"
    HEAD_MISMATCH = "HEAD_MISMATCH"
    UNEXPECTED_CHANGE = "UNEXPECTED_CHANGE"
    UNAUTHORIZED_PATH = "UNAUTHORIZED_PATH"
    PROTECTED_PATH = "PROTECTED_PATH"
    STAGE_MISMATCH = "STAGE_MISMATCH"
    EMPTY_COMMIT = "EMPTY_COMMIT"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    AUTHORIZATION_INVALID = "AUTHORIZATION_INVALID"
    REPAIR_NOT_VERIFIED = "REPAIR_NOT_VERIFIED"
    COMMIT_FAILURE = "COMMIT_FAILURE"
    COMMIT_VERIFICATION_FAILURE = "COMMIT_VERIFICATION_FAILURE"
    REMOTE_UNAVAILABLE = "REMOTE_UNAVAILABLE"
    PUSH_REJECTED = "PUSH_REJECTED"
    NON_FAST_FORWARD = "NON_FAST_FORWARD"
    FORCE_PUSH_BLOCKED = "FORCE_PUSH_BLOCKED"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    CONCURRENT_TRANSACTION = "CONCURRENT_TRANSACTION"


@dataclass(frozen=True, slots=True)
class GitPolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    allow_branch_creation: bool = True
    allow_staging: bool = True
    allow_commit: bool = True
    allow_push: bool = True

    allow_force_push: bool = False
    allow_history_rewrite: bool = False
    allow_hard_reset: bool = False
    allow_clean: bool = False

    protected_paths: tuple[str, ...] = (
        ".git",
        ".gitignore",
        ".gitmodules",
        "data/state.json",
        "REOS_CONTROL_CENTER/data/state.json",
    )


@dataclass(frozen=True, slots=True)
class GitRepositorySnapshot:
    repository_root: str
    branch: str
    head_sha: str
    status_porcelain: str
    working_tree_clean: bool
    remote_names: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository_root": self.repository_root,
            "branch": self.branch,
            "head_sha": self.head_sha,
            "status_porcelain": self.status_porcelain,
            "working_tree_clean": self.working_tree_clean,
            "remote_names": list(self.remote_names),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class GitTransactionRequest:
    operation: GitOperation
    repository_root: str

    expected_branch: str
    expected_head_sha: str

    transaction_id: str
    repair_id: str
    repair_fingerprint: str

    changed_paths: tuple[str, ...]

    commit_message: str = ""
    target_branch: str | None = None

    remote_name: str | None = None
    push: bool = False

    authorization_fingerprint: str = ""
    authorization_nonce: str = ""


@dataclass(frozen=True, slots=True)
class GitTransactionResult:
    schema_version: str
    decision: GitDecision
    reason: GitReason
    operation: GitOperation

    transaction_id: str
    repair_id: str
    repair_fingerprint: str

    repository_root: str
    branch_before: str
    branch_after: str

    head_before: str
    head_after: str

    changed_paths: tuple[str, ...]
    staged_paths: tuple[str, ...]

    commit_sha: str | None
    remote_name: str | None
    push_performed: bool
    push_verified: bool

    before_fingerprint: str
    after_fingerprint: str
    transaction_fingerprint: str

    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "operation": self.operation.value,
            "transaction_id": self.transaction_id,
            "repair_id": self.repair_id,
            "repair_fingerprint": self.repair_fingerprint,
            "repository_root": self.repository_root,
            "branch_before": self.branch_before,
            "branch_after": self.branch_after,
            "head_before": self.head_before,
            "head_after": self.head_after,
            "changed_paths": list(self.changed_paths),
            "staged_paths": list(self.staged_paths),
            "commit_sha": self.commit_sha,
            "remote_name": self.remote_name,
            "push_performed": self.push_performed,
            "push_verified": self.push_verified,
            "before_fingerprint": self.before_fingerprint,
            "after_fingerprint": self.after_fingerprint,
            "transaction_fingerprint": self.transaction_fingerprint,
            "explanation": self.explanation,
        }
