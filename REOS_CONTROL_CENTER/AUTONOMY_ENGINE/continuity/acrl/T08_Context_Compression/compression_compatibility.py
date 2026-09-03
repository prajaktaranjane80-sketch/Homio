"""ACRL T08 — Compression Compatibility.

Provides fail-closed compatibility classification for compressed
context versions.

Unknown or future versions are never silently accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class CompressionCompatibilityError(ValueError):
    """Base compatibility error."""


class CompressionCompatibilityStatus(str, Enum):
    """Compatibility outcomes."""

    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CompatibilityResult:
    """Immutable compatibility decision."""

    status: CompressionCompatibilityStatus
    source_version: str
    target_version: str
    migration_required: bool
    reason: str

    @property
    def compatible(self) -> bool:
        """Whether the context may safely proceed."""

        return self.status in {
            CompressionCompatibilityStatus.SUPPORTED,
            CompressionCompatibilityStatus.MIGRATABLE,
        }

    @property
    def fail_closed(self) -> bool:
        """Whether execution must stop."""

        return not self.compatible


class CompressionCompatibilityEngine:
    """Deterministic T08 version compatibility engine."""

    CURRENT_SCHEMA_VERSION: Final[str] = "1.0"
    CURRENT_COMPRESSION_VERSION: Final[str] = "T08-1.0"
    CURRENT_POLICY_VERSION: Final[str] = "T08-POLICY-1.0"

    SUPPORTED_SCHEMA_VERSIONS: Final[frozenset[str]] = frozenset(
        {"1.0"}
    )

    SUPPORTED_COMPRESSION_VERSIONS: Final[
        frozenset[str]
    ] = frozenset(
        {"T08-1.0"}
    )

    SUPPORTED_POLICY_VERSIONS: Final[
        frozenset[str]
    ] = frozenset(
        {"T08-POLICY-1.0"}
    )

    MIGRATABLE_SCHEMA_VERSIONS: Final[
        frozenset[str]
    ] = frozenset()

    MIGRATABLE_COMPRESSION_VERSIONS: Final[
        frozenset[str]
    ] = frozenset()

    MIGRATABLE_POLICY_VERSIONS: Final[
        frozenset[str]
    ] = frozenset()

    @classmethod
    def check_schema(
        cls,
        source_version: str,
    ) -> CompatibilityResult:
        """Check schema compatibility."""

        return cls._check(
            source_version=source_version,
            target_version=cls.CURRENT_SCHEMA_VERSION,
            supported=cls.SUPPORTED_SCHEMA_VERSIONS,
            migratable=cls.MIGRATABLE_SCHEMA_VERSIONS,
            label="schema",
        )

    @classmethod
    def check_compression(
        cls,
        source_version: str,
    ) -> CompatibilityResult:
        """Check compression-version compatibility."""

        return cls._check(
            source_version=source_version,
            target_version=cls.CURRENT_COMPRESSION_VERSION,
            supported=cls.SUPPORTED_COMPRESSION_VERSIONS,
            migratable=cls.MIGRATABLE_COMPRESSION_VERSIONS,
            label="compression",
        )

    @classmethod
    def check_policy(
        cls,
        source_version: str,
    ) -> CompatibilityResult:
        """Check compression-policy compatibility."""

        return cls._check(
            source_version=source_version,
            target_version=cls.CURRENT_POLICY_VERSION,
            supported=cls.SUPPORTED_POLICY_VERSIONS,
            migratable=cls.MIGRATABLE_POLICY_VERSIONS,
            label="policy",
        )

    @classmethod
    def validate(
        cls,
        *,
        schema_version: str,
        compression_version: str,
        policy_version: str,
    ) -> None:
        """Fail closed unless every version is safe."""

        results = (
            cls.check_schema(schema_version),
            cls.check_compression(compression_version),
            cls.check_policy(policy_version),
        )

        incompatible = [
            result
            for result in results
            if not result.compatible
        ]

        if incompatible:
            details = "; ".join(
                (
                    f"{result.status.value}: "
                    f"{result.reason}"
                )
                for result in incompatible
            )

            raise CompressionCompatibilityError(
                "T08 compatibility validation failed: "
                f"{details}"
            )

    @classmethod
    def _check(
        cls,
        *,
        source_version: str,
        target_version: str,
        supported: frozenset[str],
        migratable: frozenset[str],
        label: str,
    ) -> CompatibilityResult:
        if not isinstance(
            source_version,
            str,
        ) or not source_version.strip():
            return CompatibilityResult(
                status=CompressionCompatibilityStatus.UNKNOWN,
                source_version=str(source_version),
                target_version=target_version,
                migration_required=False,
                reason=(
                    f"Unknown {label} version."
                ),
            )

        if source_version in supported:
            return CompatibilityResult(
                status=CompressionCompatibilityStatus.SUPPORTED,
                source_version=source_version,
                target_version=target_version,
                migration_required=False,
                reason=(
                    f"{label.capitalize()} version is supported."
                ),
            )

        if source_version in migratable:
            return CompatibilityResult(
                status=CompressionCompatibilityStatus.MIGRATABLE,
                source_version=source_version,
                target_version=target_version,
                migration_required=True,
                reason=(
                    f"{label.capitalize()} version requires "
                    "an explicit migration."
                ),
            )

        return CompatibilityResult(
            status=CompressionCompatibilityStatus.UNKNOWN,
            source_version=source_version,
            target_version=target_version,
            migration_required=False,
            reason=(
                f"Unknown or unsupported {label} version; "
                "fail closed."
            ),
        )


def validate_compression_compatibility(
    *,
    schema_version: str,
    compression_version: str,
    policy_version: str,
) -> None:
    """Convenience API for T08 compatibility validation."""

    CompressionCompatibilityEngine.validate(
        schema_version=schema_version,
        compression_version=compression_version,
        policy_version=policy_version,
    )


__all__ = [
    "CompatibilityResult",
    "CompressionCompatibilityEngine",
    "CompressionCompatibilityError",
    "CompressionCompatibilityStatus",
    "validate_compression_compatibility",
]
