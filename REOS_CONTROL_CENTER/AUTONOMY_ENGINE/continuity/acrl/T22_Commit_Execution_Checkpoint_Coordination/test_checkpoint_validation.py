import pytest

from .checkpoint_models import (
    CheckpointKind,
    CheckpointRequest,
)
from .checkpoint_policy import (
    CheckpointPolicy,
)
from .checkpoint_validation import (
    validate_request,
)


def make_request():
    return CheckpointRequest(
        checkpoint_id="checkpoint-1",
        checkpoint_kind=CheckpointKind.EXECUTION,
        execution_intent="execute_verified_work",
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


def test_valid_request():
    validate_request(
        make_request(),
        CheckpointPolicy(),
    )


def test_invalid_commit_sha():
    request = make_request()

    invalid = CheckpointRequest(
        checkpoint_id=request.checkpoint_id,
        checkpoint_kind=request.checkpoint_kind,
        execution_intent=request.execution_intent,
        repository_root=request.repository_root,
        expected_branch=request.expected_branch,
        expected_commit_sha="bad",
        transaction_id=request.transaction_id,
        repair_id=request.repair_id,
        repair_fingerprint=request.repair_fingerprint,
        transaction_fingerprint=request.transaction_fingerprint,
        authorization_fingerprint=request.authorization_fingerprint,
        authorization_nonce=request.authorization_nonce,
        protected_state_fingerprint=(
            request.protected_state_fingerprint
        ),
    )

    with pytest.raises(ValueError):
        validate_request(
            invalid,
            CheckpointPolicy(),
        )
