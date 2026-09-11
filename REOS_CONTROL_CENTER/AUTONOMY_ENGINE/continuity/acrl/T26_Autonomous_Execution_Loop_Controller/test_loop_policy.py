import pytest

from .loop_policy import (
    LoopPolicy,
    validate_policy,
)


def test_safe_default_policy():
    policy = LoopPolicy()

    validate_policy(
        policy
    )

    assert not policy.allow_unbounded_loop
    assert not policy.allow_execution


def test_unbounded_loop_rejected():
    with pytest.raises(ValueError):
        validate_policy(
            LoopPolicy(
                allow_unbounded_loop=True
            )
        )
