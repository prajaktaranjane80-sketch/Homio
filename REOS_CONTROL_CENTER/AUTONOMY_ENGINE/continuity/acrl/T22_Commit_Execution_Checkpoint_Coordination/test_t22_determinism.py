from .checkpoint_builder import (
    build_checkpoint,
)
from .checkpoint_models import (
    CheckpointKind,
    CheckpointRequest,
)


def make_request():
    return CheckpointRequest(
        checkpoint_id="deterministic",
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


def test_checkpoint_fingerprint_is_stable():
    first = build_checkpoint(
        make_request()
    )

    second = build_checkpoint(
        make_request()
    )

    assert (
        first.checkpoint_fingerprint
        == second.checkpoint_fingerprint
    )
