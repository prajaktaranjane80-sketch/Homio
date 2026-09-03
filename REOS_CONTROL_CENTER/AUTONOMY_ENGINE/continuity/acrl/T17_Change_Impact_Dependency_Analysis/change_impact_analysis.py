"""ACRL T17 — Change Impact & Dependency Analysis."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .repository_intelligence import (
    FileAuthority,
    FileRisk,
    find_repository_files,
    normalize_repository_path,
)


class ChangeImpactError(RuntimeError):
    """Base error for T17 change-impact analysis."""


class ImpactLevel(str, Enum):
    """Impact classification for a changed repository path."""

    DIRECT = "DIRECT"
    PROTECTED = "PROTECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ChangeImpact:
    """Impact classification for one changed repository path."""

    relative_path: str
    impact_level: ImpactLevel
    authority: FileAuthority | None
    source_kind: str | None
    reason: str


@dataclass(frozen=True)
class ChangeImpactReport:
    """Deterministic result of a change-impact analysis."""

    changed_paths: tuple[str, ...]
    impacts: tuple[ChangeImpact, ...]
    fingerprint: str

    @property
    def impacted_paths(self) -> tuple[str, ...]:
        """Return paths with a known impact classification."""
        return tuple(
            item.relative_path
            for item in self.impacts
            if item.impact_level != ImpactLevel.UNKNOWN
        )


class ChangeImpactAnalyzer:
    """Deterministic, read-only T17 impact analyzer."""

    def __init__(self, repository_root: Path | str) -> None:
        self.repository_root = Path(repository_root).resolve()

        if not self.repository_root.is_dir():
            raise ChangeImpactError(
                f"Repository root is not a directory: {self.repository_root}"
            )

    def analyze(
        self,
        changed_paths: Iterable[str],
    ) -> ChangeImpactReport:
        """Analyze changed repository paths without modifying repository state."""

        normalized_paths = self._normalize_paths(changed_paths)

        impacts = tuple(
            self._analyze_path(path)
            for path in normalized_paths
        )

        return ChangeImpactReport(
            changed_paths=normalized_paths,
            impacts=impacts,
            fingerprint=self._fingerprint(
                normalized_paths,
                impacts,
            ),
        )

    def _analyze_path(
        self,
        relative_path: str,
    ) -> ChangeImpact:
        """Classify one normalized repository-relative path."""

        matches = find_repository_files(
            self.repository_root,
            relative_path,
        )

        exact = next(
            (
                item
                for item in matches
                if normalize_repository_path(item.relative_path)
                == relative_path
            ),
            None,
        )

        if exact is None:
            return ChangeImpact(
                relative_path=relative_path,
                impact_level=ImpactLevel.UNKNOWN,
                authority=None,
                source_kind=None,
                reason=(
                    "Changed path was not found in repository intelligence."
                ),
            )

        if exact.risk == FileRisk.PROTECTED:
            return ChangeImpact(
                relative_path=relative_path,
                impact_level=ImpactLevel.PROTECTED,
                authority=exact.authority,
                source_kind=exact.source_kind.value,
                reason="Changed file is protected.",
            )

        return ChangeImpact(
            relative_path=relative_path,
            impact_level=ImpactLevel.DIRECT,
            authority=exact.authority,
            source_kind=exact.source_kind.value,
            reason=(
                "Changed path directly matches a repository file."
            ),
        )

    @staticmethod
    def _normalize_paths(
        paths: Iterable[str],
    ) -> tuple[str, ...]:
        """Normalize, validate, deduplicate, and deterministically sort paths."""

        normalized = {
            normalize_repository_path(path)
            for path in paths
        }

        if any(not path for path in normalized):
            raise ChangeImpactError(
                "Changed path cannot be empty."
            )

        return tuple(sorted(normalized))

    @staticmethod
    def _fingerprint(
        changed_paths: tuple[str, ...],
        impacts: tuple[ChangeImpact, ...],
    ) -> str:
        """Create a deterministic SHA-256 fingerprint of the report."""

        payload = {
            "changed_paths": changed_paths,
            "impacts": [
                {
                    "relative_path": item.relative_path,
                    "impact_level": item.impact_level.value,
                    "authority": (
                        item.authority.value
                        if item.authority is not None
                        else None
                    ),
                    "source_kind": item.source_kind,
                    "reason": item.reason,
                }
                for item in impacts
            ],
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


__all__ = [
    "ChangeImpact",
    "ChangeImpactAnalyzer",
    "ChangeImpactError",
    "ChangeImpactReport",
    "ImpactLevel",
]