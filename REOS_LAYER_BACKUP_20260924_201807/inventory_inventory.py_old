"""Authoritative REOS inventory domain for CORE-004.

T02 owns inventory identity, tenant/project scope and inventory type.
T03 owns inventory lifecycle and lifecycle transitions.
T04 owns inventory availability and availability transitions.

Verification, history/evidence, indexing and concurrency orchestration
remain dedicated to their respective CORE-004 subtasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Mapping
from uuid import uuid4


class InventoryDomainError(ValueError):
    """Base error for invalid inventory-domain operations."""


class InventoryTenantViolation(InventoryDomainError):
    """Raised when tenant isolation is violated."""


class InventoryProjectViolation(InventoryDomainError):
    """Raised when project ownership is violated."""


class InventoryTransitionError(InventoryDomainError):
    """Raised when an inventory lifecycle transition is invalid."""


class InventoryAvailabilityTransitionError(InventoryDomainError):
    """Raised when an inventory availability transition is invalid."""


class InventoryType(str, Enum):
    RESIDENTIAL_UNIT = "RESIDENTIAL_UNIT"
    COMMERCIAL_UNIT = "COMMERCIAL_UNIT"
    PLOT = "PLOT"
    LAND_PARCEL = "LAND_PARCEL"
    BUILDING = "BUILDING"
    VILLA = "VILLA"
    OFFICE = "OFFICE"
    RETAIL = "RETAIL"
    WAREHOUSE = "WAREHOUSE"
    INDUSTRIAL = "INDUSTRIAL"
    OTHER = "OTHER"


class InventoryLifecycle(str, Enum):
    DRAFT = "DRAFT"
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class InventoryAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    UNAVAILABLE = "UNAVAILABLE"


_ALLOWED_LIFECYCLE_TRANSITIONS: dict[
    InventoryLifecycle, frozenset[InventoryLifecycle]
] = {
    InventoryLifecycle.DRAFT: frozenset(
        {
            InventoryLifecycle.ONBOARDING,
            InventoryLifecycle.ARCHIVED,
        }
    ),
    InventoryLifecycle.ONBOARDING: frozenset(
        {
            InventoryLifecycle.ACTIVE,
            InventoryLifecycle.SUSPENDED,
            InventoryLifecycle.ARCHIVED,
        }
    ),
    InventoryLifecycle.ACTIVE: frozenset(
        {
            InventoryLifecycle.SUSPENDED,
            InventoryLifecycle.ARCHIVED,
        }
    ),
    InventoryLifecycle.SUSPENDED: frozenset(
        {
            InventoryLifecycle.ONBOARDING,
            InventoryLifecycle.ACTIVE,
            InventoryLifecycle.ARCHIVED,
        }
    ),
    InventoryLifecycle.ARCHIVED: frozenset(),
}


_ALLOWED_AVAILABILITY_TRANSITIONS: dict[
    InventoryAvailability, frozenset[InventoryAvailability]
] = {
    InventoryAvailability.AVAILABLE: frozenset(
        {
            InventoryAvailability.RESERVED,
            InventoryAvailability.SOLD,
            InventoryAvailability.UNAVAILABLE,
        }
    ),
    InventoryAvailability.RESERVED: frozenset(
        {
            InventoryAvailability.AVAILABLE,
            InventoryAvailability.SOLD,
            InventoryAvailability.UNAVAILABLE,
        }
    ),
    InventoryAvailability.SOLD: frozenset(
        {
            InventoryAvailability.UNAVAILABLE,
        }
    ),
    InventoryAvailability.UNAVAILABLE: frozenset(
        {
            InventoryAvailability.AVAILABLE,
        }
    ),
}


_INVENTORY_CODE = re.compile(r"[A-Z0-9][A-Z0-9_-]{1,63}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class InventoryEvent:
    """Persistence-neutral event emitted by an inventory domain change."""

    event_id: str
    event_type: str
    inventory_id: str
    project_id: str
    tenant_id: str
    inventory_version: int
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "inventory_id": self.inventory_id,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "inventory_version": self.inventory_version,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class Inventory:
    """Authoritative inventory aggregate for CORE-004.

    ``tenant_id + project_id + inventory_code`` is the natural identity.

    ``project_id`` is the authoritative relationship to Project.
    Inventory does not duplicate project ownership as an independent
    source of truth.

    Lifecycle and availability are independent domain dimensions.
    """

    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_code: str
    inventory_type: InventoryType
    name: str
    lifecycle: InventoryLifecycle
    created_at: str
    updated_at: str
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_of_truth: str = "inventory"
    availability: InventoryAvailability = InventoryAvailability.AVAILABLE

    def __post_init__(self) -> None:
        for field_name in (
            "inventory_id",
            "tenant_id",
            "project_id",
            "inventory_code",
            "name",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InventoryDomainError(f"{field_name} is required.")

        if not _INVENTORY_CODE.fullmatch(self.inventory_code):
            raise InventoryDomainError(
                "inventory_code must be 2-64 characters using uppercase "
                "letters, digits, '_' or '-'."
            )

        if self.version < 1:
            raise InventoryDomainError("version must be >= 1.")

        if self.source_of_truth != "inventory":
            raise InventoryDomainError(
                "inventory must remain the authoritative source of truth."
            )

        object.__setattr__(
            self,
            "inventory_type",
            InventoryType(self.inventory_type),
        )
        object.__setattr__(
            self,
            "lifecycle",
            InventoryLifecycle(self.lifecycle),
        )
        object.__setattr__(
            self,
            "availability",
            InventoryAvailability(self.availability),
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        project_id: str,
        inventory_code: str,
        inventory_type: InventoryType,
        name: str,
        metadata: Mapping[str, Any] | None = None,
        inventory_id: str | None = None,
        at: str | None = None,
    ) -> "Inventory":
        timestamp = at or _utc_now()

        return cls(
            inventory_id=inventory_id or str(uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            inventory_code=inventory_code,
            inventory_type=InventoryType(inventory_type),
            name=name,
            lifecycle=InventoryLifecycle.DRAFT,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=dict(metadata or {}),
            availability=InventoryAvailability.AVAILABLE,
        )

    @property
    def identity_key(self) -> str:
        return f"{self.tenant_id}:{self.project_id}:{self.inventory_code}"

    def assert_tenant(self, tenant_id: str) -> None:
        if tenant_id != self.tenant_id:
            raise InventoryTenantViolation(
                "Inventory belongs to a different tenant."
            )

    def assert_project(self, project_id: str) -> None:
        if project_id != self.project_id:
            raise InventoryProjectViolation(
                "Inventory belongs to a different project."
            )

    def transition(
        self,
        target: InventoryLifecycle,
        *,
        tenant_id: str,
        project_id: str,
        at: str | None = None,
    ) -> tuple["Inventory", InventoryEvent]:
        """Apply one deterministic lifecycle transition."""

        self.assert_tenant(tenant_id)
        self.assert_project(project_id)

        target = InventoryLifecycle(target)

        if target not in _ALLOWED_LIFECYCLE_TRANSITIONS[self.lifecycle]:
            raise InventoryTransitionError(
                "Invalid inventory lifecycle transition: "
                f"{self.lifecycle.value} -> {target.value}."
            )

        timestamp = at or _utc_now()

        updated = replace(
            self,
            lifecycle=target,
            updated_at=timestamp,
            version=self.version + 1,
        )

        event = InventoryEvent(
            event_id=str(uuid4()),
            event_type="INVENTORY_LIFECYCLE_CHANGED",
            inventory_id=self.inventory_id,
            project_id=self.project_id,
            tenant_id=self.tenant_id,
            inventory_version=updated.version,
            occurred_at=timestamp,
            payload={
                "from": self.lifecycle.value,
                "to": target.value,
                "identity_key": self.identity_key,
            },
        )

        return updated, event

    def set_availability(
        self,
        target: InventoryAvailability,
        *,
        tenant_id: str,
        project_id: str,
        at: str | None = None,
    ) -> tuple["Inventory", InventoryEvent]:
        """Apply one deterministic availability transition.

        Availability is part of the authoritative inventory aggregate.
        Every accepted transition creates a new immutable inventory version
        and emits one persistence-neutral domain event.
        """

        self.assert_tenant(tenant_id)
        self.assert_project(project_id)

        target = InventoryAvailability(target)

        if target not in _ALLOWED_AVAILABILITY_TRANSITIONS[self.availability]:
            raise InventoryAvailabilityTransitionError(
                "Invalid inventory availability transition: "
                f"{self.availability.value} -> {target.value}."
            )

        timestamp = at or _utc_now()

        updated = replace(
            self,
            availability=target,
            updated_at=timestamp,
            version=self.version + 1,
        )

        event = InventoryEvent(
            event_id=str(uuid4()),
            event_type="INVENTORY_AVAILABILITY_CHANGED",
            inventory_id=self.inventory_id,
            project_id=self.project_id,
            tenant_id=self.tenant_id,
            inventory_version=updated.version,
            occurred_at=timestamp,
            payload={
                "identity_key": self.identity_key,
                "from": self.availability.value,
                "to": target.value,
                "from_version": self.version,
                "to_version": updated.version,
            },
        )

        return updated, event

    def touch(
        self,
        *,
        tenant_id: str,
        project_id: str,
        at: str | None = None,
    ) -> tuple["Inventory", InventoryEvent]:
        """Create the next immutable domain version."""

        self.assert_tenant(tenant_id)
        self.assert_project(project_id)

        timestamp = at or _utc_now()

        updated = replace(
            self,
            updated_at=timestamp,
            version=self.version + 1,
        )

        event = InventoryEvent(
            event_id=str(uuid4()),
            event_type="INVENTORY_VERSION_CHANGED",
            inventory_id=self.inventory_id,
            project_id=self.project_id,
            tenant_id=self.tenant_id,
            inventory_version=updated.version,
            occurred_at=timestamp,
            payload={
                "identity_key": self.identity_key,
                "from_version": self.version,
                "to_version": updated.version,
            },
        )

        return updated, event

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_code": self.inventory_code,
            "inventory_type": self.inventory_type.value,
            "name": self.name,
            "lifecycle": self.lifecycle.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
            "availability": self.availability.value,
        }


__all__ = [
    "Inventory",
    "InventoryAvailability",
    "InventoryAvailabilityTransitionError",
    "InventoryDomainError",
    "InventoryEvent",
    "InventoryLifecycle",
    "InventoryProjectViolation",
    "InventoryTenantViolation",
    "InventoryTransitionError",
    "InventoryType",
]