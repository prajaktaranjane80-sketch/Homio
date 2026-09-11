import pytest

from .checkpoint_policy import (
    CheckpointPolicy,
    is_protected_path,
    validate_policy,
)


def test_default_policy_is_safe():
    policy = CheckpointPolicy()

    validate_policy(policy)

    assert not policy.allow_execution
    assert not policy.allow_deployment
    assert not policy.allow_release
    assert not policy.allow_state_mutation


def test_execution_policy_cannot_be_enabled():
    policy = CheckpointPolicy(
        allow_execution=True
    )

    with pytest.raises(ValueError):
        validate_policy(policy)


def test_protected_state_path():
    policy = CheckpointPolicy()

    assert is_protected_path(
        "REOS_CONTROL_CENTER/data/state.json",
        policy,
    )
