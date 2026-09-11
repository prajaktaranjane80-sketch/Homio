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


class AuthDecision(Enum):
    AUTHORIZE = "AUTHORIZE"


class GitDecision(Enum):
    COMMITTED = "COMMITTED"


class RepairDecision(Enum):
    VERIFIED = "VERIFIED"


@dataclass
class Authorization:
    decision: AuthDecision
    execution_authorized: bool
    state_mutated: bool
    authorization_fingerprint: str


@dataclass
class GitResult:
    decision: GitDecision
    commit_sha: str
    branch_after: str
    transaction_fingerprint: str


@dataclass
class RepairResult:
    decision: RepairDecision
    patch_fingerprint: str


def test_replay_is_detected():
    request = CheckpointRequest(
        checkpoint_id="same",
        checkpoint_kind=CheckpointKind.EXECUTION,
        execution_intent="run",
        repository_root="repo",
        expected_branch="reos-development",
        expected_commit_sha="a" * 40,
        transaction_id="tx",
        repair_id="repair",
        repair_fingerprint="b" * 64,
        transaction_fingerprint="c" * 64,
        authorization_fingerprint="d" * 64,
        authorization_nonce="nonce",
        protected_state_fingerprint="e" * 64,
    )

    authorization = Authorization(
        decision=AuthDecision.AUTHORIZE,
        execution_authorized=True,
        state_mutated=False,
        authorization_fingerprint="d" * 64,
    )

    git_result = GitResult(
        decision=GitDecision.COMMITTED,
        commit_sha="a" * 40,
        branch_after="reos-development",
        transaction_fingerprint="c" * 64,
    )

    repair_result = RepairResult(
        decision=RepairDecision.VERIFIED,
        patch_fingerprint="b" * 64,
    )

    store = CheckpointStore()

    first = create_execution_checkpoint(
        request=request,
        authorization=authorization,
        git_result=git_result,
        repair_result=repair_result,
        store=store,
    )

    second = create_execution_checkpoint(
        request=request,
        authorization=authorization,
        git_result=git_result,
        repair_result=repair_result,
        store=store,
    )

    assert (
        first.decision
        == CheckpointDecision.CHECKPOINT_CREATED
    )

    assert (
        second.decision
        == CheckpointDecision.REPLAY_DETECTED
    )

    assert second.replay is True
