"""ACRL T01 — Project DNA schema compatibility."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


COMPATIBILITY_SCHEMA_VERSION = "1.0"


class CompatibilityStatus(str, Enum):
    """Machine-readable compatibility status."""

    SUPPORTED = "SUPPORTED"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    FUTURE_VERSION = "FUTURE_VERSION"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CompatibilityResult:
    """Compatibility decision for an incoming state/DNA version."""

    status: CompatibilityStatus
    current_version: int
    supported_minimum: int
    supported_maximum: int
    reason: str
    schema_version: str = COMPATIBILITY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "current_version": self.current_version,
            "supported_minimum": self.supported_minimum,
            "supported_maximum": self.supported_maximum,
            "reason": self.reason,
        }


def evaluate_state_schema_compatibility(
    version: int,
    *,
    supported_minimum: int = 3,
    supported_maximum: int = 3,
) -> CompatibilityResult:
    """Evaluate state schema compatibility without performing migration."""

    if version < supported_minimum:
        return CompatibilityResult(
            status=CompatibilityStatus.MIGRATION_REQUIRED,
            current_version=version,
            supported_minimum=supported_minimum,
            supported_maximum=supported_maximum,
            reason="State schema is older than the supported minimum.",
        )

    if version > supported_maximum:
        return CompatibilityResult(
            status=CompatibilityStatus.FUTURE_VERSION,
            current_version=version,
            supported_minimum=supported_minimum,
            supported_maximum=supported_maximum,
            reason="State schema is newer than the supported maximum.",
        )

    return CompatibilityResult(
        status=CompatibilityStatus.SUPPORTED,
        current_version=version,
        supported_minimum=supported_minimum,
        supported_maximum=supported_maximum,
        reason="State schema is supported.",
    )


__all__ = [
    "COMPATIBILITY_SCHEMA_VERSION",
    "CompatibilityResult",
    "CompatibilityStatus",
    "evaluate_state_schema_compatibility",
]