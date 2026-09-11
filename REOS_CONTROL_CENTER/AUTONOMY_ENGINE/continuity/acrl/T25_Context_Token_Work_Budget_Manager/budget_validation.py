from __future__ import annotations

from .budget_models import (
    BudgetRequest,
)
from .budget_policy import (
    BudgetPolicy,
    validate_policy,
)


def _non_negative(
    value: int,
    name: str,
) -> None:
    if not isinstance(
        value,
        int,
    ):
        raise ValueError(
            f"{name} must be an integer."
        )

    if value < 0:
        raise ValueError(
            f"{name} cannot be negative."
        )


def validate_request(
    request: BudgetRequest,
    policy: BudgetPolicy,
) -> None:
    validate_policy(
        policy
    )

    if not request.request_id.strip():
        raise ValueError(
            "request_id is required."
        )

    for value, name in (
        (
            request.context_requested,
            "context_requested",
        ),
        (
            request.token_requested,
            "token_requested",
        ),
        (
            request.work_requested,
            "work_requested",
        ),
        (
            request.context_window.declared_capacity,
            "context_capacity",
        ),
        (
            request.context_window.safety_reserve,
            "safety_reserve",
        ),
        (
            request.context_window.compression_reserve,
            "compression_reserve",
        ),
        (
            request.context_window.minimum_operational_capacity,
            "minimum_operational_capacity",
        ),
        (
            request.token_capacity,
            "token_capacity",
        ),
        (
            request.work_capacity,
            "work_capacity",
        ),
        (
            request.required_context_floor,
            "required_context_floor",
        ),
        (
            request.required_token_floor,
            "required_token_floor",
        ),
        (
            request.required_work_floor,
            "required_work_floor",
        ),
    ):
        _non_negative(
            value,
            name,
        )

    if (
        request.context_window.safety_reserve
        >= request.context_window.declared_capacity
        and request.context_window.declared_capacity
        > 0
    ):
        raise ValueError(
            "Context safety reserve consumes all capacity."
        )

    if (
        request.context_window.minimum_operational_capacity
        > request.context_window.usable_capacity
    ):
        raise ValueError(
            "Minimum operational context exceeds usable capacity."
        )

    if (
        request.required_context_floor
        > request.context_requested
    ):
        raise ValueError(
            "Required context floor exceeds requested context."
        )

    if (
        request.required_token_floor
        > request.token_requested
    ):
        raise ValueError(
            "Required token floor exceeds requested tokens."
        )

    if (
        request.required_work_floor
        > request.work_requested
    ):
        raise ValueError(
            "Required work floor exceeds requested work."
        )
