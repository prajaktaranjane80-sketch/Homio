"""ACRL T11 — Recovery compatibility."""

from __future__ import annotations

from enum import Enum


class RecoveryCompatibilityError(RuntimeError):
    """Recovery compatibility failure."""


class RecoveryCompatibilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class RecoveryCompatibilityEngine:
    """Fail-closed compatibility rules."""

    CURRENT_SCHEMA = "1.0"
    CURRENT_POLICY = "T11-POLICY-1.0"
    CURRENT_IDENTITY = "T11-IDENTITY-1.0"
    CURRENT_PROVENANCE = "T11-PROVENANCE-1.0"

    @classmethod
    def check(
        cls,
        *,
        schema_version: str,
        policy_version: str,
        identity_version: str,
        provenance_version: str,
    ) -> RecoveryCompatibilityStatus:
        versions = {
            schema_version,
            policy_version,
            identity_version,
            provenance_version,
        }

        if not all(
            isinstance(value, str) and value.strip()
            for value in versions
        ):
            return RecoveryCompatibilityStatus.UNKNOWN

        if schema_version != cls.CURRENT_SCHEMA:
            return RecoveryCompatibilityStatus.INCOMPATIBLE

        if policy_version != cls.CURRENT_POLICY:
            return RecoveryCompatibilityStatus.INCOMPATIBLE

        if identity_version != cls.CURRENT_IDENTITY:
            return RecoveryCompatibilityStatus.INCOMPATIBLE

        if provenance_version != cls.CURRENT_PROVENANCE:
            return RecoveryCompatibilityStatus.INCOMPATIBLE

        return RecoveryCompatibilityStatus.SUPPORTED

    @classmethod
    def require_supported(
        cls,
        **kwargs: str,
    ) -> bool:
        status = cls.check(**kwargs)

        if status != RecoveryCompatibilityStatus.SUPPORTED:
            raise RecoveryCompatibilityError(
                f"Recovery compatibility status: {status.value}"
            )

        return True


__all__ = [
    "RecoveryCompatibilityEngine",
    "RecoveryCompatibilityError",
    "RecoveryCompatibilityStatus",
]