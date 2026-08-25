"""Workspace manifest primitives for AUTONOMY_ENGINE V6.

Provides deterministic, read-only representation and validation of the
AUTONOMY_ENGINE workspace.

This addition does not modify files and does not replace the existing
workspace_guard or integrity mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class WorkspaceEntry:
    """Immutable description of one workspace entry."""

    relative_path: str
    entry_type: str
    required: bool = True

    def __post_init__(self) -> None:
        if not self.relative_path:
            raise ValueError("relative_path is required")

        if self.entry_type not in {"file", "directory"}:
            raise ValueError(
                "entry_type must be 'file' or 'directory'"
            )


@dataclass(frozen=True)
class WorkspaceCheck:
    """Result of validating one workspace entry."""

    relative_path: str
    expected_type: str
    exists: bool
    type_matches: bool

    @property
    def valid(self) -> bool:
        """Return whether the workspace entry satisfies its contract."""
        return self.exists and self.type_matches


class WorkspaceManifest:
    """Read-only manifest for deterministic workspace validation."""

    def __init__(
        self,
        root: str | Path,
        entries: Iterable[WorkspaceEntry] | None = None,
    ) -> None:
        self._root = Path(root).resolve()

        if not self._root.exists():
            raise FileNotFoundError(
                f"workspace root does not exist: {self._root}"
            )

        if not self._root.is_dir():
            raise NotADirectoryError(
                f"workspace root is not a directory: {self._root}"
            )

        self._entries: dict[str, WorkspaceEntry] = {}

        for entry in entries or ():
            self.register(entry)

    @property
    def root(self) -> Path:
        """Return the resolved workspace root."""
        return self._root

    def register(self, entry: WorkspaceEntry) -> None:
        """Register an expected workspace entry."""
        normalized = self._normalize_relative_path(
            entry.relative_path
        )

        if normalized in self._entries:
            raise ValueError(
                f"workspace entry already registered: {normalized}"
            )

        self._entries[normalized] = WorkspaceEntry(
            relative_path=normalized,
            entry_type=entry.entry_type,
            required=entry.required,
        )

    def resolve(self, relative_path: str) -> Path:
        """Resolve a manifest-relative path without escaping the workspace."""
        normalized = self._normalize_relative_path(relative_path)
        candidate = (self._root / normalized).resolve()

        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise ValueError(
                f"path escapes workspace root: {relative_path}"
            ) from exc

        return candidate

    def check(
        self,
        relative_path: str,
    ) -> WorkspaceCheck:
        """Validate one registered workspace entry."""
        normalized = self._normalize_relative_path(relative_path)
        entry = self._entries.get(normalized)

        if entry is None:
            raise KeyError(
                f"workspace entry is not registered: {normalized}"
            )

        path = self.resolve(normalized)
        exists = path.exists()

        if entry.entry_type == "file":
            type_matches = path.is_file() if exists else False
        else:
            type_matches = path.is_dir() if exists else False

        return WorkspaceCheck(
            relative_path=normalized,
            expected_type=entry.entry_type,
            exists=exists,
            type_matches=type_matches,
        )

    def validate(self) -> tuple[WorkspaceCheck, ...]:
        """Validate all registered entries."""
        return tuple(
            self.check(relative_path)
            for relative_path in sorted(self._entries)
        )

    def missing_required(self) -> tuple[str, ...]:
        """Return required entries that are missing or have wrong types."""
        return tuple(
            result.relative_path
            for result in self.validate()
            if not result.valid
            and self._entries[result.relative_path].required
        )

    def is_valid(self) -> bool:
        """Return whether all required entries satisfy the manifest."""
        return not self.missing_required()

    def snapshot(self) -> tuple[WorkspaceEntry, ...]:
        """Return a deterministic manifest snapshot."""
        return tuple(
            self._entries[path]
            for path in sorted(self._entries)
        )

    @staticmethod
    def _normalize_relative_path(relative_path: str) -> str:
        """Normalize and reject unsafe relative paths."""
        if not relative_path:
            raise ValueError("relative_path is required")

        path = Path(relative_path)

        if path.is_absolute():
            raise ValueError(
                "manifest paths must be relative"
            )

        normalized = path.as_posix().strip("/")

        if not normalized or normalized == ".":
            raise ValueError(
                "relative_path must identify a workspace entry"
            )

        parts = Path(normalized).parts

        if ".." in parts:
            raise ValueError(
                "relative_path cannot contain parent traversal"
            )

        return normalized

    def __len__(self) -> int:
        """Return the number of registered entries."""
        return len(self._entries)