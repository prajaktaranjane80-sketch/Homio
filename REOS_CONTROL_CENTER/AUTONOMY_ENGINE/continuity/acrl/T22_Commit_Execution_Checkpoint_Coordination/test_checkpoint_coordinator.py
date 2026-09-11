from dataclasses import dataclass
from enum import Enum

from .checkpoint_coordinator import (
    create_execution_checkpoint,
)
from .checkpoint_models import (
    CheckpointDecision,
    CheckpointKind,
    CheckpointRequest,
)
from .checkpoint_store import (
    CheckpointStore,
)


class AuthorizationDecision(Enum):
    AUTHORIZE = "AUTHORIZE"


@dataclass
class Authorization:
    decision: AuthorizationDecision
    execution_authorized: bool
    state_mutated: bool
    authorization_fingerprint: str


@dataclass
class GitResult:
    decision: Enum
    commit_sha: str
    branch_after: str
    transaction_fingerprint: str


@dataclass
class RepairResult:
    decision: Enum
    patch_fingerprint: str


class T20Decision(Enum):
    VERIFIED = "VERIFIED"


class T21Decision(Enum):
    COMMITTED = "COMMITTED"


def make_request():
    return CheckpointRequest(
        checkpoint_id="checkpoint-1",
        checkpoint_kind=CheckpointKind.EXECUTION,
        execution_intent="run_verified_repair",
        repository_root="repo",
        expected_branch="reos-development",
        expected_commit_sha="a" * 40,
        transaction_id="tx-1",
        repair_id="repair-1",
        repair_fingerprint="b" * 64,
        transaction_fingerprint="c" * 64,
        authorization_fingerprint="d" * 64,
        authorization_nonce="nonce",
        protected_state_fingerprint="e" * 64,
    )


def make_authorization():
    return Authorization(
        decision=AuthorizationDecision.AUTHORIZE,
        execution_authorized=True,
        state_mutated=False,
        authorization_fingerprint="d" * 64,
    )


def make_git_result():
    return GitResult(
        decision=T21Decision.COMMITTED,
        commit_sha="a" * 40,
        branch_after="reos-development",
        transaction_fingerprint="c" * 64,
    )


def make_repair_result():
    return RepairResult(
        decision=T20Decision.VERIFIED,
        patch_fingerprint="b" * 64,
    )


def test_checkpoint_creation():
    result = create_execution_checkpoint(
        request=make_request(),
        authorization=make_authorization(),
        git_result=make_git_result(),
        repair_result=make_repair_result(),
        store=CheckpointStore(),
    )

    assert (
        result.decision
        == CheckpointDecision.CHECKPOINT_CREATED
    )

    assert result.checkpoint is not None

    assert (
        result.checkpoint.commit_sha
        == "a" * 40
    )
