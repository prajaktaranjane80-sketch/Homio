import pytest

from .checkpoint_builder import (
    build_checkpoint,
)
from .checkpoint_models import (
    CheckpointKind,
    CheckpointRequest,
)
from .checkpoint_store import (
    CheckpointReplayError,
    CheckpointStore,
)


def make_checkpoint():
    return build_checkpoint(
        CheckpointRequest(
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
    )


def test_store_accepts_first_checkpoint():
    store = CheckpointStore()

    checkpoint = make_checkpoint()

    store.put(checkpoint)

    assert store.contains(
        "checkpoint-1"
    )


def test_duplicate_checkpoint_is_rejected():
    store = CheckpointStore()

    checkpoint = make_checkpoint()

    store.put(checkpoint)

    with pytest.raises(
        CheckpointReplayError
    ):
        store.put(checkpoint)
