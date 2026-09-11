import pytest

from .loop_models import (
    ExecutionLoop,
    LoopStatus,
)
from .loop_store import (
    LoopIdentityConflict,
    LoopStore,
)


def make_loop(
    fingerprint,
):
    return ExecutionLoop(
        schema_version="1.0",
        loop_version="1.0",
        loop_id="same",
        status=LoopStatus.CREATED,
        execution_intent="run",
        checkpoint_id="checkpoint",
        checkpoint_fingerprint="a" * 64,
        continuity_recovery_id="recovery",
        continuity_fingerprint="b" * 64,
        evidence_resolution_id="resolution",
        evidence_fingerprint="c" * 64,
        max_iterations=5,
        max_retries_per_iteration=2,
        current_iteration=0,
        total_work_budget=10,
        total_token_budget=100,
        total_context_budget=100,
        work_consumed=0,
        token_consumed=0,
        context_consumed=0,
        no_progress_limit=2,
        no_progress_count=0,
        iterations=(),
        terminal_reason=None,
        loop_fingerprint=fingerprint,
    )


def test_conflicting_loop_identity_is_blocked():
    store = LoopStore()

    store.put(
        make_loop(
            "a" * 64
        )
    )

    with pytest.raises(
        LoopIdentityConflict
    ):
        store.put(
            make_loop(
                "b" * 64
            )
        )
