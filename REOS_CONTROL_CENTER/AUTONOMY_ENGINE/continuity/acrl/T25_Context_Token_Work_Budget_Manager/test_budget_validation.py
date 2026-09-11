import pytest

from .budget_models import (
    BudgetRequest,
    ContextWindow,
)
from .budget_policy import (
    BudgetPolicy,
)
from .budget_validation import (
    validate_request,
)


def make_request():
    return BudgetRequest(
        request_id="budget-1",
        context_requested=1000,
        token_requested=2000,
        work_requested=5,
        context_window=ContextWindow(
            declared_capacity=5000,
            safety_reserve=500,
            minimum_operational_capacity=500,
        ),
        token_capacity=5000,
        work_capacity=20,
    )


def test_valid_request():
    validate_request(
        make_request(),
        BudgetPolicy(),
    )


def test_negative_budget_rejected():
    request = BudgetRequest(
        request_id="bad",
        context_requested=-1,
        token_requested=1,
        work_requested=1,
        context_window=ContextWindow(
            declared_capacity=5000,
            safety_reserve=500,
            minimum_operational_capacity=500,
        ),
        token_capacity=5000,
        work_capacity=20,
    )

    with pytest.raises(ValueError):
        validate_request(
            request,
            BudgetPolicy(),
        )
