from __future__ import annotations

from dataclasses import replace

import pytest

from AUTONOMY_ENGINE.core.inventory_core_freeze import (
    FROZEN_INVENTORY_CAPABILITIES,
    FROZEN_INVENTORY_MODULES,
    InventoryCoreFreezeManifest,
    InventoryCoreFreezeValidationError,
    freeze_inventory_core,
    validate_inventory_core_freeze,
)


def test_inventory_core_freezes_successfully() -> None:
    manifest = freeze_inventory_core()

    assert manifest.core_name == "Inventory Core"
    assert manifest.gate_id == "CORE-004"
    assert manifest.version == "1.0"
    assert manifest.status == "FROZEN"


def test_freeze_contains_all_canonical_capabilities() -> None:
    manifest = freeze_inventory_core()

    assert manifest.capabilities == FROZEN_INVENTORY_CAPABILITIES
    assert manifest.capability_count == 9


@pytest.mark.parametrize(
    "capability",
    FROZEN_INVENTORY_CAPABILITIES,
)
def test_each_inventory_capability_is_frozen(
    capability: str,
) -> None:
    manifest = freeze_inventory_core()

    assert manifest.contains_capability(capability) is True


def test_freeze_contains_authoritative_modules() -> None:
    manifest = freeze_inventory_core()

    assert manifest.authoritative_modules == FROZEN_INVENTORY_MODULES
    assert manifest.module_count == len(FROZEN_INVENTORY_MODULES)


@pytest.mark.parametrize(
    "module",
    FROZEN_INVENTORY_MODULES,
)
def test_each_authoritative_module_is_in_freeze(
    module: str,
) -> None:
    manifest = freeze_inventory_core()

    assert manifest.contains_module(module) is True


def test_freeze_baseline_can_record_current_regression() -> None:
    manifest = freeze_inventory_core(test_baseline=509)

    assert manifest.test_baseline == 509


def test_freeze_manifest_is_immutable() -> None:
    manifest = freeze_inventory_core()

    with pytest.raises(Exception):
        manifest.status = "OPEN"  # type: ignore[misc]


def test_freeze_manifest_serializes_canonically() -> None:
    manifest = freeze_inventory_core()

    data = manifest.to_dict()

    assert data["core_name"] == "Inventory Core"
    assert data["gate_id"] == "CORE-004"
    assert data["version"] == "1.0"
    assert data["status"] == "FROZEN"
    assert data["capability_count"] == 9
    assert data["module_count"] == len(FROZEN_INVENTORY_MODULES)
    assert data["test_baseline"] == 509


def test_canonical_manifest_validates() -> None:
    manifest = freeze_inventory_core()

    validate_inventory_core_freeze(manifest)


def test_wrong_gate_is_rejected() -> None:
    with pytest.raises(InventoryCoreFreezeValidationError):
        InventoryCoreFreezeManifest(
            core_name="Inventory Core",
            gate_id="CORE-999",
            version="1.0",
            status="FROZEN",
            capabilities=FROZEN_INVENTORY_CAPABILITIES,
            authoritative_modules=FROZEN_INVENTORY_MODULES,
            excluded_responsibilities=(),
            test_baseline=509,
        )


def test_non_frozen_status_is_rejected() -> None:
    with pytest.raises(InventoryCoreFreezeValidationError):
        InventoryCoreFreezeManifest(
            core_name="Inventory Core",
            gate_id="CORE-004",
            version="1.0",
            status="OPEN",
            capabilities=FROZEN_INVENTORY_CAPABILITIES,
            authoritative_modules=FROZEN_INVENTORY_MODULES,
            excluded_responsibilities=(),
            test_baseline=509,
        )



def test_missing_capability_boundary_is_rejected() -> None:
    manifest = replace(
        freeze_inventory_core(),
        capabilities=(
            "inventory_identity_and_scope",
        ),
    )

    with pytest.raises(InventoryCoreFreezeValidationError):
        validate_inventory_core_freeze(manifest)


def test_changed_module_boundary_is_rejected() -> None:
    manifest = replace(
        freeze_inventory_core(),
        authoritative_modules=(
            "inventory.py",
        ),
    )

    with pytest.raises(InventoryCoreFreezeValidationError):
        validate_inventory_core_freeze(manifest)


def test_duplicate_capabilities_are_rejected() -> None:
    with pytest.raises(InventoryCoreFreezeValidationError):
        InventoryCoreFreezeManifest(
            core_name="Inventory Core",
            gate_id="CORE-004",
            version="1.0",
            status="FROZEN",
            capabilities=(
                "inventory_identity_and_scope",
                "inventory_identity_and_scope",
            ),
            authoritative_modules=(
                "inventory.py",
            ),
            excluded_responsibilities=(),
            test_baseline=1,
        )


def test_duplicate_modules_are_rejected() -> None:
    with pytest.raises(InventoryCoreFreezeValidationError):
        InventoryCoreFreezeManifest(
            core_name="Inventory Core",
            gate_id="CORE-004",
            version="1.0",
            status="FROZEN",
            capabilities=(
                "inventory_identity_and_scope",
            ),
            authoritative_modules=(
                "inventory.py",
                "inventory.py",
            ),
            excluded_responsibilities=(),
            test_baseline=1,
        )


@pytest.mark.parametrize(
    "baseline",
    [
        0,
        -1,
    ],
)
def test_invalid_test_baseline_is_rejected(
    baseline: int,
) -> None:
    with pytest.raises(InventoryCoreFreezeValidationError):
        freeze_inventory_core(test_baseline=baseline)


def test_custom_version_is_preserved() -> None:
    manifest = freeze_inventory_core(version="1.0.1")

    assert manifest.version == "1.0.1"
    validate_inventory_core_freeze(manifest)


def test_freeze_does_not_depend_on_live_inventory_mutation() -> None:
    first = freeze_inventory_core()
    second = freeze_inventory_core()

    assert first == second