from .budget_calculator import (
    allocate_amounts,
    calculate_available,
)
from .budget_models import (
    BudgetRequest,
    ContextWindow,
)
from .budget_policy import (
    BudgetPolicy,
)


def make_request(
    *,
    allow_partial=False,
):
    return BudgetRequest(
        request_id="q",
        context_requested=2000,
        token_requested=3000,
        work_requested=10,
        context_window=ContextWindow(
            declared_capacity=10000,
            safety_reserve=1000,
            minimum_operational_capacity=1000,
        ),
        token_capacity=10000,
        work_capacity=20,
        allow_partial=allow_partial,
    )


def test_available_budget_is_bounded():
    request = make_request()

    available = calculate_available(
        request,
        BudgetPolicy(),
    )

    assert available[0] <= 10000
    assert available[1] <= 10000
    assert available[2] <= 20


def test_requested_budget_can_be_allocated():
    request = make_request()

    available = calculate_available(
        request,
        BudgetPolicy(),
    )

    amounts = allocate_amounts(
        request=request,
        available=available,
        policy=BudgetPolicy(),
    )

    assert amounts == (
        2000,
        3000,
        10,
    )
