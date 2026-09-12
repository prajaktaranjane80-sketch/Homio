import pytest

from .scheduler_models import SchedulerPolicy
from .scheduler_policy import validate_policy


def test_valid_policy():
    validate_policy(
        SchedulerPolicy()
    )


def test_invalid_parallel_limit():
    with pytest.raises(ValueError):
        validate_policy(
            SchedulerPolicy(
                max_parallel=0
            )
        )
