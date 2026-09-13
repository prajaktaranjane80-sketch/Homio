import pytest

from .reconciliation_models import ReconciliationPolicy
from .reconciliation_policy import validate_policy


def test_policy_valid():
    validate_policy(ReconciliationPolicy())


def test_policy_requires_version():
    with pytest.raises(ValueError):
        validate_policy(ReconciliationPolicy(policy_version=""))
