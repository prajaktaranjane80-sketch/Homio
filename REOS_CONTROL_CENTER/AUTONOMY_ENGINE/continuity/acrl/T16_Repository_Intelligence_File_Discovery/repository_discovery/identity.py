"""T16 PART-01 — Repository identity.

Provides deterministic, read-only identity information for a repository.
This module does not modify the repository and does not own project state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


class RepositoryIdentityError(RuntimeError):
    """Raised when repository identity cannot be established."""


@dataclass(frozen=True, slots=True)
class RepositoryIdentity:
    """Immutable repository identity."""

    root: str
    name: str
    normalized_root: str
    identity_hash: str


def _normalize_root(root: Path) -> Path:
    """Return a resolved repository root without mutating anything."""

    if not root.exists():
        raise RepositoryIdentityError(
            f"Repository root does not exist: {root}"
        )

    if not root.is_dir():
        raise RepositoryIdentityError(
            f"Repository root is not a directory: {root}"
        )

    try:
        return root.resolve(strict=True)
    except OSError as exc:
        raise RepositoryIdentityError(
            f"Unable to resolve repository root: {root}"
        ) from exc


def identify_repository(root: Path) -> RepositoryIdentity:
    """Create a deterministic immutable repository identity."""

    resolved = _normalize_root(root)

    normalized = resolved.as_posix().rstrip("/")

    if not normalized:
        raise RepositoryIdentityError(
            "Repository root resolved to an empty path."
        )

    name = resolved.name or resolved.anchor.rstrip("/\\")

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()

    return RepositoryIdentity(
        root=str(root),
        name=name,
        normalized_root=normalized,
        identity_hash=digest,
    )


__all__ = [
    "RepositoryIdentity",
    "RepositoryIdentityError",
    "identify_repository",
]