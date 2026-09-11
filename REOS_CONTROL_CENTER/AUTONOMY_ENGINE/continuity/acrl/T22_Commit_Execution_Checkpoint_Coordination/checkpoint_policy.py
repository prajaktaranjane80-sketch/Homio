from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckpointPolicy:
    schema_version: str = "1.0"
    policy_version: str = "1.0"

    require_verified_commit: bool = True
    require_authorization: bool = True
    require_repair_evidence: bool = True
    require_transaction_identity: bool = True

    allow_replay: bool = False
    allow_state_mutation: bool = False
    allow_execution: bool = False
    allow_deployment: bool = False
    allow_release: bool = False
    allow_authority_promotion: bool = False

    protected_paths: tuple[str, ...] = (
        "data/state.json",
        "REOS_CONTROL_CENTER/data/state.json",
    )


def validate_policy(policy: CheckpointPolicy) -> None:
    if policy.allow_replay:
        raise ValueError(
            "T22 policy cannot allow replay."
        )

    if policy.allow_state_mutation:
        raise ValueError(
            "T22 cannot allow canonical state mutation."
        )

    if policy.allow_execution:
        raise ValueError(
            "T22 cannot allow execution."
        )

    if policy.allow_deployment:
        raise ValueError(
            "T22 cannot allow deployment."
        )

    if policy.allow_release:
        raise ValueError(
            "T22 cannot allow release."
        )

    if policy.allow_authority_promotion:
        raise ValueError(
            "T22 cannot promote authority."
        )


def is_protected_path(
    path: str,
    policy: CheckpointPolicy,
) -> bool:
    normalized = path.replace("\\", "/").strip("/")

    return normalized in {
        value.strip("/")
        for value in policy.protected_paths
    }
