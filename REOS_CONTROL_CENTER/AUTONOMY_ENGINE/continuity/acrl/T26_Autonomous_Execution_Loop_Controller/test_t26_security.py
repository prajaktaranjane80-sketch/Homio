import pytest

from .loop_policy import (
    LoopPolicy,
    validate_policy,
)


def test_execution_permission_is_forbidden():
    with pytest.raises(ValueError):
        validate_policy(
            LoopPolicy(
                allow_execution=True
            )
        )


def test_budget_escalation_is_forbidden():
    with pytest.raises(ValueError):
        validate_policy(
            LoopPolicy(
                allow_budget_escalation=True
            )
        )


def test_unbounded_loop_is_forbidden():
    with pytest.raises(ValueError):
        validate_policy(
            LoopPolicy(
                allow_unbounded_loop=True
            )
        )
