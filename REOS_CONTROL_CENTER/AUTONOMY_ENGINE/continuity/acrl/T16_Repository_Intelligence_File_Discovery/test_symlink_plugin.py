"""ACRL T16 — Windows symlink capability test support.

This module is independent from repository_intelligence.py.
It verifies whether the current environment can create and inspect
real symbolic links. It never skips the capability test.
"""

from __future__ import annotations

import os
from pathlib import Path


class SymlinkCapabilityError(RuntimeError):
    """Raised when the environment cannot create a real symbolic link."""


def create_test_symlink(
    target: Path,
    link: Path,
) -> None:
    """Create a real symbolic link for T16 verification."""

    if os.name == "nt":
        link.symlink_to(target, target_is_directory=target.is_dir())
    else:
        link.symlink_to(target)

    if not link.is_symlink():
        raise SymlinkCapabilityError(
            f"Symbolic link was not created correctly: {link}"
        )


def verify_symlink_capability(tmp_path: Path) -> Path:
    """Create and verify a real symbolic link."""

    target = tmp_path / "symlink_target.py"
    link = tmp_path / "symlink_probe.py"

    target.write_text(
        "SYMLINK_PROBE = True\n",
        encoding="utf-8",
    )

    try:
        create_test_symlink(target, link)
    except (OSError, NotImplementedError) as exc:
        raise SymlinkCapabilityError(
            "Real symbolic-link creation is unavailable in this environment. "
            "Windows requires Developer Mode or the SeCreateSymbolicLinkPrivilege."
        ) from exc

    if not link.is_symlink():
        raise SymlinkCapabilityError(
            "Symlink capability verification failed."
        )

    return link


__all__ = [
    "SymlinkCapabilityError",
    "create_test_symlink",
    "verify_symlink_capability",
]
