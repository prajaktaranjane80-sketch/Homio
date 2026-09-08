"""
ACRL T15 — Operator Compatibility.
"""

from __future__ import annotations

from enum import Enum


class OperatorCompatibilityStatus(str, Enum):
    """Canonical compatibility states."""

    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class OperatorCompatibilityError(ValueError):
    """Raised when compatibility requirements are not met."""


class OperatorCompatibilityEngine:
    """Deterministic T15 compatibility checks."""

    CURRENT_SCHEMA_VERSION = "1.0"
    CURRENT_POLICY_VERSION = "T15-POLICY-1.0"
    CURRENT_IDENTITY_VERSION = "T15-IDENTITY-1.0"
    CURRENT_PROVENANCE_VERSION = "T15-PROVENANCE-1.0"

    @classmethod
    def _status(
        cls,
        version: str,
        current_version: str,
    ) -> OperatorCompatibilityStatus:
        if not isinstance(version, str) or not version:
            return OperatorCompatibilityStatus.UNKNOWN

        if version == current_version:
            return OperatorCompatibilityStatus.SUPPORTED

        return OperatorCompatibilityStatus.INCOMPATIBLE

    @classmethod
    def schema_status(
        cls,
        version: str,
    ) -> OperatorCompatibilityStatus:
        return cls._status(
            version,
            cls.CURRENT_SCHEMA_VERSION,
        )

    @classmethod
    def policy_status(
        cls,
        version: str,
    ) -> OperatorCompatibilityStatus:
        return cls._status(
            version,
            cls.CURRENT_POLICY_VERSION,
        )

    @classmethod
    def identity_status(
        cls,
        version: str,
    ) -> OperatorCompatibilityStatus:
        return cls._status(
            version,
            cls.CURRENT_IDENTITY_VERSION,
        )

    @classmethod
    def provenance_status(
        cls,
        version: str,
    ) -> OperatorCompatibilityStatus:
        return cls._status(
            version,
            cls.CURRENT_PROVENANCE_VERSION,
        )

    @classmethod
    def require_supported(
        cls,
        status: OperatorCompatibilityStatus,
    ) -> None:
        if status is not OperatorCompatibilityStatus.SUPPORTED:
            raise OperatorCompatibilityError(
                f"T15 compatibility rejected: {status.value}"
            )

    @classmethod
    def is_compatible(
        cls,
        status: OperatorCompatibilityStatus,
    ) -> bool:
        return status in {
            OperatorCompatibilityStatus.SUPPORTED,
            OperatorCompatibilityStatus.MIGRATABLE,
        }


__all__ = [
    "OperatorCompatibilityEngine",
    "OperatorCompatibilityError",
    "OperatorCompatibilityStatus",
]
