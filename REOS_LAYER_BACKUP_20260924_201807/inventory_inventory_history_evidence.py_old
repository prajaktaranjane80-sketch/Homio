"""REOS CORE-004-T06 history/evidence linking capability.

This module links immutable inventory history with immutable evidence
references. It does not mutate Inventory, Verification, History, or Evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from .inventory_evidence import InventoryEvidence
from .inventory_history import InventoryHistory


class InventoryHistoryEvidenceError(ValueError):
    """Base error for history/evidence linking failures."""


class InventoryHistoryEvidenceScopeError(InventoryHistoryEvidenceError):
    """Raised when history and evidence cannot share canonical scope."""


class InventoryHistoryEvidenceVersionError(InventoryHistoryEvidenceError):
    """Raised when history and evidence versions do not match."""


@dataclass(frozen=True)
class InventoryHistoryEvidenceLink:
    """Immutable relationship between one history record and one evidence."""

    link_id: str
    history_id: str
    evidence_id: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    created_at: str
    metadata: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        history: InventoryHistory,
        evidence: InventoryEvidence,
        *,
        at: str,
        link_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "InventoryHistoryEvidenceLink":
        if history.inventory_id != evidence.inventory_id:
            raise InventoryHistoryEvidenceScopeError(
                "History and evidence reference different inventories."
            )

        if history.tenant_id != evidence.tenant_id:
            raise InventoryHistoryEvidenceScopeError(
                "History and evidence reference different tenants."
            )

        if history.project_id != evidence.project_id:
            raise InventoryHistoryEvidenceScopeError(
                "History and evidence reference different projects."
            )

        if history.inventory_version != evidence.inventory_version:
            raise InventoryHistoryEvidenceVersionError(
                "History and evidence reference different inventory versions."
            )

        return cls(
            link_id=link_id or str(uuid4()),
            history_id=history.history_id,
            evidence_id=evidence.evidence_id,
            inventory_id=history.inventory_id,
            tenant_id=history.tenant_id,
            project_id=history.project_id,
            inventory_version=history.inventory_version,
            created_at=at,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "link_id": self.link_id,
            "history_id": self.history_id,
            "evidence_id": self.evidence_id,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "InventoryHistoryEvidenceError",
    "InventoryHistoryEvidenceLink",
    "InventoryHistoryEvidenceScopeError",
    "InventoryHistoryEvidenceVersionError",
]