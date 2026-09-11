from .loop_controller import (
    advance_execution_loop,
)
from .loop_models import (
    ExecutionLoop,
    LoopDecision,
    LoopStatus,
)
from .loop_store import (
    LoopStore,
)


def make_loop():
    return ExecutionLoop(
        schema_version="1.0",
        loop_version="1.0",
        loop_id="progress",
        status=LoopStatus.RUNNING,
        execution_intent="run",
        checkpoint_id="checkpoint",
        checkpoint_fingerprint="a" * 64,
        continuity_recovery_id="recovery",
        continuity_fingerprint="b" * 64,
        evidence_resolution_id="resolution",
        evidence_fingerprint="c" * 64,
        max_iterations=5,
        max_retries_per_iteration=2,
        current_iteration=1,
        total_work_budget=10,
        total_token_budget=100,
        total_context_budget=100,
        work_consumed=1,
        token_consumed=10,
        context_consumed=10,
        no_progress_limit=1,
        no_progress_count=0,
        iterations=(
            type(
                "Iteration",
                (),
                {
                    "progress_fingerprint": "same",
                },
            )(),
        ),
        terminal_reason=None,
        loop_fingerprint="d" * 64,
    )


def test_no_progress_stops_loop():
    store = LoopStore()
    loop = make_loop()

    store.put(loop)

    result = advance_execution_loop(
        loop=loop,
        store=store,
        progress_fingerprint="same",
        work_consumed=1,
        token_consumed=1,
        context_consumed=1,
    )

    assert (
        result.decision
        is LoopDecision.NO_PROGRESS
    )
