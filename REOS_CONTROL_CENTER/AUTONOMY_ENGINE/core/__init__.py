"""REOS core domain package.

Domain implementations live in their named CORE subpackages.

The package root keeps the historical public exports, but resolves them
lazily so an unfinished or evolving future CORE cannot block an already
implemented CORE during package import.
"""

from importlib import import_module


_LAZY_EXPORTS = {
    "Inventory": (".inventory", "Inventory"),
    "InventoryDomainError": (".inventory", "InventoryDomainError"),
    "InventoryEvent": (".inventory", "InventoryEvent"),
    "InventoryProjectViolation": (
        ".inventory",
        "InventoryProjectViolation",
    ),
    "InventoryTenantViolation": (
        ".inventory",
        "InventoryTenantViolation",
    ),
    "InventoryType": (".inventory", "InventoryType"),
    "Project": (".project", "Project"),
    "ProjectDomainError": (".project", "ProjectDomainError"),
    "ProjectEvent": (".project", "ProjectEvent"),
    "ProjectLifecycle": (".project", "ProjectLifecycle"),
    "ProjectLocation": (".project", "ProjectLocation"),
    "ProjectOperatingMode": (
        ".project",
        "ProjectOperatingMode",
    ),
    "ProjectTenantViolation": (
        ".project",
        "ProjectTenantViolation",
    ),
    "ProjectTransitionError": (
        ".project",
        "ProjectTransitionError",
    ),
}


__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str):
    """Resolve domain exports only when explicitly requested."""
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )

    module_name, attribute_name = target
    module = import_module(module_name, __name__)

    try:
        return getattr(module, attribute_name)
    except AttributeError as exc:
        raise AttributeError(
            f"domain export {name!r} is not currently implemented"
        ) from exc
