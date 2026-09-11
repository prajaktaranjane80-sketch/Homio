from __future__ import annotations

from .repair_models import RepairPolicy


def validate_policy(policy: RepairPolicy) -> None:
    if policy.schema_version != "1.0":
        raise ValueError("Unsupported T20 schema version.")

    if policy.policy_version != "1.0":
        raise ValueError("Unsupported T20 policy version.")

    if policy.max_files <= 0:
        raise ValueError("T20 max_files must be positive.")

    if policy.max_patch_bytes <= 0:
        raise ValueError("T20 max_patch_bytes must be positive.")

    if policy.max_attempts <= 0:
        raise ValueError("T20 max_attempts must be positive.")

    if policy.allow_state_mutation:
        raise ValueError("T20 cannot mutate state.")

    if policy.allow_architecture_mutation:
        raise ValueError("T20 cannot mutate architecture.")

    if policy.allow_authorization_mutation:
        raise ValueError("T20 cannot mutate authorization.")

    if policy.allow_main_repository_mutation:
        raise ValueError("T20 cannot mutate the main repository.")
