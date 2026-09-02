"""Authoritative REOS inventory history capability for CORE-004-T06.

T06 owns immutable inventory history records.

The canonical Inventory aggregate remains authoritative for the current
inventory state. This module records historical snapshots/revisions without
mutating Inventory.

No persistence implementation is included here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from .inventory import Inventory


class InventoryHistoryError(ValueError):
    """Base error for inventory history failures."""


class InventoryHistoryScopeError(InventoryHistoryError):
    """Raised when a history record is used outside its inventory scope."""


class InventoryHistoryVersionError(InventoryHistoryError):
    """Raised when history versions are invalid or inconsistent."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class InventoryHistoryEvent:
    """Persistence-neutral history event."""

    event_id: str
    event_type: str
    history_id: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "history_id": self.history_id,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class InventoryHistory:
    """Immutable historical representation of an Inventory version."""

    history_id: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    recorded_at: str
    snapshot: Mapping[str, Any]
    event_type: str = "INVENTORY_HISTORY_RECORDED"
    source_of_truth: str = "inventory_history"

    @classmethod
    def from_inventory(
        cls,
        inventory: Inventory,
        *,
        at: str | None = None,
        history_id: str | None = None,
        event_type: str = "INVENTORY_HISTORY_RECORDED",
    ) -> "InventoryHistory":
        timestamp = at or _utc_now()

        return cls(
            history_id=history_id or str(uuid4()),
            inventory_id=inventory.inventory_id,
            tenant_id=inventory.tenant_id,
            project_id=inventory.project_id,
            inventory_version=inventory.version,
            recorded_at=timestamp,
            snapshot=dict(inventory.to_dict()),
            event_type=event_type,
        )

    def assert_scope(
        self,
        *,
        tenant_id: str,
        project_id: str,
        inventory_id: str,
    ) -> None:
        if tenant_id != self.tenant_id:
            raise InventoryHistoryScopeError(
                "History belongs to a different tenant."
            )

        if project_id != self.project_id:
            raise InventoryHistoryScopeError(
                "History belongs to a different project."
            )

        if inventory_id != self.inventory_id:
            raise InventoryHistoryScopeError(
                "History belongs to a different inventory."
            )

    def assert_matches_inventory(self, inventory: Inventory) -> None:
        self.assert_scope(
            tenant_id=inventory.tenant_id,
            project_id=inventory.project_id,
            inventory_id=inventory.inventory_id,
        )

        if self.inventory_version != inventory.version:
            raise InventoryHistoryVersionError(
                "History version does not match the supplied inventory version."
            )

    def to_event(self) -> InventoryHistoryEvent:
        return InventoryHistoryEvent(
            event_id=str(uuid4()),
            event_type=self.event_type,
            history_id=self.history_id,
            inventory_id=self.inventory_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            inventory_version=self.inventory_version,
            occurred_at=self.recorded_at,
            payload={
                "history_id": self.history_id,
                "inventory_version": self.inventory_version,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "recorded_at": self.recorded_at,
            "snapshot": dict(self.snapshot),
            "event_type": self.event_type,
            "source_of_truth": self.source_of_truth,
        }


__all__ = [
    "InventoryHistory",
    "InventoryHistoryError",
    "InventoryHistoryEvent",
    "InventoryHistoryScopeError",
    "InventoryHistoryVersionError",
]