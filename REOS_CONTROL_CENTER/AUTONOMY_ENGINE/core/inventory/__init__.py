"""CORE-004 Inventory domain package.

The package owns canonical inventory identity and project identity for the
inventory bounded context. Higher-level contracts, hierarchy, lifecycle,
availability, provenance, commercial state, concurrency, security and
integration contracts are added by dedicated CORE-004 modules.
"""

from .inventory import (
    AvailabilityState,
    Inventory,
    InventoryDomainError,
    InventoryEvent,
    InventoryIdentity,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
    LifecycleState,
)

from .project import (
    Project,
    ProjectDomainError,
    ProjectEvent,
    ProjectLifecycle,
    ProjectLocation,
    ProjectOperatingMode,
    ProjectTenantViolation,
    ProjectTransitionError,
)

__all__ = [
    "AvailabilityState",
    "Inventory",
    "InventoryDomainError",
    "InventoryEvent",
    "InventoryIdentity",
    "InventoryProjectViolation",
    "InventoryTenantViolation",
    "InventoryType",
    "LifecycleState",
    "Project",
    "ProjectDomainError",
    "ProjectEvent",
    "ProjectLifecycle",
    "ProjectLocation",
    "ProjectOperatingMode",
    "ProjectTenantViolation",
    "ProjectTransitionError",
]
