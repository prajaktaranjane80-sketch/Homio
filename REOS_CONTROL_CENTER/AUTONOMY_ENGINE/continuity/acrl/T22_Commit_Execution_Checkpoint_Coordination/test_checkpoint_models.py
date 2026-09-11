from .checkpoint_models import (
    CheckpointKind,
    CheckpointRequest,
)


def test_checkpoint_request_serialization():
    request = CheckpointRequest(
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
        authorization_nonce="nonce-1",
        protected_state_fingerprint="e" * 64,
    )

    data = request.to_dict()

    assert data["checkpoint_id"] == "checkpoint-1"
    assert (
        data["checkpoint_kind"]
        == "EXECUTION"
    )
