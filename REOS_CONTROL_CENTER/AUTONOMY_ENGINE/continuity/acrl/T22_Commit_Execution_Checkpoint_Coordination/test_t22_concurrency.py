from .checkpoint_builder import (
    build_checkpoint,
)
from .checkpoint_models import (
    CheckpointKind,
    CheckpointRequest,
)
from .checkpoint_store import (
    CheckpointConcurrencyError,
    CheckpointStore,
)


def make_checkpoint(checkpoint_id):
    return build_checkpoint(
        CheckpointRequest(
            checkpoint_id=checkpoint_id,
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
    )


def test_checkpoint_id_collision_is_blocked():
    store = CheckpointStore()

    first = make_checkpoint(
        "same-id"
    )

    second = make_checkpoint(
        "same-id"
    )

    store.put(first)

    second = second.__class__(
        schema_version=second.schema_version,
        checkpoint_version=second.checkpoint_version,
        checkpoint_id=second.checkpoint_id,
        kind=second.kind,
        execution_intent="different",
        transaction_id=second.transaction_id,
        repair_id=second.repair_id,
        repository_root=second.repository_root,
        branch=second.branch,
        commit_sha=second.commit_sha,
        authorization_fingerprint=(
            second.authorization_fingerprint
        ),
        authorization_nonce=(
            second.authorization_nonce
        ),
        repair_fingerprint=(
            second.repair_fingerprint
        ),
        transaction_fingerprint=(
            second.transaction_fingerprint
        ),
        expected_branch=second.expected_branch,
        expected_commit_sha=(
            second.expected_commit_sha
        ),
        created_from_head=(
            second.created_from_head
        ),
        protected_state_fingerprint=(
            second.protected_state_fingerprint
        ),
        checkpoint_fingerprint="f" * 64,
    )

    try:
        store.put(second)
        assert False
    except CheckpointConcurrencyError:
        assert True
