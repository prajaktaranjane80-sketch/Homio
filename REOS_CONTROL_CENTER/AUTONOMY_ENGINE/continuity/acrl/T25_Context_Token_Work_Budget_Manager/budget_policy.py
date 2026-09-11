from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    max_context_utilization_percent: int = 80
    max_token_utilization_percent: int = 80
    max_work_utilization_percent: int = 80

    minimum_context_reserve: int = 1024
    minimum_token_reserve: int = 256
    minimum_work_reserve: int = 1

    allow_partial_allocation: bool = False

    allow_limit_escalation: bool = False
    allow_negative_budget: bool = False
    allow_over_consumption: bool = False
    allow_canonical_state_mutation: bool = False
    allow_execution: bool = False


def validate_policy(
    policy: BudgetPolicy,
) -> None:
    for value, name in (
        (
            policy.max_context_utilization_percent,
            "max_context_utilization_percent",
        ),
        (
            policy.max_token_utilization_percent,
            "max_token_utilization_percent",
        ),
        (
            policy.max_work_utilization_percent,
            "max_work_utilization_percent",
        ),
    ):
        if value <= 0 or value > 100:
            raise ValueError(
                f"{name} must be between 1 and 100."
            )

    if policy.allow_limit_escalation:
        raise ValueError(
            "T25 cannot escalate declared limits."
        )

    if policy.allow_negative_budget:
        raise ValueError(
            "T25 cannot allow negative budgets."
        )

    if policy.allow_over_consumption:
        raise ValueError(
            "T25 cannot allow over-consumption."
        )

    if policy.allow_canonical_state_mutation:
        raise ValueError(
            "T25 cannot mutate canonical state."
        )

    if policy.allow_execution:
        raise ValueError(
            "T25 cannot execute work."
        )
