from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_release import CommissionRelease
from .commission_release_snapshot import (
    CommissionReleaseSnapshot,
)


class CommissionReleaseIntegrityError(
    ValueError
):
    """Financial release integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionReleaseIntegrityReport:
    valid: bool
    release_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "release_fingerprint": (
                self.release_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    release: CommissionRelease,
    snapshot: CommissionReleaseSnapshot,
) -> CommissionReleaseIntegrityReport:
    if not isinstance(
        release,
        CommissionRelease,
    ):
        raise CommissionReleaseIntegrityError(
            "release must be CommissionRelease."
        )

    if not isinstance(
        snapshot,
        CommissionReleaseSnapshot,
    ):
        raise CommissionReleaseIntegrityError(
            "snapshot must be CommissionReleaseSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        release.immutable_fingerprint
    )

    if (
        release.release_id
        != snapshot.release_id
    ):
        reasons.append(
            "release_id mismatch"
        )

    if (
        release.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        release.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        release.statement_id
        != snapshot.statement_id
    ):
        reasons.append(
            "statement_id mismatch"
        )

    if (
        release.release_version
        != snapshot.release_version
    ):
        reasons.append(
            "release_version mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionReleaseSnapshot.from_release(
            release
        )
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "release does not match snapshot"
        )

    return CommissionReleaseIntegrityReport(
        valid=not reasons,
        release_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    release: CommissionRelease,
    snapshot: CommissionReleaseSnapshot,
) -> None:
    report = inspect_integrity(
        release,
        snapshot,
    )

    if not report.valid:
        raise CommissionReleaseIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionReleaseIntegrityError",
    "CommissionReleaseIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
