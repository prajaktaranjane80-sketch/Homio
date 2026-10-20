"""T14 repository context facade over canonical T16 intelligence + fast resume."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from AUTONOMY_ENGINE.continuity.acrl.T16_Repository_Intelligence_File_Discovery.repository_intelligence import (
    FileAuthority,
    FileRisk,
    RepositoryFile,
    RepositoryFingerprintError,
    RepositoryIntegrityError,
    RepositoryPathSecurityError,
    RepositorySourceError,
    SearchMatchMode,
    SourceKind,
    discover_repository,
    normalize_repository_path,
)
from .audit_resume_manifest import ResumeAssessment, assess_resume_manifest

SCHEMA_VERSION = "1.0"
AUTHORITY = "REOS_CONTROL_CENTER"


class RepositoryContextDecision(str, Enum):
    RESOLVED = "RESOLVED"
    BLOCKED = "BLOCKED"
    FAIL_CLOSED = "FAIL_CLOSED"


class RepositoryContextReason(str, Enum):
    VALID = "VALID"
    REPOSITORY_UNAVAILABLE = "REPOSITORY_UNAVAILABLE"
    NO_RELEVANT_FILES = "NO_RELEVANT_FILES"
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    PATH_SECURITY_FAILURE = "PATH_SECURITY_FAILURE"


class RepositoryContextError(Exception):
    """Base error for T14."""


class RepositoryContextAuthorityError(RepositoryContextError):
    """Repository context authority contract violated."""


class RepositoryContextValidationError(RepositoryContextError):
    """Repository context request is invalid."""


@dataclass(frozen=True, slots=True)
class RepositoryContextRequest:
    repository_root: Path
    current_gate: str | None
    current_task: str | None
    current_subtask: str | None
    candidate_paths: tuple[str, ...] = ()
    search_terms: tuple[str, ...] = ()
    expected_authority: str = AUTHORITY


@dataclass(frozen=True, slots=True)
class RepositoryContextReport:
    schema_version: str
    authority: str
    decision: RepositoryContextDecision
    reason: RepositoryContextReason
    repository_root: str
    repository_fingerprint: str | None
    current_gate: str | None
    current_task: str | None
    current_subtask: str | None
    relevant_files: tuple[RepositoryFile, ...]
    test_files: tuple[RepositoryFile, ...]
    python_files: tuple[RepositoryFile, ...]
    execution_authorized: bool
    validated: bool
    observational_only: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "authority": self.authority,
            "decision": self.decision.value,
            "reason": self.reason.value,
            "repository_root": self.repository_root,
            "repository_fingerprint": self.repository_fingerprint,
            "current_gate": self.current_gate,
            "current_task": self.current_task,
            "current_subtask": self.current_subtask,
            "relevant_files": [
                {
                    "relative_path": item.relative_path,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "source_kind": item.source_kind.value,
                    "authority": item.authority.value,
                    "risk": item.risk.value,
                    "is_symlink": item.is_symlink,
                }
                for item in self.relevant_files
            ],
            "test_files": [item.relative_path for item in self.test_files],
            "python_files": [item.relative_path for item in self.python_files],
            "execution_authorized": self.execution_authorized,
            "validated": self.validated,
            "observational_only": self.observational_only,
        }


class RepositoryContextEngine:
    """Thin T14 layer. T16 remains the canonical source/dependency graph."""

    STOP_WORDS = frozenset({
        "the", "and", "for", "with", "from", "implement", "implementation",
        "create", "build", "update", "fix", "current", "task", "domain",
        "part", "repository", "intelligence",
    })
    IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]{2,}")

    @staticmethod
    def evaluate_fast_resume(
        *,
        manifest: Mapping[str, Any],
        live_snapshot: Mapping[str, Any],
        dependency_graph: Mapping[str, Sequence[str]] | None = None,
        now: datetime | None = None,
    ) -> ResumeAssessment:
        """Check a validated cache before invoking the full T16 repository scan.

        The caller must obtain live HEAD, state.json SHA, branch and working-tree
        cleanliness independently. A cached position never becomes authority.
        """
        return assess_resume_manifest(
            manifest,
            live_snapshot,
            dependency_graph=dependency_graph,
            now=now,
        )

    @staticmethod
    def _match_snapshot_files(
        snapshot: Any,
        pattern: str,
        match_mode: SearchMatchMode,
    ) -> tuple[RepositoryFile, ...]:
        """Filter one already-discovered T16 snapshot; never rescan per term."""
        normalized_pattern = normalize_repository_path(pattern)
        has_separator = "/" in normalized_pattern
        results: list[RepositoryFile] = []

        for item in snapshot.files:
            if item.source_kind in {
                SourceKind.GENERATED,
                SourceKind.VENDOR,
                SourceKind.CACHE,
            }:
                continue

            normalized_path = normalize_repository_path(item.relative_path)
            normalized_name = Path(normalized_path).name.lower()

            if match_mode is SearchMatchMode.CONTAINS:
                matched = normalized_pattern.lower() in normalized_path.lower()
            elif match_mode is SearchMatchMode.EXACT:
                if has_separator:
                    matched = normalized_pattern.lower() == normalized_path.lower()
                else:
                    matched = normalized_pattern.lower() == normalized_name
            elif match_mode is SearchMatchMode.GLOB:
                matched = fnmatch.fnmatchcase(
                    normalized_path.lower(),
                    normalized_pattern.lower(),
                )
            else:
                raise RepositoryContextValidationError(
                    "Unsupported repository search mode"
                )

            if matched:
                results.append(item)

        return tuple(sorted(results, key=lambda item: item.relative_path.lower()))

    @classmethod
    def resolve(
        cls,
        request: RepositoryContextRequest,
    ) -> RepositoryContextReport:
        cls._validate_request(request)
        root = Path(request.repository_root).resolve()

        try:
            # One canonical T16 scan supplies every query in this resolution.
            # Repeated calls to find_repository_files() create new T16 engines
            # and rescan the tree for each search term.
            snapshot = discover_repository(root)
            matches: dict[str, RepositoryFile] = {}

            for candidate in request.candidate_paths:
                for item in cls._match_snapshot_files(
                    snapshot,
                    candidate,
                    SearchMatchMode.EXACT,
                ):
                    matches[item.relative_path] = item

            terms = list(request.search_terms)
            terms.extend(
                cls.derive_search_terms(
                    request.current_gate,
                    request.current_task,
                    request.current_subtask,
                )
            )

            seen: set[str] = set()
            for term in terms:
                normalized = term.strip()
                key = normalized.lower()

                if not normalized or key in seen:
                    continue

                seen.add(key)

                for item in cls._match_snapshot_files(
                    snapshot,
                    normalized,
                    SearchMatchMode.CONTAINS,
                ):
                    matches[item.relative_path] = item

            relevant = tuple(
                sorted(matches.values(), key=lambda item: item.relative_path.lower())
            )

            if not relevant:
                return cls._report(
                    request=request,
                    decision=RepositoryContextDecision.BLOCKED,
                    reason=RepositoryContextReason.NO_RELEVANT_FILES,
                    fingerprint=snapshot.fingerprint,
                    files=(),
                )

            paths = {item.relative_path for item in relevant}
            tests = tuple(
                item for item in snapshot.test_files
                if item.relative_path in paths
            )
            python_files = tuple(
                item for item in snapshot.python_files
                if item.relative_path in paths
            )

            return cls._report(
                request=request,
                decision=RepositoryContextDecision.RESOLVED,
                reason=RepositoryContextReason.VALID,
                fingerprint=snapshot.fingerprint,
                files=relevant,
                tests=tests,
                python_files=python_files,
            )

        except RepositoryPathSecurityError:
            return cls._report(
                request=request,
                decision=RepositoryContextDecision.FAIL_CLOSED,
                reason=RepositoryContextReason.PATH_SECURITY_FAILURE,
                fingerprint=None,
                files=(),
            )
        except (RepositoryFingerprintError, RepositoryIntegrityError):
            return cls._report(
                request=request,
                decision=RepositoryContextDecision.FAIL_CLOSED,
                reason=RepositoryContextReason.INTEGRITY_FAILURE,
                fingerprint=None,
                files=(),
            )
        except RepositorySourceError:
            return cls._report(
                request=request,
                decision=RepositoryContextDecision.BLOCKED,
                reason=RepositoryContextReason.REPOSITORY_UNAVAILABLE,
                fingerprint=None,
                files=(),
            )

    @classmethod
    def derive_search_terms(
        cls,
        gate: str | None,
        task: str | None,
        subtask: str | None,
    ) -> tuple[str, ...]:
        terms: set[str] = set()

        for value in (gate or "", task or "", subtask or ""):
            for match in cls.IDENTIFIER_PATTERN.findall(value):
                normalized = match.strip("._-")
                if (
                    len(normalized) >= 3
                    and normalized.lower() not in cls.STOP_WORDS
                ):
                    terms.add(normalized)

        return tuple(sorted(terms, key=str.lower))

    @staticmethod
    def _validate_request(request: RepositoryContextRequest) -> None:
        if not isinstance(request, RepositoryContextRequest):
            raise RepositoryContextValidationError(
                "request must be RepositoryContextRequest"
            )

        if request.expected_authority != AUTHORITY:
            raise RepositoryContextAuthorityError(
                "Repository intelligence authority must remain REOS_CONTROL_CENTER"
            )

        if not str(request.repository_root).strip():
            raise RepositoryContextValidationError(
                "repository_root is required"
            )

    @classmethod
    def _report(
        cls,
        *,
        request: RepositoryContextRequest,
        decision: RepositoryContextDecision,
        reason: RepositoryContextReason,
        fingerprint: str | None,
        files: tuple[RepositoryFile, ...],
        tests: tuple[RepositoryFile, ...] = (),
        python_files: tuple[RepositoryFile, ...] = (),
    ) -> RepositoryContextReport:
        return RepositoryContextReport(
            schema_version=SCHEMA_VERSION,
            authority=AUTHORITY,
            decision=decision,
            reason=reason,
            repository_root=str(Path(request.repository_root).resolve()),
            repository_fingerprint=fingerprint,
            current_gate=request.current_gate,
            current_task=request.current_task,
            current_subtask=request.current_subtask,
            relevant_files=files,
            test_files=tests,
            python_files=python_files,
            execution_authorized=False,
            validated=decision is RepositoryContextDecision.RESOLVED,
            observational_only=True,
        )


def evaluate_fast_resume(
    *,
    manifest: Mapping[str, Any],
    live_snapshot: Mapping[str, Any],
    dependency_graph: Mapping[str, Sequence[str]] | None = None,
    now: datetime | None = None,
) -> ResumeAssessment:
    return RepositoryContextEngine.evaluate_fast_resume(
        manifest=manifest,
        live_snapshot=live_snapshot,
        dependency_graph=dependency_graph,
        now=now,
    )


def resolve_repository_context(
    request: RepositoryContextRequest,
) -> RepositoryContextReport:
    return RepositoryContextEngine.resolve(request)


__all__ = [
    "AUTHORITY",
    "SCHEMA_VERSION",
    "RepositoryContextDecision",
    "RepositoryContextReason",
    "RepositoryContextError",
    "RepositoryContextAuthorityError",
    "RepositoryContextValidationError",
    "RepositoryContextRequest",
    "RepositoryContextReport",
    "RepositoryContextEngine",
    "evaluate_fast_resume",
    "resolve_repository_context",
]
