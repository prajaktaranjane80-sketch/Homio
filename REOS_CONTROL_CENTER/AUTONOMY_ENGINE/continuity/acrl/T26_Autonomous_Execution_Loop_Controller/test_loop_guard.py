from dataclasses import replace

from .loop_guard import (
    evaluate_loop_guard,
)
from .loop_models import (
    ExecutionLoop,
    LoopDecision,
    LoopStatus,
)


def make_loop():
    return ExecutionLoop(
        schema_version="1.0",
        loop_version="1.0",
        loop_id="loop",
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
        no_progress_limit=2,
        no_progress_count=0,
        iterations=(),
        terminal_reason=None,
        loop_fingerprint="d" * 64,
    )


def test_continue():
    decision, _ = evaluate_loop_guard(
        make_loop()
    )

    assert (
        decision
        is LoopDecision.CONTINUE
    )


def test_no_progress_guard():
    loop = replace(
        make_loop(),
        no_progress_count=2,
    )

    decision, _ = evaluate_loop_guard(
        loop
    )

    assert (
        decision
        is LoopDecision.NO_PROGRESS
    )
