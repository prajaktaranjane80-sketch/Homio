from __future__ import annotations

from .git_models import GitPolicy


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def validate_policy(policy: GitPolicy) -> None:
    if policy.schema_version != "1.0":
        raise ValueError(
            "Unsupported T21 schema version."
        )

    if policy.policy_version != "1.0":
        raise ValueError(
            "Unsupported T21 policy version."
        )

    if policy.allow_force_push:
        raise ValueError(
            "T21 V1 forbids force push."
        )

    if policy.allow_history_rewrite:
        raise ValueError(
            "T21 V1 forbids history rewrite."
        )

    if policy.allow_hard_reset:
        raise ValueError(
            "T21 V1 forbids hard reset."
        )

    if policy.allow_clean:
        raise ValueError(
            "T21 V1 forbids git clean."
        )


def is_protected_path(
    path: str,
    policy: GitPolicy,
) -> bool:
    normalized = normalize_path(path)

    return normalized in {
        normalize_path(item)
        for item in policy.protected_paths
    }
