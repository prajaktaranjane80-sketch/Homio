from dataclasses import replace

import pytest

from .loop_controller import advance_execution_loop
from .loop_identity import fingerprint
from .loop_models import ExecutionLoop, LoopStatus
from .loop_store import (
    LoopConcurrentUpdateError,
    LoopIdentityConflict,
    LoopReplayError,
    LoopStore,
)


def make_loop(
    loop_fingerprint: str,
    *,
    status: LoopStatus = LoopStatus.CREATED,
) -> ExecutionLoop:
    return ExecutionLoop(
        schema_version="1.0",
        loop_version="1.0",
        loop_id="same",
        status=status,
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
        loop_fingerprint=loop_fingerprint,
    )


def test_conflicting_loop_identity_is_blocked():
    store = LoopStore()

    store.put(make_loop("a" * 64))

    with pytest.raises(LoopIdentityConflict):
        store.put(make_loop("b" * 64))


def test_duplicate_loop_is_rejected():
    store = LoopStore()
    loop = make_loop("d" * 64)

    store.put(loop)

    with pytest.raises(LoopReplayError):
        store.put(loop)


def test_stale_concurrent_iteration_cannot_overwrite_winner():
    store = LoopStore()
    initial = make_loop(
        fingerprint({"initial": "state"}),
        status=LoopStatus.RUNNING,
    )
    store.put(initial)

    first = advance_execution_loop(
        loop=initial,
        store=store,
        progress_fingerprint="progress-from-worker-one",
        work_consumed=1,
        token_consumed=10,
        context_consumed=5,
    )

    assert first.loop is not None
    assert first.loop.current_iteration == 1

    winning_state = store.get(initial.loop_id)
    assert winning_state == first.loop

    # Simulate another worker attempting to advance the same stale
    # iteration-0 snapshot with a different result.
    with pytest.raises(LoopConcurrentUpdateError):
        advance_execution_loop(
            loop=initial,
            store=store,
            progress_fingerprint="different-progress-from-worker-two",
            work_consumed=2,
            token_consumed=20,
            context_consumed=10,
        )

    # The rejected worker must not overwrite the first worker's state.
    assert store.get(initial.loop_id) == winning_state
    assert (
        store.get(initial.loop_id).iterations[-1].progress_fingerprint
        == "progress-from-worker-one"
    )


def test_budget_exhaustion_transition_does_not_require_a_new_iteration():
    store = LoopStore()
    initial = make_loop(
        "a" * 64,
        status=LoopStatus.RUNNING,
    )
    store.put(initial)

    exhausted = replace(
        initial,
        status=LoopStatus.EXHAUSTED,
        terminal_reason="BUDGET_EXHAUSTED",
        loop_fingerprint="e" * 64,
    )

    store.update(exhausted)

    assert store.get(initial.loop_id) == exhausted
    assert store.get(initial.loop_id).status is LoopStatus.EXHAUSTED


def test_immutable_budget_cannot_change_during_update():
    store = LoopStore()
    initial = make_loop(
        "a" * 64,
        status=LoopStatus.RUNNING,
    )
    store.put(initial)

    altered = replace(
        initial,
        total_work_budget=initial.total_work_budget + 100,
        loop_fingerprint="f" * 64,
    )

    with pytest.raises(LoopIdentityConflict):
        store.update(altered)

    assert store.get(initial.loop_id) == initial
