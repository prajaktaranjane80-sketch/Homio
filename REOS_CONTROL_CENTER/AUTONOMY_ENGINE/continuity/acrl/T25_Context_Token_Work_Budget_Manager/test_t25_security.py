import pytest

from .budget_models import (
    BudgetRequest,
    ContextWindow,
)
from .budget_policy import (
    BudgetPolicy,
    validate_policy,
)
from .budget_validation import (
    validate_request,
)


def test_execution_permission_cannot_be_enabled():
    with pytest.raises(ValueError):
        validate_policy(
            BudgetPolicy(
                allow_execution=True
            )
        )


def test_limit_escalation_cannot_be_enabled():
    with pytest.raises(ValueError):
        validate_policy(
            BudgetPolicy(
                allow_limit_escalation=True
            )
        )


def test_zero_capacities_remain_zero():
    request = BudgetRequest(
        request_id="zero",
        context_requested=0,
        token_requested=0,
        work_requested=0,
        context_window=ContextWindow(
            declared_capacity=0,
            safety_reserve=0,
            minimum_operational_capacity=0,
        ),
        token_capacity=0,
        work_capacity=0,
    )

    validate_request(
        request,
        BudgetPolicy(),
    )
