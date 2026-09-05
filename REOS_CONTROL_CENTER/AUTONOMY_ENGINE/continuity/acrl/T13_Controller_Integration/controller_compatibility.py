"""ACRL T13 — Controller Integration Compatibility."""

from enum import Enum


class ControllerCompatibilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class ControllerCompatibilityError(ValueError):
    """Raised when T13 compatibility requirements are not satisfied."""


class ControllerCompatibilityEngine:
    CURRENT_SCHEMA_VERSION = "1.0"
    CURRENT_POLICY_VERSION = "T13-POLICY-1.0"
    CURRENT_IDENTITY_VERSION = "T13-IDENTITY-1.0"
    CURRENT_PROVENANCE_VERSION = "T13-PROVENANCE-1.0"

    @classmethod
    def _status(
        cls,
        version: str,
        current_version: str,
    ) -> ControllerCompatibilityStatus:
        if version == current_version:
            return ControllerCompatibilityStatus.SUPPORTED

        if not isinstance(version, str) or not version:
            return ControllerCompatibilityStatus.UNKNOWN

        return ControllerCompatibilityStatus.INCOMPATIBLE

    @classmethod
    def schema_status(cls, version: str) -> ControllerCompatibilityStatus:
        return cls._status(version, cls.CURRENT_SCHEMA_VERSION)

    @classmethod
    def policy_status(cls, version: str) -> ControllerCompatibilityStatus:
        return cls._status(version, cls.CURRENT_POLICY_VERSION)

    @classmethod
    def identity_status(cls, version: str) -> ControllerCompatibilityStatus:
        return cls._status(version, cls.CURRENT_IDENTITY_VERSION)

    @classmethod
    def provenance_status(
        cls,
        version: str,
    ) -> ControllerCompatibilityStatus:
        return cls._status(version, cls.CURRENT_PROVENANCE_VERSION)

    @classmethod
    def require_supported(
        cls,
        status: ControllerCompatibilityStatus,
    ) -> None:
        if status is not ControllerCompatibilityStatus.SUPPORTED:
            raise ControllerCompatibilityError(
                f"T13 compatibility rejected: {status.value}"
            )

    @classmethod
    def is_compatible(
        cls,
        status: ControllerCompatibilityStatus,
    ) -> bool:
        return status in {
            ControllerCompatibilityStatus.SUPPORTED,
            ControllerCompatibilityStatus.MIGRATABLE,
        }