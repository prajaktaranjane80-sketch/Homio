from __future__ import annotations

from pathlib import PurePosixPath

from .git_models import GitPolicy, GitTransactionRequest
from .git_policy import (
    is_protected_path,
    normalize_path,
)


def is_safe_repository_path(
    path: str,
) -> bool:
    normalized = normalize_path(path)

    if not normalized:
        return False

    if normalized.startswith("/"):
        return False

    parts = PurePosixPath(
        normalized
    ).parts

    return (
        ".." not in parts
        and "." not in parts
    )


def validate_write_scope(
    request: GitTransactionRequest,
    policy: GitPolicy,
) -> tuple[str, ...]:
    if not request.changed_paths:
        raise ValueError(
            "T21 requires explicit changed paths."
        )

    normalized = tuple(
        sorted(
            {
                normalize_path(path)
                for path in request.changed_paths
            }
        )
    )

    for path in normalized:
        if not is_safe_repository_path(path):
            raise ValueError(
                f"Unsafe repository path: {path}"
            )

        if is_protected_path(
            path,
            policy,
        ):
            raise ValueError(
                f"Protected repository path: {path}"
            )

    return normalized
