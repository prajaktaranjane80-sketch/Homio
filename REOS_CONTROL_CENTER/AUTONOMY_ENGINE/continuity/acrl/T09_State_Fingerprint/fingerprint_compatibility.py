"""ACRL T09 — Fingerprint Compatibility.

Defines explicit version compatibility rules for T09 artifacts.

Unknown versions fail closed.
No silent downgrade is permitted.
No incompatible artifact may become authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FingerprintCompatibilityError(RuntimeError):
    """Base compatibility error."""


class FingerprintCompatibilityValidationError(
    FingerprintCompatibilityError
):
    """Raised when compatibility input is invalid."""


class CompatibilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FingerprintCompatibilityResult:
    """Machine-readable compatibility result."""

    artifact: str
    version: str
    status: CompatibilityStatus
    accepted: bool
    migration_required: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "artifact": self.artifact,
            "version": self.version,
            "status": self.status.value,
            "accepted": self.accepted,
            "migration_required": self.migration_required,
            "reason": self.reason,
        }


class FingerprintCompatibilityEngine:
    """Explicit compatibility matrix for T09."""

    CURRENT_SCHEMA_VERSION = "1.0"
    CURRENT_IDENTITY_VERSION = "T09-IDENTITY-1.0"
    CURRENT_PROVENANCE_VERSION = "T09-PROVENANCE-1.0"

    @classmethod
    def check_schema(
        cls,
        version: str,
    ) -> FingerprintCompatibilityResult:
        return cls._check(
            "schema",
            version,
            {
                cls.CURRENT_SCHEMA_VERSION:
                    CompatibilityStatus.SUPPORTED,
            },
        )

    @classmethod
    def check_identity(
        cls,
        version: str,
    ) -> FingerprintCompatibilityResult:
        return cls._check(
            "identity",
            version,
            {
                cls.CURRENT_IDENTITY_VERSION:
                    CompatibilityStatus.SUPPORTED,
            },
        )

    @classmethod
    def check_provenance(
        cls,
        version: str,
    ) -> FingerprintCompatibilityResult:
        return cls._check(
            "provenance",
            version,
            {
                cls.CURRENT_PROVENANCE_VERSION:
                    CompatibilityStatus.SUPPORTED,
            },
        )

    @classmethod
    def _check(
        cls,
        artifact: str,
        version: str,
        supported: dict[str, CompatibilityStatus],
    ) -> FingerprintCompatibilityResult:
        if not isinstance(version, str) or not version:
            raise FingerprintCompatibilityValidationError(
                "Version must be a non-empty string."
            )

        status = supported.get(
            version,
            CompatibilityStatus.UNKNOWN,
        )

        if status == CompatibilityStatus.SUPPORTED:
            return FingerprintCompatibilityResult(
                artifact=artifact,
                version=version,
                status=status,
                accepted=True,
                migration_required=False,
                reason="Version is explicitly supported.",
            )

        if status == CompatibilityStatus.MIGRATABLE:
            return FingerprintCompatibilityResult(
                artifact=artifact,
                version=version,
                status=status,
                accepted=True,
                migration_required=True,
                reason="Version requires explicit migration.",
            )

        if status == CompatibilityStatus.INCOMPATIBLE:
            return FingerprintCompatibilityResult(
                artifact=artifact,
                version=version,
                status=status,
                accepted=False,
                migration_required=False,
                reason="Version is explicitly incompatible.",
            )

        return FingerprintCompatibilityResult(
            artifact=artifact,
            version=version,
            status=CompatibilityStatus.UNKNOWN,
            accepted=False,
            migration_required=False,
            reason="Unknown version; fail closed.",
        )

    @classmethod
    def validate_all(
        cls,
        schema_version: str,
        identity_version: str,
        provenance_version: str,
    ) -> tuple[FingerprintCompatibilityResult, ...]:
        results = (
            cls.check_schema(schema_version),
            cls.check_identity(identity_version),
            cls.check_provenance(provenance_version),
        )

        if not all(
            result.accepted
            for result in results
        ):
            raise FingerprintCompatibilityError(
                "T09 compatibility validation failed."
            )

        return results


__all__ = [
    "CompatibilityStatus",
    "FingerprintCompatibilityError",
    "FingerprintCompatibilityValidationError",
    "FingerprintCompatibilityResult",
    "FingerprintCompatibilityEngine",
]