"""Authoritative REOS inventory concurrency capability for CORE-004-T09.

T09 owns optimistic concurrency review and stale-write protection.

The canonical Inventory aggregate remains authoritative for:
    - inventory identity
    - tenant/project scope
    - inventory type
    - lifecycle
    - availability
    - canonical version

This module does NOT mutate Inventory.

It provides a persistence-neutral concurrency boundary that validates
a caller's expected inventory version before an operation is allowed
to proceed.

History/evidence, verification, indexing, consistency, persistence and
transaction orchestration remain owned by their dedicated modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .inventory import Inventory


class InventoryConcurrencyError(ValueError):
    """Base error for inventory concurrency failures."""


class InventoryConcurrencyScopeError(InventoryConcurrencyError):
    """Raised when a concurrency request crosses tenant/project scope."""


class InventoryStaleWriteError(InventoryConcurrencyError):
    """Raised when an operation targets a stale inventory version."""


class InventoryInvalidExpectedVersionError(InventoryConcurrencyError):
    """Raised when an expected version is structurally invalid."""


class InventoryConcurrencyOperation(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    TRANSITION = "TRANSITION"
    INDEX = "INDEX"


@dataclass(frozen=True)
class InventoryConcurrencyReceipt:
    """Immutable result of a successful optimistic concurrency check."""

    inventory_id: str
    tenant_id: str
    project_id: str
    operation: InventoryConcurrencyOperation
    expected_version: int
    current_version: int

    @property
    def is_current(self) -> bool:
        return self.expected_version == self.current_version

    def to_dict(self) -> dict[str, object]:
        return {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "operation": self.operation.value,
            "expected_version": self.expected_version,
            "current_version": self.current_version,
            "is_current": self.is_current,
        }


@dataclass(frozen=True)
class InventoryConcurrencyGuard:
    """Persistence-neutral optimistic concurrency guard."""

    def assert_current(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
        expected_version: int,
        operation: InventoryConcurrencyOperation = (
            InventoryConcurrencyOperation.WRITE
        ),
    ) -> InventoryConcurrencyReceipt:
        """Validate scope and require an exact inventory version match."""

        if tenant_id != inventory.tenant_id:
            raise InventoryConcurrencyScopeError(
                "Inventory concurrency request belongs to a different tenant."
            )

        if project_id != inventory.project_id:
            raise InventoryConcurrencyScopeError(
                "Inventory concurrency request belongs to a different project."
            )

        if (
            isinstance(expected_version, bool)
            or not isinstance(expected_version, int)
            or expected_version < 1
        ):
            raise InventoryInvalidExpectedVersionError(
                "expected_version must be an integer >= 1."
            )

        operation = InventoryConcurrencyOperation(operation)

        if expected_version != inventory.version:
            raise InventoryStaleWriteError(
                "Inventory operation targets a stale inventory version: "
                f"expected {expected_version}, "
                f"current {inventory.version}."
            )

        return InventoryConcurrencyReceipt(
            inventory_id=inventory.inventory_id,
            tenant_id=inventory.tenant_id,
            project_id=inventory.project_id,
            operation=operation,
            expected_version=expected_version,
            current_version=inventory.version,
        )


def assert_inventory_version(
    inventory: Inventory,
    *,
    tenant_id: str,
    project_id: str,
    expected_version: int,
    operation: InventoryConcurrencyOperation = (
        InventoryConcurrencyOperation.WRITE
    ),
) -> InventoryConcurrencyReceipt:
    """Convenience API for optimistic inventory concurrency validation."""

    return InventoryConcurrencyGuard().assert_current(
        inventory,
        tenant_id=tenant_id,
        project_id=project_id,
        expected_version=expected_version,
        operation=operation,
    )


__all__ = [
    "InventoryConcurrencyError",
    "InventoryConcurrencyGuard",
    "InventoryConcurrencyOperation",
    "InventoryConcurrencyReceipt",
    "InventoryConcurrencyScopeError",
    "InventoryInvalidExpectedVersionError",
    "InventoryStaleWriteError",
    "assert_inventory_version",
]