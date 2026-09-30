from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_release import CommissionRelease


@dataclass(frozen=True, slots=True)
class CommissionReleaseSnapshot:
    release_id: str
    tenant_id: str
    commission_id: str
    statement_id: str
    release_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_release(
        cls,
        release: CommissionRelease,
    ) -> "CommissionReleaseSnapshot":
        if not isinstance(
            release,
            CommissionRelease,
        ):
            raise TypeError(
                "release must be CommissionRelease."
            )

        payload = release.to_dict(
            include_fingerprint=False
        )

        return cls(
            release_id=release.release_id,
            tenant_id=release.tenant_id,
            commission_id=release.commission_id,
            statement_id=release.statement_id,
            release_version=(
                release.release_version
            ),
            canonical_payload=payload,
            snapshot_fingerprint=fingerprint(
                payload
            ),
        )

    def verify(self) -> bool:
        return (
            self.snapshot_fingerprint
            == fingerprint(
                self.canonical_payload
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "statement_id": self.statement_id,
            "release_version": (
                self.release_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionReleaseSnapshot",
]
