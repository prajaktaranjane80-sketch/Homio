"""REOS Core bounded-package namespace and controlled public API.

The root package is a discovery and compatibility boundary. It does not
implement domain orchestration, business services, or a second source of
truth.

Bounded Core packages are loaded lazily to avoid eager Core-graph imports.
Existing Inventory compatibility exports are also resolved lazily.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Final


CORE_PACKAGE_NAMES: Final[tuple[str, ...]] = (
    "identity_tenant",
    "event_platform",
    "lead_ownership",
    "inventory",
    "search_matching",
    "deal_transaction",
    "trust_fraud_governance",
    "commission_financial",
)


_LEGACY_EXPORTS: Final[dict[str, str]] = {
    "AvailabilityState": "AUTONOMY_ENGINE.core.inventory",
    "Inventory": "AUTONOMY_ENGINE.core.inventory",
    "InventoryDomainError": "AUTONOMY_ENGINE.core.inventory",
    "InventoryIdentity": "AUTONOMY_ENGINE.core.inventory",
    "InventoryProjectViolation": "AUTONOMY_ENGINE.core.inventory",
    "InventoryTenantViolation": "AUTONOMY_ENGINE.core.inventory",
    "InventoryType": "AUTONOMY_ENGINE.core.inventory",
    "LifecycleState": "AUTONOMY_ENGINE.core.inventory",
    "Project": "AUTONOMY_ENGINE.core.inventory",
    "ProjectDomainError": "AUTONOMY_ENGINE.core.inventory",
    "ProjectIdentity": "AUTONOMY_ENGINE.core.inventory",
    "ProjectTenantViolation": "AUTONOMY_ENGINE.core.inventory",
    "InventoryDomainEvent": (
        "AUTONOMY_ENGINE.core.inventory.inventory_event_integration"
    ),
    "InventoryDomainEventType": (
        "AUTONOMY_ENGINE.core.inventory.inventory_event_integration"
    ),
}


def get_core_package(
    name: str,
) -> ModuleType:
    """Load exactly one bounded Core package on demand."""
    if name not in CORE_PACKAGE_NAMES:
        raise ValueError(
            f"Unknown REOS Core package: {name!r}."
        )

    return import_module(
        f"{__name__}.{name}"
    )


def iter_core_packages() -> tuple[str, ...]:
    """Return the canonical bounded Core package names."""
    return CORE_PACKAGE_NAMES


def __getattr__(
    name: str,
) -> object:
    """Resolve bounded packages and legacy compatibility exports lazily."""
    if name in CORE_PACKAGE_NAMES:
        return get_core_package(name)

    module_name = _LEGACY_EXPORTS.get(name)

    if module_name is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )

    module = import_module(module_name)

    try:
        return getattr(module, name)
    except AttributeError as exc:
        raise AttributeError(
            f"Compatibility export {name!r} is unavailable "
            f"from {module_name!r}."
        ) from exc


__all__ = [
    "CORE_PACKAGE_NAMES",
    "get_core_package",
    "iter_core_packages",
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
    "InventoryDomainEvent",
    "InventoryDomainEventType",
]
