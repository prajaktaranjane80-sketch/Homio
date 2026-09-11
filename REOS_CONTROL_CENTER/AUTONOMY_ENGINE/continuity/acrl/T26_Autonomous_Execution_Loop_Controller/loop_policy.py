from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoopPolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    max_iterations_hard_limit: int = 1000
    max_retries_hard_limit: int = 10
    max_no_progress_hard_limit: int = 5

    require_checkpoint: bool = True
    require_continuity: bool = True
    require_evidence: bool = True
    require_budget: bool = True

    allow_unbounded_loop: bool = False
    allow_retry_escalation: bool = False
    allow_budget_escalation: bool = False
    allow_execution: bool = False
    allow_state_mutation: bool = False


def validate_policy(
    policy: LoopPolicy,
) -> None:
    if policy.max_iterations_hard_limit <= 0:
        raise ValueError(
            "Maximum iteration hard limit must be positive."
        )

    if policy.max_retries_hard_limit < 0:
        raise ValueError(
            "Maximum retry hard limit cannot be negative."
        )

    if policy.max_no_progress_hard_limit <= 0:
        raise ValueError(
            "Maximum no-progress hard limit must be positive."
        )

    if policy.allow_unbounded_loop:
        raise ValueError(
            "Unbounded execution loops are forbidden."
        )

    if policy.allow_retry_escalation:
        raise ValueError(
            "Retry escalation is forbidden."
        )

    if policy.allow_budget_escalation:
        raise ValueError(
            "Budget escalation is forbidden."
        )

    if policy.allow_execution:
        raise ValueError(
            "T26 cannot execute work."
        )

    if policy.allow_state_mutation:
        raise ValueError(
            "T26 cannot mutate canonical state."
        )
