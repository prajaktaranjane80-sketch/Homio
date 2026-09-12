import pytest

from .decision_models import DecisionPolicy
from .decision_policy import validate_policy


def test_policy_valid():
    validate_policy(DecisionPolicy())


def test_policy_requires_version():
    with pytest.raises(ValueError):
        validate_policy(
            DecisionPolicy(policy_version="")
        )
