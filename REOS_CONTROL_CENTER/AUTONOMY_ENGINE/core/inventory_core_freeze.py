"""Authoritative REOS inventory core freeze capability for CORE-004-T10.

T10 owns the final freeze boundary for the completed Inventory Core.

The Inventory Core implementation remains distributed across dedicated,
independent modules:

    T02 - inventory domain
    T03 - lifecycle
    T04 - availability
    T05 - verification
    T06 - history and evidence
    T07 - indexing hooks
    T08 - consistency
    T09 - concurrency

This module does not mutate or duplicate any authoritative domain state.

It creates a deterministic, persistence-neutral freeze manifest that
records the approved CORE-004 capability boundary.

A freeze manifest is an explicit contract describing what belongs to the
frozen Inventory Core and what remains outside its responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class InventoryCoreFreezeError(ValueError):
    """Base error for Inventory Core freeze failures."""


class InventoryCoreFreezeValidationError(InventoryCoreFreezeError):
    """Raised when a freeze manifest is structurally invalid."""


@dataclass(frozen=True)
class InventoryCoreFreezeManifest:
    """Immutable manifest describing the frozen CORE-004 boundary."""

    core_name: str
    gate_id: str
    version: str
    status: str
    capabilities: tuple[str, ...]
    authoritative_modules: tuple[str, ...]
    excluded_responsibilities: tuple[str, ...]
    test_baseline: int

    def __post_init__(self) -> None:
        if self.core_name != "Inventory Core":
            raise InventoryCoreFreezeValidationError(
                "core_name must be 'Inventory Core'."
            )

        if self.gate_id != "CORE-004":
            raise InventoryCoreFreezeValidationError(
                "gate_id must be 'CORE-004'."
            )

        if self.status != "FROZEN":
            raise InventoryCoreFreezeValidationError(
                "status must be 'FROZEN'."
            )

        if not self.version.strip():
            raise InventoryCoreFreezeValidationError(
                "version is required."
            )

        if not self.capabilities:
            raise InventoryCoreFreezeValidationError(
                "capabilities are required."
            )

        if len(set(self.capabilities)) != len(self.capabilities):
            raise InventoryCoreFreezeValidationError(
                "capabilities must be unique."
            )

        if not self.authoritative_modules:
            raise InventoryCoreFreezeValidationError(
                "authoritative_modules are required."
            )

        if len(set(self.authoritative_modules)) != len(
            self.authoritative_modules
        ):
            raise InventoryCoreFreezeValidationError(
                "authoritative_modules must be unique."
            )

        if self.test_baseline < 1:
            raise InventoryCoreFreezeValidationError(
                "test_baseline must be >= 1."
            )

    @property
    def capability_count(self) -> int:
        return len(self.capabilities)

    @property
    def module_count(self) -> int:
        return len(self.authoritative_modules)

    def contains_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def contains_module(self, module: str) -> bool:
        return module in self.authoritative_modules

    def to_dict(self) -> dict[str, object]:
        return {
            "core_name": self.core_name,
            "gate_id": self.gate_id,
            "version": self.version,
            "status": self.status,
            "capabilities": list(self.capabilities),
            "authoritative_modules": list(
                self.authoritative_modules
            ),
            "excluded_responsibilities": list(
                self.excluded_responsibilities
            ),
            "test_baseline": self.test_baseline,
            "capability_count": self.capability_count,
            "module_count": self.module_count,
        }


FROZEN_INVENTORY_CAPABILITIES = (
    "inventory_identity_and_scope",
    "inventory_type",
    "inventory_lifecycle",
    "inventory_availability",
    "inventory_verification",
    "inventory_history_and_evidence",
    "inventory_indexing_hooks",
    "inventory_consistency",
    "inventory_concurrency",
)


FROZEN_INVENTORY_MODULES = (
    "inventory.py",
    "inventory_verification.py",
    "inventory_history.py",
    "inventory_evidence.py",
    "inventory_indexing.py",
    "inventory_consistency.py",
    "inventory_concurrency.py",
)


EXCLUDED_INVENTORY_RESPONSIBILITIES = (
    "persistent_database_storage",
    "search_engine_persistence",
    "cross_core_orchestration",
    "external_api_transport",
    "production_deployment",
)


def freeze_inventory_core(
    *,
    version: str = "1.0",
    test_baseline: int = 509,
) -> InventoryCoreFreezeManifest:
    """Create the canonical immutable CORE-004 freeze manifest."""

    return InventoryCoreFreezeManifest(
        core_name="Inventory Core",
        gate_id="CORE-004",
        version=version,
        status="FROZEN",
        capabilities=FROZEN_INVENTORY_CAPABILITIES,
        authoritative_modules=FROZEN_INVENTORY_MODULES,
        excluded_responsibilities=(
            EXCLUDED_INVENTORY_RESPONSIBILITIES
        ),
        test_baseline=test_baseline,
    )


def validate_inventory_core_freeze(
    manifest: InventoryCoreFreezeManifest,
) -> None:
    """Validate that a manifest matches the canonical CORE-004 boundary."""

    if manifest.gate_id != "CORE-004":
        raise InventoryCoreFreezeValidationError(
            "Freeze manifest belongs to a different gate."
        )

    if manifest.status != "FROZEN":
        raise InventoryCoreFreezeValidationError(
            "Inventory Core must be marked FROZEN."
        )

    if manifest.capabilities != FROZEN_INVENTORY_CAPABILITIES:
        raise InventoryCoreFreezeValidationError(
            "Inventory Core capability boundary does not match "
            "the canonical CORE-004 freeze definition."
        )

    if manifest.authoritative_modules != FROZEN_INVENTORY_MODULES:
        raise InventoryCoreFreezeValidationError(
            "Inventory Core module boundary does not match "
            "the canonical CORE-004 freeze definition."
        )


__all__ = [
    "EXCLUDED_INVENTORY_RESPONSIBILITIES",
    "FROZEN_INVENTORY_CAPABILITIES",
    "FROZEN_INVENTORY_MODULES",
    "InventoryCoreFreezeError",
    "InventoryCoreFreezeManifest",
    "InventoryCoreFreezeValidationError",
    "freeze_inventory_core",
    "validate_inventory_core_freeze",
]