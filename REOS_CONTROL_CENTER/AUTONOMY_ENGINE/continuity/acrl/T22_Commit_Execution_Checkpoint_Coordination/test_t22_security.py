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
from .checkpoint_store import CheckpointStore


class Decision(Enum):
    AUTHORIZE = "AUTHORIZE"


@dataclass
class Authorization:
    decision: Decision
    execution_authorized: bool
    state_mutated: bool
    authorization_fingerprint: str


def make_request():
    return CheckpointRequest(
        checkpoint_id="checkpoint-secure",
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


def test_missing_authorization_blocks():
    result = create_execution_checkpoint(
        request=make_request(),
        authorization=None,
        git_result=None,
        repair_result=None,
        store=CheckpointStore(),
    )

    assert result.decision in {
        CheckpointDecision.BLOCKED,
        CheckpointDecision.INVALID,
    }


def test_checkpoint_never_executes():
    result = create_execution_checkpoint(
        request=make_request(),
        authorization=None,
        git_result=None,
        repair_result=None,
        store=CheckpointStore(),
    )

    assert result.checkpoint is None
