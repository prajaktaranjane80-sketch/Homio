from __future__ import annotations

from .budget_models import (
    BudgetRequest,
)
from .budget_policy import (
    BudgetPolicy,
)


def calculate_available(
    request: BudgetRequest,
    policy: BudgetPolicy,
) -> tuple[int, int, int]:
    context_available = (
        request.context_window.usable_capacity
        * policy.max_context_utilization_percent
        // 100
    )

    token_available = (
        request.token_capacity
        * policy.max_token_utilization_percent
        // 100
    )

    work_available = (
        request.work_capacity
        * policy.max_work_utilization_percent
        // 100
    )

    return (
        max(
            0,
            context_available
            - policy.minimum_context_reserve,
        ),
        max(
            0,
            token_available
            - policy.minimum_token_reserve,
        ),
        max(
            0,
            work_available
            - policy.minimum_work_reserve,
        ),
    )


def can_allocate(
    *,
    request: BudgetRequest,
    available: tuple[int, int, int],
    policy: BudgetPolicy,
) -> bool:
    requested = (
        request.context_requested,
        request.token_requested,
        request.work_requested,
    )

    floors = (
        request.required_context_floor,
        request.required_token_floor,
        request.required_work_floor,
    )

    for want, floor, capacity in zip(
        requested,
        floors,
        available,
    ):
        if want > capacity:
            if (
                not request.allow_partial
                and not policy.allow_partial_allocation
            ):
                return False

        if floor > capacity:
            return False

    return True


def allocate_amounts(
    *,
    request: BudgetRequest,
    available: tuple[int, int, int],
    policy: BudgetPolicy,
) -> tuple[int, int, int]:
    requested = (
        request.context_requested,
        request.token_requested,
        request.work_requested,
    )

    if can_allocate(
        request=request,
        available=available,
        policy=policy,
    ):
        return requested

    if not (
        request.allow_partial
        or policy.allow_partial_allocation
    ):
        raise ValueError(
            "Requested budget exceeds safe available budget."
        )

    result = []

    floors = (
        request.required_context_floor,
        request.required_token_floor,
        request.required_work_floor,
    )

    for want, floor, capacity in zip(
        requested,
        floors,
        available,
    ):
        if capacity < floor:
            raise ValueError(
                "Required budget floor cannot be satisfied."
            )

        result.append(
            min(
                want,
                capacity,
            )
        )

    return tuple(result)
