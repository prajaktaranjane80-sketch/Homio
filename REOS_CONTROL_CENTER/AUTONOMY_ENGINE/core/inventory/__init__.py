"""CORE-004 Inventory bounded-context public exports."""

from .inventory import (
    AvailabilityState,
    Inventory,
    InventoryDomainError,
    InventoryIdentity,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
    LifecycleState,
)

from .project import (
    Project,
    ProjectDomainError,
    ProjectIdentity,
    ProjectTenantViolation,
)

from .inventory_event_integration import (
    CORE_004_EVENT_PRODUCER,
    CORE_004_EVENT_SCHEMA_VERSION,
    InventoryDomainEvent,
    InventoryDomainEventType,
)

__all__ = [
    "AvailabilityState",
    "Inventory",
    "InventoryDomainError",
    "InventoryIdentity",
    "InventoryProjectViolation",
    "InventoryTenantViolation",
    "InventoryType",
    "LifecycleState",
    "Project",
    "ProjectDomainError",
    "ProjectIdentity",
    "ProjectTenantViolation",
    "CORE_004_EVENT_PRODUCER",
    "CORE_004_EVENT_SCHEMA_VERSION",
    "InventoryDomainEvent",
    "InventoryDomainEventType",
]
