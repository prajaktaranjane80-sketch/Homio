from enum import Enum


class ResumeCompatibilityStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    MIGRATABLE = "MIGRATABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class ResumeCompatibilityError(ValueError):
    pass


class ResumeCompatibilityEngine:
    CURRENT_SCHEMA_VERSION = "1.0"
    CURRENT_POLICY_VERSION = "T12-POLICY-1.0"
    CURRENT_IDENTITY_VERSION = "T12-IDENTITY-1.0"
    CURRENT_PROVENANCE_VERSION = "T12-PROVENANCE-1.0"

    @classmethod
    def schema_status(cls, version: str) -> ResumeCompatibilityStatus:
        if version == cls.CURRENT_SCHEMA_VERSION:
            return ResumeCompatibilityStatus.SUPPORTED

        if not isinstance(version, str) or not version:
            return ResumeCompatibilityStatus.UNKNOWN

        return ResumeCompatibilityStatus.INCOMPATIBLE

    @classmethod
    def policy_status(cls, version: str) -> ResumeCompatibilityStatus:
        if version == cls.CURRENT_POLICY_VERSION:
            return ResumeCompatibilityStatus.SUPPORTED

        if not isinstance(version, str) or not version:
            return ResumeCompatibilityStatus.UNKNOWN

        return ResumeCompatibilityStatus.INCOMPATIBLE

    @classmethod
    def identity_status(cls, version: str) -> ResumeCompatibilityStatus:
        if version == cls.CURRENT_IDENTITY_VERSION:
            return ResumeCompatibilityStatus.SUPPORTED

        if not isinstance(version, str) or not version:
            return ResumeCompatibilityStatus.UNKNOWN

        return ResumeCompatibilityStatus.INCOMPATIBLE

    @classmethod
    def provenance_status(cls, version: str) -> ResumeCompatibilityStatus:
        if version == cls.CURRENT_PROVENANCE_VERSION:
            return ResumeCompatibilityStatus.SUPPORTED

        if not isinstance(version, str) or not version:
            return ResumeCompatibilityStatus.UNKNOWN

        return ResumeCompatibilityStatus.INCOMPATIBLE

    @classmethod
    def require_supported(
        cls,
        status: ResumeCompatibilityStatus,
    ) -> None:
        if status is not ResumeCompatibilityStatus.SUPPORTED:
            raise ResumeCompatibilityError(
                f"Resume compatibility rejected: {status.value}"
            )

    @classmethod
    def is_compatible(
        cls,
        status: ResumeCompatibilityStatus,
    ) -> bool:
        return status in {
            ResumeCompatibilityStatus.SUPPORTED,
            ResumeCompatibilityStatus.MIGRATABLE,
        }