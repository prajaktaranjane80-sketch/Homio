from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_closeout import CommissionCloseout


class CommissionCloseoutHistoryError(
    ValueError
):
    """Invalid closeout history."""


@dataclass(frozen=True, slots=True)
class CommissionCloseoutHistoryEntry:
    closeout_id: str
    tenant_id: str
    commission_id: str
    statement_id: str
    closeout_version: int
    state: str
    closeout_fingerprint: str

    @classmethod
    def from_closeout(
        cls,
        closeout: CommissionCloseout,
    ) -> "CommissionCloseoutHistoryEntry":
        if not isinstance(
            closeout,
            CommissionCloseout,
        ):
            raise CommissionCloseoutHistoryError(
                "closeout must be CommissionCloseout."
            )

        return cls(
            closeout_id=closeout.closeout_id,
            tenant_id=closeout.tenant_id,
            commission_id=closeout.commission_id,
            statement_id=closeout.statement_id,
            closeout_version=(
                closeout.closeout_version
            ),
            state=closeout.state.value,
            closeout_fingerprint=(
                closeout.immutable_fingerprint
            ),
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
            "state": self.state,
            "closeout_fingerprint": (
                self.closeout_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionCloseoutHistory:
    entries: tuple[
        CommissionCloseoutHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        closeout: CommissionCloseout,
    ) -> "CommissionCloseoutHistory":
        entry = (
            CommissionCloseoutHistoryEntry
            .from_closeout(closeout)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.closeout_id
                != entry.closeout_id
            ):
                raise CommissionCloseoutHistoryError(
                    "Closeout history identity mismatch."
                )

            if (
                entry.closeout_version
                != latest.closeout_version + 1
            ):
                if (
                    entry.closeout_version
                    == latest.closeout_version
                    and entry.closeout_fingerprint
                    == latest.closeout_fingerprint
                ):
                    return self

                raise CommissionCloseoutHistoryError(
                    "Closeout versions must advance sequentially."
                )

        elif entry.closeout_version != 1:
            raise CommissionCloseoutHistoryError(
                "First closeout version must be 1."
            )

        return CommissionCloseoutHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionCloseoutHistoryEntry | None:
        return (
            self.entries[-1]
            if self.entries
            else None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }


__all__ = [
    "CommissionCloseoutHistoryError",
    "CommissionCloseoutHistoryEntry",
    "CommissionCloseoutHistory",
]
