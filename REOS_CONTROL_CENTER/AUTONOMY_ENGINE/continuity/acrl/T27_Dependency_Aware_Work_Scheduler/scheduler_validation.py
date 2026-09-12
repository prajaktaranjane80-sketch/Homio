from __future__ import annotations

from .scheduler_models import SchedulerRequest


def validate_request(
    request: SchedulerRequest,
) -> None:
    if not request.scheduler_id:
        raise ValueError(
            "scheduler_id is required."
        )

    if not request.loop_id:
        raise ValueError(
            "loop_id is required."
        )

    if not request.loop_fingerprint:
        raise ValueError(
            "loop_fingerprint is required."
        )

    if request.work_budget < 0:
        raise ValueError(
            "work_budget cannot be negative."
        )

    if request.token_budget < 0:
        raise ValueError(
            "token_budget cannot be negative."
        )

    if request.context_budget < 0:
        raise ValueError(
            "context_budget cannot be negative."
        )

    request.policy and None

    seen: set[str] = set()

    for item in request.work_units:
        if not item.work_id:
            raise ValueError(
                "work_id is required."
            )

        if item.work_id in seen:
            raise ValueError(
                "duplicate work_id."
            )

        seen.add(item.work_id)

        if item.work_cost < 0:
            raise ValueError(
                "work_cost cannot be negative."
            )

        if item.token_cost < 0:
            raise ValueError(
                "token_cost cannot be negative."
            )

        if item.context_cost < 0:
            raise ValueError(
                "context_cost cannot be negative."
            )

        if item.priority < 0:
            raise ValueError(
                "priority cannot be negative."
            )
