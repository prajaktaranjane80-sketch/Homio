"""Authoritative REOS inventory indexing hooks for CORE-004-T07.

T07 owns the indexing projection/hook boundary for Inventory.

The canonical Inventory aggregate remains authoritative for:
    - inventory identity
    - tenant/project scope
    - inventory type
    - lifecycle
    - availability
    - version

This module does NOT mutate Inventory and does NOT persist an index.

It produces deterministic, persistence-neutral indexing documents that
downstream search/index infrastructure can consume.

History/evidence, verification, consistency, concurrency, and persistence
remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .inventory import Inventory


class InventoryIndexingError(ValueError):
    """Base error for inventory indexing failures."""


class InventoryIndexScopeError(InventoryIndexingError):
    """Raised when an indexing request violates tenant/project scope."""


class InventoryIndexStaleVersionError(InventoryIndexingError):
    """Raised when an indexing request targets a stale inventory version."""


class InventoryIndexDocumentError(InventoryIndexingError):
    """Raised when an index document is structurally invalid."""


class InventoryIndexOperation(str, Enum):
    UPSERT = "UPSERT"
    DELETE = "DELETE"


@dataclass(frozen=True)
class InventoryIndexDocument:
    """Immutable persistence-neutral inventory index projection."""

    index_key: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_code: str
    inventory_type: str
    name: str
    lifecycle: str
    availability: str
    inventory_version: int
    operation: InventoryIndexOperation
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        required = (
            "index_key",
            "inventory_id",
            "tenant_id",
            "project_id",
            "inventory_code",
            "inventory_type",
            "name",
            "lifecycle",
            "availability",
        )

        for field_name in required:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InventoryIndexDocumentError(
                    f"{field_name} is required."
                )

        if self.inventory_version < 1:
            raise InventoryIndexDocumentError(
                "inventory_version must be >= 1."
            )

        object.__setattr__(
            self,
            "operation",
            InventoryIndexOperation(self.operation),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical serializable indexing document."""

        return {
            "index_key": self.index_key,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_code": self.inventory_code,
            "inventory_type": self.inventory_type,
            "name": self.name,
            "lifecycle": self.lifecycle,
            "availability": self.availability,
            "inventory_version": self.inventory_version,
            "operation": self.operation.value,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class InventoryIndexingHook:
    """Deterministic indexing hook for the canonical Inventory aggregate."""

    index_name: str = "reos_inventory"

    def _assert_scope(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
    ) -> None:
        if tenant_id != inventory.tenant_id:
            raise InventoryIndexScopeError(
                "Inventory indexing request belongs to a different tenant."
            )

        if project_id != inventory.project_id:
            raise InventoryIndexScopeError(
                "Inventory indexing request belongs to a different project."
            )

    def _assert_version(
        self,
        inventory: Inventory,
        *,
        expected_version: int | None,
    ) -> None:
        if expected_version is None:
            return

        if expected_version < 1:
            raise InventoryIndexStaleVersionError(
                "expected_version must be >= 1."
            )

        if expected_version != inventory.version:
            raise InventoryIndexStaleVersionError(
                "Inventory indexing request targets a stale inventory version."
            )

    def build_upsert(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
        expected_version: int | None = None,
    ) -> InventoryIndexDocument:
        """Build an UPSERT projection without mutating Inventory."""

        self._assert_scope(
            inventory,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        self._assert_version(
            inventory,
            expected_version=expected_version,
        )

        return InventoryIndexDocument(
            index_key=inventory.identity_key,
            inventory_id=inventory.inventory_id,
            tenant_id=inventory.tenant_id,
            project_id=inventory.project_id,
            inventory_code=inventory.inventory_code,
            inventory_type=inventory.inventory_type.value,
            name=inventory.name,
            lifecycle=inventory.lifecycle.value,
            availability=inventory.availability.value,
            inventory_version=inventory.version,
            operation=InventoryIndexOperation.UPSERT,
            payload={
                "index_name": self.index_name,
                "identity_key": inventory.identity_key,
                "inventory_id": inventory.inventory_id,
                "tenant_id": inventory.tenant_id,
                "project_id": inventory.project_id,
                "inventory_code": inventory.inventory_code,
                "inventory_type": inventory.inventory_type.value,
                "name": inventory.name,
                "lifecycle": inventory.lifecycle.value,
                "availability": inventory.availability.value,
                "inventory_version": inventory.version,
                "metadata": dict(inventory.metadata),
            },
        )

    def build_delete(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
        expected_version: int | None = None,
    ) -> InventoryIndexDocument:
        """Build a DELETE projection without mutating Inventory."""

        self._assert_scope(
            inventory,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        self._assert_version(
            inventory,
            expected_version=expected_version,
        )

        return InventoryIndexDocument(
            index_key=inventory.identity_key,
            inventory_id=inventory.inventory_id,
            tenant_id=inventory.tenant_id,
            project_id=inventory.project_id,
            inventory_code=inventory.inventory_code,
            inventory_type=inventory.inventory_type.value,
            name=inventory.name,
            lifecycle=inventory.lifecycle.value,
            availability=inventory.availability.value,
            inventory_version=inventory.version,
            operation=InventoryIndexOperation.DELETE,
            payload={
                "index_name": self.index_name,
                "identity_key": inventory.identity_key,
                "inventory_id": inventory.inventory_id,
                "tenant_id": inventory.tenant_id,
                "project_id": inventory.project_id,
                "inventory_version": inventory.version,
            },
        )


def build_inventory_index(
    inventory: Inventory,
    *,
    tenant_id: str,
    project_id: str,
    expected_version: int | None = None,
) -> InventoryIndexDocument:
    """Convenience API for producing an inventory UPSERT projection."""

    return InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id=tenant_id,
        project_id=project_id,
        expected_version=expected_version,
    )


def build_inventory_index_delete(
    inventory: Inventory,
    *,
    tenant_id: str,
    project_id: str,
    expected_version: int | None = None,
) -> InventoryIndexDocument:
    """Convenience API for producing an inventory DELETE projection."""

    return InventoryIndexingHook().build_delete(
        inventory,
        tenant_id=tenant_id,
        project_id=project_id,
        expected_version=expected_version,
    )


__all__ = [
    "InventoryIndexDocument",
    "InventoryIndexDocumentError",
    "InventoryIndexOperation",
    "InventoryIndexScopeError",
    "InventoryIndexStaleVersionError",
    "InventoryIndexingError",
    "InventoryIndexingHook",
    "build_inventory_index",
    "build_inventory_index_delete",
]