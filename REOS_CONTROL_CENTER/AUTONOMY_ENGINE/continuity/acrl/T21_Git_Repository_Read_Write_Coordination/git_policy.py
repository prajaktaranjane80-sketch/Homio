from __future__ import annotations

from .git_models import GitPolicy


def normalize_path(value: str) -> str:
    """Normalize separators without changing case-sensitive path identity."""
    normalized = value.replace("\\", "/").strip()

    while normalized.startswith("./"):
        normalized = normalized[2:]

    return normalized.rstrip("/")


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

    if not normalized:
        return False

    protected_paths = {
        normalize_path(item)
        for item in policy.protected_paths
    }

    # Protect each declared path and all descendants.
    for protected in protected_paths:
        if normalized == protected:
            return True

        if normalized.startswith(protected + "/"):
            return True

    # T21 contract forbids architecture mutations.
    architecture_roots = (
        "architecture",
        "REOS_CONTROL_CENTER/architecture",
    )

    for root in architecture_roots:
        if (
            normalized == root
            or normalized.startswith(root + "/")
        ):
            return True

    return False
