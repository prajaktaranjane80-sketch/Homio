from __future__ import annotations

from .git_models import GitPolicy


def normalize_path(value: str) -> str:
    """Normalize separators without changing path case."""
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

    key = normalized.casefold()

    protected_paths = {
        normalize_path(item).casefold()
        for item in policy.protected_paths
    }

    for protected in protected_paths:
        if key == protected:
            return True

        if key.startswith(protected + "/"):
            return True

    # Architecture is controlled by its own governance boundary.
    architecture_roots = (
        "architecture",
        "reos_control_center/architecture",
    )

    for root in architecture_roots:
        if key == root or key.startswith(root + "/"):
            return True

    # T18's authorization source must not be changed through T21 repair writes.
    authorization_roots = (
        "autonomy_engine/continuity/acrl/"
        "t18_safe_execution_authorization_guard",
        "reos_control_center/autonomy_engine/continuity/acrl/"
        "t18_safe_execution_authorization_guard",
    )

    for root in authorization_roots:
        if key == root or key.startswith(root + "/"):
            return True

    return False
