"""REOS CORE-004-T08 — Inventory Consistency Boundary.

T08 provides read-only consistency validation across the authoritative
Inventory aggregate and its capability projections.

This module does not mutate Inventory and does not replace any earlier
CORE-004 domain module.

Responsibilities:
    - tenant isolation invariants
    - project isolation invariants
    - inventory identity invariants
    - version invariants
    - lifecycle/availability representation invariants
    - event-to-inventory consistency
    - verification projection consistency
    - indexing projection consistency

Persistence, indexing execution, history persistence, verification
workflow and concurrency orchestration remain owned by their dedicated
modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .inventory import Inventory, InventoryEvent
from .inventory_indexing import InventoryIndexDocument
from .inventory_verification import InventoryVerification


class InventoryConsistencyError(ValueError):
    """Base error for inventory consistency violations."""


class InventoryConsistencyScopeError(InventoryConsistencyError):
    """Raised when tenant/project scope is inconsistent."""


class InventoryConsistencyIdentityError(InventoryConsistencyError):
    """Raised when inventory identity is inconsistent."""


class InventoryConsistencyVersionError(InventoryConsistencyError):
    """Raised when version relationships are inconsistent."""


class InventoryConsistencyProjectionError(InventoryConsistencyError):
    """Raised when a capability projection is inconsistent."""


class InventoryConsistencyInvariant(str, Enum):
    TENANT_SCOPE = "TENANT_SCOPE"
    PROJECT_SCOPE = "PROJECT_SCOPE"
    IDENTITY = "IDENTITY"
    VERSION = "VERSION"
    LIFECYCLE = "LIFECYCLE"
    AVAILABILITY = "AVAILABILITY"
    VERIFICATION = "VERIFICATION"
    INDEXING = "INDEXING"
    EVENT = "EVENT"


@dataclass(frozen=True)
class InventoryConsistencyResult:
    """Immutable result of a consistency validation."""

    valid: bool
    checked_invariants: tuple[InventoryConsistencyInvariant, ...]
    violations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "checked_invariants": [
                invariant.value for invariant in self.checked_invariants
            ],
            "violations": list(self.violations),
        }


@dataclass(frozen=True)
class InventoryConsistencyValidator:
    """Read-only validator for the Inventory aggregate and projections."""

    def validate_inventory(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
    ) -> InventoryConsistencyResult:
        """Validate the core Inventory invariants."""

        violations: list[str] = []

        if inventory.tenant_id != tenant_id:
            violations.append(
                "Inventory tenant scope does not match requested tenant."
            )

        if inventory.project_id != project_id:
            violations.append(
                "Inventory project scope does not match requested project."
            )

        if not inventory.inventory_id.strip():
            violations.append("Inventory identity is empty.")

        if inventory.identity_key != (
            f"{inventory.tenant_id}:"
            f"{inventory.project_id}:"
            f"{inventory.inventory_code}"
        ):
            violations.append("Inventory identity_key is inconsistent.")

        if inventory.version < 1:
            violations.append("Inventory version must be >= 1.")

        if not inventory.created_at.strip():
            violations.append("Inventory created_at is required.")

        if not inventory.updated_at.strip():
            violations.append("Inventory updated_at is required.")

        if not inventory.name.strip():
            violations.append("Inventory name is required.")

        checked = (
            InventoryConsistencyInvariant.TENANT_SCOPE,
            InventoryConsistencyInvariant.PROJECT_SCOPE,
            InventoryConsistencyInvariant.IDENTITY,
            InventoryConsistencyInvariant.VERSION,
            InventoryConsistencyInvariant.LIFECYCLE,
            InventoryConsistencyInvariant.AVAILABILITY,
        )

        return InventoryConsistencyResult(
            valid=not violations,
            checked_invariants=checked,
            violations=tuple(violations),
        )

    def assert_inventory(
        self,
        inventory: Inventory,
        *,
        tenant_id: str,
        project_id: str,
    ) -> None:
        """Raise a typed error if Inventory consistency is invalid."""

        result = self.validate_inventory(
            inventory,
            tenant_id=tenant_id,
            project_id=project_id,
        )

        if result.valid:
            return

        if any(
            "tenant" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyScopeError(
                result.violations[0]
            )

        if any(
            "project" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyScopeError(
                result.violations[0]
            )

        if any(
            "identity" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyIdentityError(
                result.violations[0]
            )

        if any(
            "version" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyVersionError(
                result.violations[0]
            )

        raise InventoryConsistencyError(result.violations[0])

    def validate_event(
        self,
        inventory: Inventory,
        event: InventoryEvent,
    ) -> InventoryConsistencyResult:
        """Validate an Inventory event against its aggregate."""

        violations: list[str] = []

        if event.inventory_id != inventory.inventory_id:
            violations.append(
                "Event inventory_id does not match Inventory."
            )

        if event.tenant_id != inventory.tenant_id:
            violations.append(
                "Event tenant_id does not match Inventory."
            )

        if event.project_id != inventory.project_id:
            violations.append(
                "Event project_id does not match Inventory."
            )

        if event.inventory_version != inventory.version:
            violations.append(
                "Event inventory_version does not match Inventory."
            )

        return InventoryConsistencyResult(
            valid=not violations,
            checked_invariants=(
                InventoryConsistencyInvariant.EVENT,
                InventoryConsistencyInvariant.TENANT_SCOPE,
                InventoryConsistencyInvariant.PROJECT_SCOPE,
                InventoryConsistencyInvariant.VERSION,
            ),
            violations=tuple(violations),
        )

    def assert_event(
        self,
        inventory: Inventory,
        event: InventoryEvent,
    ) -> None:
        """Raise if an Inventory event is inconsistent."""

        result = self.validate_event(inventory, event)

        if result.valid:
            return

        if any(
            "tenant" in violation.lower()
            or "project" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyScopeError(
                result.violations[0]
            )

        if any(
            "version" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyVersionError(
                result.violations[0]
            )

        raise InventoryConsistencyIdentityError(
            result.violations[0]
        )

    def validate_verification(
        self,
        inventory: Inventory,
        verification: InventoryVerification,
    ) -> InventoryConsistencyResult:
        """Validate a verification projection against Inventory."""

        violations: list[str] = []

        if verification.inventory_id != inventory.inventory_id:
            violations.append(
                "Verification inventory_id does not match Inventory."
            )

        if verification.tenant_id != inventory.tenant_id:
            violations.append(
                "Verification tenant_id does not match Inventory."
            )

        if verification.project_id != inventory.project_id:
            violations.append(
                "Verification project_id does not match Inventory."
            )

        if verification.inventory_version != inventory.version:
            violations.append(
                "Verification inventory_version does not match Inventory."
            )

        if verification.version < 1:
            violations.append(
                "Verification version must be >= 1."
            )

        return InventoryConsistencyResult(
            valid=not violations,
            checked_invariants=(
                InventoryConsistencyInvariant.VERIFICATION,
                InventoryConsistencyInvariant.TENANT_SCOPE,
                InventoryConsistencyInvariant.PROJECT_SCOPE,
                InventoryConsistencyInvariant.VERSION,
            ),
            violations=tuple(violations),
        )

    def assert_verification(
        self,
        inventory: Inventory,
        verification: InventoryVerification,
    ) -> None:
        """Raise if a verification projection is inconsistent."""

        result = self.validate_verification(
            inventory,
            verification,
        )

        if result.valid:
            return

        if any(
            "tenant" in violation.lower()
            or "project" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyScopeError(
                result.violations[0]
            )

        if any(
            "version" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyVersionError(
                result.violations[0]
            )

        raise InventoryConsistencyProjectionError(
            result.violations[0]
        )

    def validate_index(
        self,
        inventory: Inventory,
        document: InventoryIndexDocument,
    ) -> InventoryConsistencyResult:
        """Validate an indexing projection against Inventory."""

        violations: list[str] = []

        if document.inventory_id != inventory.inventory_id:
            violations.append(
                "Index inventory_id does not match Inventory."
            )

        if document.index_key != inventory.identity_key:
            violations.append(
                "Index key does not match Inventory identity."
            )

        if document.tenant_id != inventory.tenant_id:
            violations.append(
                "Index tenant_id does not match Inventory."
            )

        if document.project_id != inventory.project_id:
            violations.append(
                "Index project_id does not match Inventory."
            )

        if document.inventory_version != inventory.version:
            violations.append(
                "Index inventory_version does not match Inventory."
            )

        if document.inventory_code != inventory.inventory_code:
            violations.append(
                "Index inventory_code does not match Inventory."
            )

        if document.inventory_type != inventory.inventory_type.value:
            violations.append(
                "Index inventory_type does not match Inventory."
            )

        if document.lifecycle != inventory.lifecycle.value:
            violations.append(
                "Index lifecycle does not match Inventory."
            )

        if document.availability != inventory.availability.value:
            violations.append(
                "Index availability does not match Inventory."
            )

        return InventoryConsistencyResult(
            valid=not violations,
            checked_invariants=(
                InventoryConsistencyInvariant.INDEXING,
                InventoryConsistencyInvariant.IDENTITY,
                InventoryConsistencyInvariant.TENANT_SCOPE,
                InventoryConsistencyInvariant.PROJECT_SCOPE,
                InventoryConsistencyInvariant.VERSION,
            ),
            violations=tuple(violations),
        )

    def assert_index(
        self,
        inventory: Inventory,
        document: InventoryIndexDocument,
    ) -> None:
        """Raise if an indexing projection is inconsistent."""

        result = self.validate_index(
            inventory,
            document,
        )

        if result.valid:
            return

        if any(
            "tenant" in violation.lower()
            or "project" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyScopeError(
                result.violations[0]
            )

        if any(
            "version" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyVersionError(
                result.violations[0]
            )

        if any(
            "identity" in violation.lower()
            for violation in result.violations
        ):
            raise InventoryConsistencyIdentityError(
                result.violations[0]
            )

        raise InventoryConsistencyProjectionError(
            result.violations[0]
        )


def validate_inventory_consistency(
    inventory: Inventory,
    *,
    tenant_id: str,
    project_id: str,
) -> InventoryConsistencyResult:
    """Convenience API for Inventory consistency validation."""

    return InventoryConsistencyValidator().validate_inventory(
        inventory,
        tenant_id=tenant_id,
        project_id=project_id,
    )


__all__ = [
    "InventoryConsistencyError",
    "InventoryConsistencyIdentityError",
    "InventoryConsistencyInvariant",
    "InventoryConsistencyProjectionError",
    "InventoryConsistencyResult",
    "InventoryConsistencyScopeError",
    "InventoryConsistencyValidator",
    "InventoryConsistencyVersionError",
    "validate_inventory_consistency",
]