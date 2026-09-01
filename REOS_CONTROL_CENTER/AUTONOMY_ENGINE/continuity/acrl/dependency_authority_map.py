"""ACRL T05 — Dependency & Authority Map.

Defines a deterministic, read-only authority and dependency projection
for REOS autonomous continuity.

The existing REOS architecture remains authoritative.

This module:
    - identifies authoritative sources
    - identifies derived sources
    - records dependency relationships
    - detects authority conflicts
    - produces a deterministic fingerprint

This module does NOT:
    - modify state.json
    - modify architecture files
    - create a second source of truth
    - advance gates
    - complete subtasks
    - approve or freeze gates
    - modify ACRL __init__.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Iterable


class AuthorityMapError(RuntimeError):
    """Base error for authority-map failures."""


class AuthorityConflictError(AuthorityMapError):
    """Raised when authoritative sources conflict."""


class AuthorityMapIntegrityError(AuthorityMapError):
    """Raised when the authority map is structurally invalid."""


class AuthorityLevel(str, Enum):
    """Authority classification for project sources."""

    AUTHORITATIVE = "AUTHORITATIVE"
    DERIVED = "DERIVED"
    CONTEXT = "CONTEXT"


class DependencyType(str, Enum):
    """Relationship classification between consumers and sources."""

    AUTHORITATIVE = "AUTHORITATIVE"
    DERIVED_FROM = "DERIVED_FROM"
    CONTEXT_ONLY = "CONTEXT_ONLY"


@dataclass(frozen=True)
class AuthoritySource:
    """Immutable description of one project source."""

    source_id: str
    path: str
    level: AuthorityLevel
    purpose: str
    mutable_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "path",
            "purpose",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise AuthorityMapIntegrityError(
                    f"{field_name} must be a non-empty string."
                )

        object.__setattr__(
            self,
            "level",
            AuthorityLevel(self.level),
        )

        for item in self.mutable_by:
            if not isinstance(item, str) or not item.strip():
                raise AuthorityMapIntegrityError(
                    "mutable_by contains an invalid entry."
                )


@dataclass(frozen=True)
class AuthorityDependency:
    """Immutable dependency relationship."""

    consumer: str
    source: str
    dependency_type: DependencyType
    reason: str

    def __post_init__(self) -> None:
        for field_name in (
            "consumer",
            "source",
            "reason",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise AuthorityMapIntegrityError(
                    f"{field_name} must be a non-empty string."
                )

        object.__setattr__(
            self,
            "dependency_type",
            DependencyType(self.dependency_type),
        )


@dataclass(frozen=True)
class DependencyAuthorityMap:
    """Complete immutable authority/dependency projection."""

    sources: tuple[AuthoritySource, ...]
    dependencies: tuple[AuthorityDependency, ...]
    primary_authority: str
    fingerprint: str

    def source(self, source_id: str) -> AuthoritySource:
        """Return a source by ID."""

        for source in self.sources:
            if source.source_id == source_id:
                return source

        raise AuthorityMapIntegrityError(
            f"Unknown authority source: {source_id}"
        )

    def dependencies_for(
        self,
        consumer: str,
    ) -> tuple[AuthorityDependency, ...]:
        """Return dependencies for a consumer."""

        return tuple(
            item
            for item in self.dependencies
            if item.consumer == consumer
        )

    def to_dict(self) -> dict[str, Any]:
        """Return canonical serializable representation."""

        return {
            "schema_version": "1.0",
            "primary_authority": self.primary_authority,
            "sources": [
                {
                    "source_id": source.source_id,
                    "path": source.path,
                    "level": source.level.value,
                    "purpose": source.purpose,
                    "mutable_by": list(source.mutable_by),
                }
                for source in self.sources
            ],
            "dependencies": [
                {
                    "consumer": dependency.consumer,
                    "source": dependency.source,
                    "dependency_type": (
                        dependency.dependency_type.value
                    ),
                    "reason": dependency.reason,
                }
                for dependency in self.dependencies
            ],
            "fingerprint": self.fingerprint,
        }


class DependencyAuthorityMapBuilder:
    """Build the canonical ACRL authority/dependency map."""

    PRIMARY_AUTHORITY = "REOS_STATE"

    def build(
        self,
        *,
        sources: Iterable[AuthoritySource] | None = None,
        dependencies: Iterable[AuthorityDependency] | None = None,
    ) -> DependencyAuthorityMap:
        """Build and validate a deterministic authority map."""

        source_items = tuple(
            sources
            if sources is not None
            else self._default_sources()
        )

        dependency_items = tuple(
            dependencies
            if dependencies is not None
            else self._default_dependencies()
        )

        self._validate_sources(source_items)

        self._validate_dependencies(
            source_items,
            dependency_items,
        )

        fingerprint = self._fingerprint(
            source_items,
            dependency_items,
        )

        return DependencyAuthorityMap(
            sources=source_items,
            dependencies=dependency_items,
            primary_authority=self.PRIMARY_AUTHORITY,
            fingerprint=fingerprint,
        )

    @staticmethod
    def _default_sources() -> tuple[AuthoritySource, ...]:
        """Return the canonical REOS source definitions."""

        return (
            AuthoritySource(
                source_id="REOS_STATE",
                path="data/state.json",
                level=AuthorityLevel.AUTHORITATIVE,
                purpose=(
                    "Canonical machine-readable execution state "
                    "and current controller position."
                ),
                mutable_by=(
                    "REOS_CONTROL_CENTER",
                ),
            ),
            AuthoritySource(
                source_id="REOS_ARCHITECTURE",
                path="architecture",
                level=AuthorityLevel.AUTHORITATIVE,
                purpose=(
                    "Approved and frozen REOS architecture definition."
                ),
                mutable_by=(
                    "AUTHORIZED_ARCHITECTURE_CHANGE",
                ),
            ),
            AuthoritySource(
                source_id="REOS_CONTROLLER",
                path="reos_control_center.py",
                level=AuthorityLevel.AUTHORITATIVE,
                purpose=(
                    "Execution controller and gate-transition authority."
                ),
                mutable_by=(
                    "REOS_ENGINEERING",
                ),
            ),
            AuthoritySource(
                source_id="ACRL",
                path="AUTONOMY_ENGINE/continuity/acrl",
                level=AuthorityLevel.DERIVED,
                purpose=(
                    "Autonomous continuity, reconstruction, "
                    "validation, and recovery projections."
                ),
                mutable_by=(
                    "REOS_ENGINEERING",
                ),
            ),
            AuthoritySource(
                source_id="CHAT_CONTEXT",
                path="chat/session",
                level=AuthorityLevel.CONTEXT,
                purpose=(
                    "Operator communication and temporary context only."
                ),
                mutable_by=(),
            ),
        )

    @staticmethod
    def _default_dependencies() -> tuple[AuthorityDependency, ...]:
        """Return canonical dependency relationships."""

        return (
            AuthorityDependency(
                consumer="ACRL",
                source="REOS_STATE",
                dependency_type=DependencyType.AUTHORITATIVE,
                reason=(
                    "Execution continuity must reconstruct from "
                    "controller state."
                ),
            ),
            AuthorityDependency(
                consumer="ACRL",
                source="REOS_ARCHITECTURE",
                dependency_type=DependencyType.AUTHORITATIVE,
                reason=(
                    "Continuity decisions must remain inside "
                    "the approved architecture."
                ),
            ),
            AuthorityDependency(
                consumer="ACRL",
                source="REOS_CONTROLLER",
                dependency_type=DependencyType.AUTHORITATIVE,
                reason=(
                    "Gate and execution transitions remain under "
                    "REOS Control Center authority."
                ),
            ),
            AuthorityDependency(
                consumer="ACRL",
                source="CHAT_CONTEXT",
                dependency_type=DependencyType.CONTEXT_ONLY,
                reason=(
                    "Chat may provide instructions but cannot "
                    "override authoritative project state."
                ),
            ),
            AuthorityDependency(
                consumer="NEW_CHAT",
                source="ACRL",
                dependency_type=DependencyType.DERIVED_FROM,
                reason=(
                    "A new chat consumes reconstructed continuity "
                    "instead of requiring manual historical replay."
                ),
            ),
        )

    @staticmethod
    def _validate_sources(
        sources: tuple[AuthoritySource, ...],
    ) -> None:
        """Validate source identity and authority rules."""

        if not sources:
            raise AuthorityMapIntegrityError(
                "Authority map must contain at least one source."
            )

        ids = [
            source.source_id
            for source in sources
        ]

        if len(ids) != len(set(ids)):
            raise AuthorityMapIntegrityError(
                "Authority source IDs must be unique."
            )

        authoritative = [
            source
            for source in sources
            if source.level == AuthorityLevel.AUTHORITATIVE
        ]

        if not authoritative:
            raise AuthorityMapIntegrityError(
                "At least one authoritative source is required."
            )

        primary = next(
            (
                source
                for source in authoritative
                if source.source_id
                == DependencyAuthorityMapBuilder.PRIMARY_AUTHORITY
            ),
            None,
        )

        if primary is None:
            raise AuthorityConflictError(
                "REOS_STATE must remain the primary authority."
            )

    @staticmethod
    def _validate_dependencies(
        sources: tuple[AuthoritySource, ...],
        dependencies: tuple[AuthorityDependency, ...],
    ) -> None:
        """Validate all dependency relationships."""

        known = {
            source.source_id
            for source in sources
        }

        for dependency in dependencies:
            if dependency.source not in known:
                raise AuthorityMapIntegrityError(
                    "Dependency references unknown source: "
                    f"{dependency.source}"
                )

        acrl_authoritative_sources = {
            dependency.source
            for dependency in dependencies
            if (
                dependency.consumer == "ACRL"
                and dependency.dependency_type
                == DependencyType.AUTHORITATIVE
            )
        }

        if not acrl_authoritative_sources:
            raise AuthorityConflictError(
                "ACRL must depend on authoritative REOS sources."
            )

        if "REOS_STATE" not in acrl_authoritative_sources:
            raise AuthorityConflictError(
                "ACRL must depend on REOS_STATE."
            )

    @staticmethod
    def _fingerprint(
        sources: tuple[AuthoritySource, ...],
        dependencies: tuple[AuthorityDependency, ...],
    ) -> str:
        """Generate a deterministic SHA-256 fingerprint."""

        payload = {
            "sources": [
                {
                    "source_id": source.source_id,
                    "path": source.path,
                    "level": source.level.value,
                    "purpose": source.purpose,
                    "mutable_by": source.mutable_by,
                }
                for source in sources
            ],
            "dependencies": [
                {
                    "consumer": dependency.consumer,
                    "source": dependency.source,
                    "dependency_type": (
                        dependency.dependency_type.value
                    ),
                    "reason": dependency.reason,
                }
                for dependency in dependencies
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


def build_dependency_authority_map() -> DependencyAuthorityMap:
    """Build the default canonical dependency/authority map."""

    return DependencyAuthorityMapBuilder().build()


__all__ = [
    "AuthorityConflictError",
    "AuthorityDependency",
    "AuthorityLevel",
    "AuthorityMapError",
    "AuthorityMapIntegrityError",
    "AuthoritySource",
    "DependencyAuthorityMap",
    "DependencyAuthorityMapBuilder",
    "DependencyType",
    "build_dependency_authority_map",
]