import pytest

from .continuity_policy import (
    ContinuityPolicy,
    validate_policy,
)


def test_default_policy_is_safe():
    policy = ContinuityPolicy()

    validate_policy(policy)

    assert not policy.allow_chat_history_authority
    assert not policy.allow_gpt_memory_authority
    assert not policy.allow_execution


def test_chat_history_authority_is_rejected():
    policy = ContinuityPolicy(
        allow_chat_history_authority=True
    )

    with pytest.raises(ValueError):
        validate_policy(policy)
