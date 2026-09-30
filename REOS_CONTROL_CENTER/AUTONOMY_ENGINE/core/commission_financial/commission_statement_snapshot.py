from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_statement import CommissionStatement


@dataclass(frozen=True, slots=True)
class CommissionStatementSnapshot:
    statement_id: str
    tenant_id: str
    commission_id: str
    statement_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_statement(
        cls,
        statement: CommissionStatement,
    ) -> "CommissionStatementSnapshot":
        if not isinstance(
            statement,
            CommissionStatement,
        ):
            raise TypeError(
                "statement must be CommissionStatement."
            )

        payload = statement.to_dict(
            include_fingerprint=False
        )

        return cls(
            statement_id=statement.statement_id,
            tenant_id=statement.tenant_id,
            commission_id=statement.commission_id,
            statement_version=(
                statement.statement_version
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
            "statement_id": self.statement_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "statement_version": (
                self.statement_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionStatementSnapshot",
]
