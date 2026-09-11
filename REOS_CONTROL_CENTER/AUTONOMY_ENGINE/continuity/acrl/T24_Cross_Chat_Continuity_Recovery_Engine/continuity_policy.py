from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContinuityPolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    require_project_identity: bool = True
    require_state_identity: bool = True
    require_git_identity: bool = True
    require_current_evidence: bool = True

    allow_chat_history_authority: bool = False
    allow_gpt_memory_authority: bool = False
    allow_state_mutation: bool = False
    allow_gate_advancement: bool = False
    allow_execution: bool = False

    fail_closed_on_ambiguity: bool = True
    fail_closed_on_integrity_mismatch: bool = True

    protected_sources: tuple[str, ...] = (
        "chat_history",
        "gpt_memory",
        "manual_assumption",
    )


def validate_policy(
    policy: ContinuityPolicy,
) -> None:
    if policy.allow_chat_history_authority:
        raise ValueError(
            "Chat history cannot be an authority."
        )

    if policy.allow_gpt_memory_authority:
        raise ValueError(
            "GPT memory cannot be an authority."
        )

    if policy.allow_state_mutation:
        raise ValueError(
            "T24 cannot mutate canonical state."
        )

    if policy.allow_gate_advancement:
        raise ValueError(
            "T24 cannot advance gates."
        )

    if policy.allow_execution:
        raise ValueError(
            "T24 cannot execute work."
        )

    if not policy.fail_closed_on_ambiguity:
        raise ValueError(
            "T24 must fail closed on ambiguity."
        )

    if not policy.fail_closed_on_integrity_mismatch:
        raise ValueError(
            "T24 must fail closed on integrity mismatch."
        )
