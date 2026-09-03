"""ACRL T02 — Architecture Drift Detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .architecture_lock import (
    ArchitectureDriftError,
    ArchitectureLockReader,
)


class ArchitectureDriftStatus(str, Enum):
    """Canonical T02 drift states."""

    UNCHANGED = "UNCHANGED"
    DRIFTED = "DRIFTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ArchitectureDriftReport:
    """Immutable result of an architecture drift check."""

    status: ArchitectureDriftStatus
    expected_fingerprint: str
    current_fingerprint: str | None
    reason: str

    @property
    def safe(self) -> bool:
        return self.status == ArchitectureDriftStatus.UNCHANGED

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "expected_fingerprint": self.expected_fingerprint,
            "current_fingerprint": self.current_fingerprint,
            "reason": self.reason,
            "safe": self.safe,
        }


def detect_architecture_drift(
    expected_fingerprint: str,
    reader: ArchitectureLockReader | None = None,
) -> ArchitectureDriftReport:
    """Compare expected architecture fingerprint with current authority."""

    if not isinstance(expected_fingerprint, str):
        raise TypeError(
            "expected_fingerprint must be a string."
        )

    expected = expected_fingerprint.strip()

    if not expected:
        raise ValueError(
            "expected_fingerprint cannot be empty."
        )

    active_reader = (
        reader
        if reader is not None
        else ArchitectureLockReader()
    )

    try:
        current = active_reader.verify_fingerprint(
            expected
        )
    except ArchitectureDriftError as exc:
        try:
            current = active_reader.read()
        except Exception as read_exc:
            return ArchitectureDriftReport(
                status=ArchitectureDriftStatus.UNAVAILABLE,
                expected_fingerprint=expected,
                current_fingerprint=None,
                reason=str(read_exc),
            )

        return ArchitectureDriftReport(
            status=ArchitectureDriftStatus.DRIFTED,
            expected_fingerprint=expected,
            current_fingerprint=(
                current.architecture_fingerprint
            ),
            reason=str(exc),
        )
    except Exception as exc:
        return ArchitectureDriftReport(
            status=ArchitectureDriftStatus.UNAVAILABLE,
            expected_fingerprint=expected,
            current_fingerprint=None,
            reason=str(exc),
        )

    return ArchitectureDriftReport(
        status=ArchitectureDriftStatus.UNCHANGED,
        expected_fingerprint=expected,
        current_fingerprint=(
            current.architecture_fingerprint
        ),
        reason="Architecture fingerprint matches.",
    )


__all__ = [
    "ArchitectureDriftReport",
    "ArchitectureDriftStatus",
    "detect_architecture_drift",
]
