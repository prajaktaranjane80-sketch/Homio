"""T16 PART-01 — Repository path boundary.

Provides fail-closed repository path validation.
Symlinks are never silently treated as ordinary repository files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class RepositoryBoundaryError(RuntimeError):
    """Raised when a path violates the repository boundary."""


@dataclass(frozen=True, slots=True)
class RepositoryBoundary:
    """Immutable repository boundary."""

    root: Path

    @classmethod
    def create(cls, root: Path) -> "RepositoryBoundary":
        if not root.exists():
            raise RepositoryBoundaryError(
                f"Repository root does not exist: {root}"
            )

        if not root.is_dir():
            raise RepositoryBoundaryError(
                f"Repository root is not a directory: {root}"
            )

        try:
            resolved = root.resolve(strict=True)
        except OSError as exc:
            raise RepositoryBoundaryError(
                f"Unable to resolve repository root: {root}"
            ) from exc

        return cls(root=resolved)

    def contains(self, candidate: Path) -> bool:
        """Return True only when candidate remains inside the root."""

        try:
            candidate_resolved = candidate.resolve(strict=False)
            candidate_resolved.relative_to(self.root)
        except (OSError, ValueError):
            return False

        return True

    def require(self, candidate: Path) -> Path:
        """Resolve and validate a path, failing closed outside the root."""

        if candidate.is_symlink():
            raise RepositoryBoundaryError(
                f"Symlink paths are not accepted as ordinary repository paths: "
                f"{candidate}"
            )

        try:
            resolved = candidate.resolve(strict=False)
        except OSError as exc:
            raise RepositoryBoundaryError(
                f"Unable to resolve repository path: {candidate}"
            ) from exc

        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise RepositoryBoundaryError(
                f"Path escapes repository boundary: {candidate}"
            ) from exc

        return resolved


__all__ = [
    "RepositoryBoundary",
    "RepositoryBoundaryError",
]