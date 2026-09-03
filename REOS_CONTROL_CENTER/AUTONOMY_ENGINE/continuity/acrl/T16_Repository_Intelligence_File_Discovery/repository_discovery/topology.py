"""T16 PART-01 — Deterministic filesystem topology discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .boundary import RepositoryBoundary, RepositoryBoundaryError
from .classification import (
    DEFAULT_EXCLUDED_DIRECTORIES,
    EntryKind,
    SourceClassification,
    classify_entry,
)


class RepositoryTopologyError(RuntimeError):
    """Raised when topology discovery cannot complete safely."""


@dataclass(frozen=True, slots=True)
class RepositoryEntry:
    """Immutable description of one repository entry."""

    relative_path: str
    kind: EntryKind
    classification: SourceClassification
    is_symlink: bool


@dataclass(frozen=True, slots=True)
class RepositoryTopology:
    """Immutable deterministic repository topology."""

    entries: tuple[RepositoryEntry, ...]
    excluded_directories: tuple[str, ...]


class RepositoryTopologyScanner:
    """Read-only repository topology scanner."""

    def __init__(
        self,
        root: Path,
        *,
        excluded_directories: frozenset[str] = DEFAULT_EXCLUDED_DIRECTORIES,
    ) -> None:
        self._boundary = RepositoryBoundary.create(root)
        self._excluded_directories = excluded_directories

    def scan(self) -> RepositoryTopology:
        entries: list[RepositoryEntry] = []
        excluded: set[str] = set()

        for current_root, directories, files in self._walk():
            current = Path(current_root)

            retained_directories: list[str] = []

            for directory in directories:
                if directory in self._excluded_directories:
                    excluded.add(
                        (current / directory)
                        .relative_to(self._boundary.root)
                        .as_posix()
                    )
                    continue

                retained_directories.append(directory)

            directories[:] = sorted(retained_directories)

            for filename in sorted(files):
                candidate = current / filename

                try:
                    relative = candidate.relative_to(
                        self._boundary.root
                    ).as_posix()
                except ValueError as exc:
                    raise RepositoryTopologyError(
                        f"Discovered path outside repository: {candidate}"
                    ) from exc

                kind, classification = classify_entry(candidate)

                entries.append(
                    RepositoryEntry(
                        relative_path=relative,
                        kind=kind,
                        classification=classification,
                        is_symlink=candidate.is_symlink(),
                    )
                )

        entries.sort(key=lambda item: item.relative_path)

        return RepositoryTopology(
            entries=tuple(entries),
            excluded_directories=tuple(sorted(excluded)),
        )

    def _walk(self):
        """Walk without following directory symlinks."""

        import os

        try:
            yield from os.walk(
                self._boundary.root,
                topdown=True,
                followlinks=False,
            )
        except OSError as exc:
            raise RepositoryTopologyError(
                "Repository topology discovery failed."
            ) from exc


__all__ = [
    "RepositoryEntry",
    "RepositoryTopology",
    "RepositoryTopologyError",
    "RepositoryTopologyScanner",
]