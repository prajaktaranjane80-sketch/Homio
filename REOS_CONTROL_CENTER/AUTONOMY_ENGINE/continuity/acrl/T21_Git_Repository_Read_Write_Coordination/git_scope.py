from __future__ import annotations

import re

from .git_models import GitPolicy, GitTransactionRequest
from .git_policy import (
    is_protected_path,
    normalize_path,
)


def is_safe_repository_path(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False

    if path != path.strip():
        return False

    if any(
        ord(character) < 32 or ord(character) == 127
        for character in path
    ):
        return False

    raw = path.replace("\\", "/")

    if raw.startswith("/"):
        return False

    if re.match(r"^[A-Za-z]:", raw):
        return False

    parts = raw.split("/")

    if any(part in {"", ".", ".."} for part in parts):
        return False

    return True


def validate_write_scope(
    request: GitTransactionRequest,
    policy: GitPolicy,
) -> tuple[str, ...]:
    if not request.changed_paths:
        raise ValueError(
            "T21 requires explicit changed paths."
        )

    for raw_path in request.changed_paths:
        if not is_safe_repository_path(raw_path):
            raise ValueError(
                f"Unsafe repository path: {raw_path}"
            )

    normalized_list = [
        normalize_path(path)
        for path in request.changed_paths
    ]

    if any(not path for path in normalized_list):
        raise ValueError(
            "T21 path normalization produced an empty path."
        )

    if len(set(normalized_list)) != len(normalized_list):
        raise ValueError(
            "Duplicate paths are not allowed in T21 write scope."
        )

    normalized = tuple(sorted(normalized_list))

    for path in normalized:
        if is_protected_path(path, policy):
            raise ValueError(
                f"Protected repository path: {path}"
            )

    return normalized
