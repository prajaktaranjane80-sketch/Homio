from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_closeout import CommissionCloseout


@dataclass(frozen=True, slots=True)
class CommissionCloseoutSnapshot:
    closeout_id: str
    tenant_id: str
    commission_id: str
    statement_id: str
    closeout_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_closeout(
        cls,
        closeout: CommissionCloseout,
    ) -> "CommissionCloseoutSnapshot":
        if not isinstance(
            closeout,
            CommissionCloseout,
        ):
            raise TypeError(
                "closeout must be CommissionCloseout."
            )

        payload = closeout.to_dict(
            include_fingerprint=False
        )

        return cls(
            closeout_id=closeout.closeout_id,
            tenant_id=closeout.tenant_id,
            commission_id=closeout.commission_id,
            statement_id=closeout.statement_id,
            closeout_version=(
                closeout.closeout_version
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
            "closeout_id": self.closeout_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "statement_id": self.statement_id,
            "closeout_version": (
                self.closeout_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionCloseoutSnapshot",
]
