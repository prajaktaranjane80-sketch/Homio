import pytest

from .budget_policy import (
    BudgetPolicy,
    validate_policy,
)


def test_default_policy_is_safe():
    policy = BudgetPolicy()

    validate_policy(
        policy
    )

    assert not policy.allow_limit_escalation
    assert not policy.allow_execution


def test_limit_escalation_is_forbidden():
    policy = BudgetPolicy(
        allow_limit_escalation=True
    )

    with pytest.raises(ValueError):
        validate_policy(
            policy
        )
