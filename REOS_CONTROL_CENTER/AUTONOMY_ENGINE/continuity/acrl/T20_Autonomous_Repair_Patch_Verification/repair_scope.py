from __future__ import annotations

import posixpath
import re

from .repair_models import RepairPolicy, RepairRequest
from .repair_policy import validate_policy


PROTECTED_PATHS = {
    "data/state.json",
    "reos_control_center/data/state.json",
}


def normalize_path(value: str) -> str:
    if not isinstance(value, str):
        return ""

    return posixpath.normpath(
        value.replace("\\", "/")
    )


def is_safe_relative_path(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False

    if value != value.strip():
        return False

    if any(
        ord(character) < 32 or ord(character) == 127
        for character in value
    ):
        return False

    raw = value.replace("\\", "/")

    if raw.startswith("/"):
        return False

    if re.match(r"^[A-Za-z]:", raw):
        return False

    parts = raw.split("/")

    if any(part in {"", ".", ".."} for part in parts):
        return False

    normalized = posixpath.normpath(raw)

    if normalized in {"", ".", ".."}:
        return False

    if normalized.startswith("../"):
        return False

    return True


def patch_paths(patch: str) -> tuple[str, ...]:
    paths: set[str] = set()

    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            paths.add(
                normalize_path(line[6:])
            )

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

    paths = patch_paths(
        request.candidate_patch
    )

    if len(paths) > policy.max_files:
        raise ValueError(
            "Repair patch exceeds file-count limit."
        )

    for path in paths:
        if not is_safe_relative_path(path):
            raise ValueError(
                f"Unsafe repair path: {path}"
            )

        if path.casefold() in PROTECTED_PATHS:
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
