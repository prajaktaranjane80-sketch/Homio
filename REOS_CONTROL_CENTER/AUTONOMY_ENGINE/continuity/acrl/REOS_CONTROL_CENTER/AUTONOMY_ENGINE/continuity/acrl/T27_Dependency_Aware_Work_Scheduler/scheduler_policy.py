from __future__ import annotations

from .scheduler_models import SchedulerPolicy


def validate_policy(
    policy: SchedulerPolicy,
) -> None:
    if policy.max_parallel < 1:
        raise ValueError(
            "max_parallel must be >= 1."
        )

    if not policy.version:
        raise ValueError(
            "policy version is required."
        )
