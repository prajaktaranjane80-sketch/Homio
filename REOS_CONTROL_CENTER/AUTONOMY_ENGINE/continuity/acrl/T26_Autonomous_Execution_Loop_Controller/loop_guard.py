from __future__ import annotations

from .loop_models import (
    ExecutionLoop,
    LoopDecision,
    LoopStatus,
)


def evaluate_loop_guard(
    loop: ExecutionLoop,
) -> tuple[
    LoopDecision,
    str,
]:
    if loop.status in {
        LoopStatus.STOPPED,
        LoopStatus.FAILED,
        LoopStatus.COMPLETED,
        LoopStatus.EXHAUSTED,
    }:
        return (
            LoopDecision.STOPPED,
            "Loop is already terminal.",
        )

    if (
        loop.current_iteration
        >= loop.max_iterations
    ):
        return (
            LoopDecision.STOPPED,
            "Maximum iteration limit reached.",
        )

    if (
        loop.no_progress_count
        >= loop.no_progress_limit
    ):
        return (
            LoopDecision.NO_PROGRESS,
            "No-progress safety limit reached.",
        )

    if (
        loop.work_consumed
        >= loop.total_work_budget
        or loop.token_consumed
        >= loop.total_token_budget
        or loop.context_consumed
        >= loop.total_context_budget
    ):
        return (
            LoopDecision.BUDGET_EXHAUSTED,
            "Loop resource budget exhausted.",
        )

    return (
        LoopDecision.CONTINUE,
        "Loop may continue.",
    )
