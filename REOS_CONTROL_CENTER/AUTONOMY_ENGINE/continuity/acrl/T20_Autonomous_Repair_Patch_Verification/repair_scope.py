from __future__ import annotations

import posixpath
from pathlib import PurePosixPath

from .repair_models import RepairPolicy, RepairRequest
from .repair_policy import validate_policy


PROTECTED_PATHS = {
    "data/state.json",
    "REOS_CONTROL_CENTER/data/state.json",
}


def normalize_path(value: str) -> str:
    value = value.replace("\\", "/").strip()
    value = posixpath.normpath(value)

    while value.startswith("./"):
        value = value[2:]

    return value.lower()


def is_safe_relative_path(value: str) -> bool:
    normalized = normalize_path(value)

    if normalized in {"", ".", ".."}:
        return False

    path = PurePosixPath(normalized)

    if path.is_absolute():
        return False

    return ".." not in path.parts


def patch_paths(patch: str) -> tuple[str, ...]:
    paths: set[str] = set()

    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            paths.add(normalize_path(line[6:]))

        elif line.startswith("--- a/"):
            path = normalize_path(line[6:])
            if path != "/dev/null":
                paths.add(path)

    return tuple(sorted(paths))


def validate_scope(
    request: RepairRequest,
    policy: RepairPolicy,
) -> tuple[str, ...]:
    validate_policy(policy)

    allowed = {
        normalize_path(path)
        for path in request.allowed_paths
    }

    forbidden = {
        normalize_path(path)
        for path in request.forbidden_paths
    }

    paths = patch_paths(request.candidate_patch)

    if len(paths) > policy.max_files:
        raise ValueError("Repair patch exceeds file-count limit.")

    for path in paths:
        if not is_safe_relative_path(path):
            raise ValueError(
                f"Unsafe repair path: {path}"
            )

        if path in PROTECTED_PATHS:
            raise ValueError(
                f"Protected path cannot be repaired: {path}"
            )

        if path in forbidden:
            raise ValueError(
                f"Forbidden repair path: {path}"
            )

        if path not in allowed:
            raise ValueError(
                f"Repair scope escape: {path}"
            )

    return paths
