from .checkpoint_builder import (
    build_checkpoint,
)
from .checkpoint_models import (
    CheckpointKind,
    CheckpointRequest,
)


def test_checkpoint_is_bound_to_expected_commit():
    request = CheckpointRequest(
        checkpoint_id="checkpoint-1",
        checkpoint_kind=CheckpointKind.EXECUTION,
        execution_intent="run",
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

    checkpoint = build_checkpoint(
        request
    )

    assert (
        checkpoint.commit_sha
        == "a" * 40
    )

    assert (
        checkpoint.created_from_head
        == "a" * 40
    )

    assert len(
        checkpoint.checkpoint_fingerprint
    ) == 64
