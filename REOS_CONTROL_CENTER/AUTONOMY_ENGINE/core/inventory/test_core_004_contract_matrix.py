from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from AUTONOMY_ENGINE.core import (
    AvailabilityState,
    Inventory,
    InventoryDomainEvent,
    InventoryDomainEventType,
    InventoryIdentity,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
    LifecycleState,
    Project,
    ProjectIdentity,
)

from AUTONOMY_ENGINE.core.inventory.inventory_contract import (
    CORE_004_SCHEMA_VERSION,
    PROJECT_CONTRACT,
    PROPERTY_CONTRACT,
    UNIT_CONTRACT,
    InventoryContractCompatibilityError,
    InventorySchemaError,
    InventorySchemaVersionError,
    InventorySerializationError,
    contract_by_name,
    contract_for_inventory_type,
    deserialize_contract,
    payload_fingerprint,
    project_contract_fingerprint,
    property_contract_fingerprint,
    require_schema_compatibility,
    schema_compatible,
    serialize_project,
    serialize_property,
    serialize_unit,
    validate_inventory_mapping,
    validate_project_mapping,
    validate_schema_version,
)

from AUTONOMY_ENGINE.core.inventory.inventory_acrl_contract import (
    InventoryACRLOperation,
    InventoryACRLDriftError,
    InventoryACRLPreconditionConflict,
    InventoryACRLIntegrationContract,
    InventoryCheckpointDescriptor,
    InventoryReconstructionDescriptor,
    detect_drift,
    hierarchy_fingerprint,
    validate_checkpoint_compatibility,
)

from AUTONOMY_ENGINE.core.inventory.inventory_event_integration import (
    CORE_004_EVENT_PRODUCER,
    CORE_004_EVENT_SCHEMA_VERSION,
    InventoryEventConflictError,
    compare_event_identity,
    inventory_created_event,
    inventory_updated_event,
)


UTC = timezone.utc
T0 = datetime(
    2026,
    1,
    1,
    10,
    0,
    tzinfo=UTC,
)


def make_project() -> Project:
    return Project(
        identity=ProjectIdentity(
            project_id="PROJECT-1",
            tenant_id="TENANT-1",
            developer_id="DEV-1",
            project_code="PRJ-001",
        ),
        name="Project One",
    )


def make_property() -> Inventory:
    return Inventory.create(
        tenant_id="TENANT-1",
        developer_id="DEV-1",
        project_id="PROJECT-1",
        inventory_type=InventoryType.PROPERTY,
        property_id="PROPERTY-1",
        name="Property",
        inventory_id="PROPERTY-1",
        at=T0,
    )


def make_unit() -> Inventory:
    return Inventory.create(
        tenant_id="TENANT-1",
        developer_id="DEV-1",
        project_id="PROJECT-1",
        inventory_type=InventoryType.UNIT,
        property_id="PROPERTY-1",
        unit_id="UNIT-1",
        name="Unit",
        inventory_id="UNIT-1",
        at=T0,
    )


def test_contract_registry_is_complete() -> None:
    assert (
        contract_by_name(
            PROJECT_CONTRACT.schema_name
        )
        is PROJECT_CONTRACT
    )

    assert (
        contract_by_name(
            PROPERTY_CONTRACT.schema_name
        )
        is PROPERTY_CONTRACT
    )

    assert (
        contract_by_name(
            UNIT_CONTRACT.schema_name
        )
        is UNIT_CONTRACT
    )

    assert (
        contract_for_inventory_type(
            InventoryType.PROPERTY
        )
        is PROPERTY_CONTRACT
    )

    assert (
        contract_for_inventory_type(
            InventoryType.UNIT
        )
        is UNIT_CONTRACT
    )


def test_unknown_contract_fails_closed() -> None:
    with pytest.raises(InventorySchemaError):
        contract_by_name(
            "REOS.CORE-004.UNKNOWN"
        )


def test_schema_future_version_fails_closed() -> None:
    with pytest.raises(
        InventorySchemaVersionError
    ):
        validate_schema_version(
            CORE_004_SCHEMA_VERSION + 1
        )


def test_contract_fingerprints_are_stable() -> None:
    assert (
        property_contract_fingerprint()
        == PROPERTY_CONTRACT.fingerprint
    )

    first = PROPERTY_CONTRACT.fingerprint
    second = PROPERTY_CONTRACT.fingerprint

    assert first == second
    assert len(first) == 64


def test_contract_compatibility_is_exact() -> None:
    assert schema_compatible(
        PROPERTY_CONTRACT,
        PROPERTY_CONTRACT,
    )

    require_schema_compatibility(
        PROPERTY_CONTRACT,
        PROPERTY_CONTRACT,
    )

    with pytest.raises(
        InventoryContractCompatibilityError
    ):
        require_schema_compatibility(
            PROPERTY_CONTRACT,
            UNIT_CONTRACT,
        )


def test_project_serialization_is_canonical() -> None:
    project = make_project()

    first = serialize_project(project)
    second = serialize_project(project)

    assert first == second

    parsed = deserialize_contract(first)

    assert (
        parsed["schema_name"]
        == PROJECT_CONTRACT.schema_name
    )
    assert (
        parsed["schema_version"]
        == CORE_004_SCHEMA_VERSION
    )
    assert (
        parsed["payload"]["project_id"]
        == "PROJECT-1"
    )


def test_property_serialization_is_canonical() -> None:
    inventory = make_property()

    serialized = serialize_property(
        inventory
    )

    parsed = deserialize_contract(
        serialized
    )

    assert (
        parsed["schema_name"]
        == PROPERTY_CONTRACT.schema_name
    )
    assert (
        parsed["payload"]["identity"]["inventory_id"]
        == "PROPERTY-1"
    )


def test_unit_serialization_is_canonical() -> None:
    inventory = make_unit()

    serialized = serialize_unit(
        inventory
    )

    parsed = deserialize_contract(
        serialized
    )

    assert (
        parsed["schema_name"]
        == UNIT_CONTRACT.schema_name
    )


def test_unknown_envelope_field_fails_closed() -> None:
    payload = json.loads(
        serialize_property(
            make_property()
        )
    )

    payload["unknown"] = True

    with pytest.raises(
        InventorySerializationError
    ):
        deserialize_contract(
            json.dumps(payload)
        )


def test_contract_fingerprint_tampering_fails_closed() -> None:
    payload = json.loads(
        serialize_property(
            make_property()
        )
    )

    payload["contract_fingerprint"] = (
        "0" * 64
    )

    with pytest.raises(
        InventorySerializationError
    ):
        deserialize_contract(
            json.dumps(payload)
        )


def test_inventory_mapping_unknown_field_fails_closed() -> None:
    payload = make_property().to_dict()
    payload["UNKNOWN_FIELD"] = True

    with pytest.raises(
        InventorySchemaError
    ):
        validate_inventory_mapping(
            payload
        )


def test_project_mapping_tampering_is_rejected() -> None:
    payload = make_project().to_dict()

    payload["identity_fingerprint"] = (
        "0" * 64
    )

    with pytest.raises(Exception):
        validate_project_mapping(
            payload
        )


def test_payload_fingerprint_is_deterministic() -> None:
    payload = make_unit().to_dict()

    assert (
        payload_fingerprint(payload)
        == payload_fingerprint(dict(payload))
    )


def test_acrl_reconstruction_contract_matches_inventory() -> None:
    inventory = make_unit()

    reconstruction = (
        InventoryReconstructionDescriptor(
            tenant_id=inventory.tenant_id,
            inventory_id=inventory.inventory_id,
            contract_version=1,
            inventory_version=inventory.version,
            identity_fingerprint=(
                inventory.identity_fingerprint
            ),
            hierarchy_fingerprint=None,
            lifecycle_fingerprint=None,
            provenance_fingerprint=None,
        )
    )

    checkpoint = (
        InventoryCheckpointDescriptor(
            checkpoint_id="CHECKPOINT-1",
            tenant_id="TENANT-1",
            inventory_id="UNIT-1",
            sequence=1,
            inventory_version=inventory.version,
            contract_fingerprint="a" * 64,
            created_at=T0,
        )
    )

    contract = (
        InventoryACRLIntegrationContract(
            operation_id="OP-1",
            tenant_id="TENANT-1",
            inventory_id="UNIT-1",
            operation=(
                InventoryACRLOperation
                .RECONSTRUCT_INVENTORY
            ),
            contract_version=1,
            correlation_id="CORR-1",
            idempotency_key="IDEMP-1",
            reconstruction=reconstruction,
            dependency_references=(
                "CORE-001",
                "CORE-002",
            ),
            contract_references=(
                "CORE-004",
            ),
            evidence_references=(
                "EVIDENCE-1",
            ),
            checkpoint=checkpoint,
            created_at=T0,
        )
    )

    contract.validate_current_inventory(
        inventory
    )

    validate_checkpoint_compatibility(
        checkpoint,
        inventory,
    )

    assert contract.fingerprint
    assert contract.contract_key == (
        "TENANT-1",
        "UNIT-1",
        "IDEMP-1",
    )


def test_acrl_checkpoint_future_version_is_rejected() -> None:
    inventory = make_unit()

    checkpoint = (
        InventoryCheckpointDescriptor(
            checkpoint_id="CHECKPOINT-FUTURE",
            tenant_id="TENANT-1",
            inventory_id="UNIT-1",
            sequence=2,
            inventory_version=(
                inventory.version + 1
            ),
            contract_fingerprint="a" * 64,
            created_at=T0,
        )
    )

    with pytest.raises(
        InventoryACRLPreconditionConflict
    ):
        validate_checkpoint_compatibility(
            checkpoint,
            inventory,
        )


def test_acrl_tenant_scope_is_enforced() -> None:
    inventory = make_unit()

    reconstruction = (
        InventoryReconstructionDescriptor(
            tenant_id="TENANT-1",
            inventory_id="UNIT-1",
            contract_version=1,
            inventory_version=inventory.version,
            identity_fingerprint=(
                inventory.identity_fingerprint
            ),
            hierarchy_fingerprint=None,
            lifecycle_fingerprint=None,
            provenance_fingerprint=None,
        )
    )

    contract = (
        InventoryACRLIntegrationContract(
            operation_id="OP-1",
            tenant_id="TENANT-2",
            inventory_id="UNIT-1",
            operation=(
                InventoryACRLOperation
                .RECONSTRUCT_INVENTORY
            ),
            contract_version=1,
            correlation_id="CORR-1",
            idempotency_key="IDEMP-1",
            reconstruction=reconstruction,
            dependency_references=(),
            contract_references=(),
            evidence_references=(),
            checkpoint=None,
            created_at=T0,
        )
    )

    with pytest.raises(
        InventoryACRLPreconditionConflict
    ):
        contract.validate_current_inventory(
            inventory
        )


def test_acrl_identity_drift_is_detected() -> None:
    assert detect_drift(
        expected_fingerprint="A",
        actual_fingerprint="B",
    )

    assert not detect_drift(
        expected_fingerprint="A",
        actual_fingerprint="A",
    )


def test_event_factory_contract() -> None:
    event = inventory_created_event(
        event_id="EVENT-1",
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        inventory_version=1,
        correlation_id="CORR-1",
        idempotency_key="IDEMP-1",
        payload={
            "created": True,
        },
        occurred_at=T0,
    )

    assert isinstance(
        event,
        InventoryDomainEvent,
    )

    assert (
        event.event_type
        is InventoryDomainEventType.INVENTORY_CREATED
    )

    assert (
        event.schema_version
        == CORE_004_EVENT_SCHEMA_VERSION
    )

    assert (
        event.producer
        == CORE_004_EVENT_PRODUCER
    )


def test_event_identity_conflict_is_rejected() -> None:
    first = inventory_updated_event(
        event_id="EVENT-1",
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        inventory_version=1,
        correlation_id="CORR-1",
        idempotency_key="IDEMP-1",
        payload={"state": "ACTIVE"},
        occurred_at=T0,
    )

    second = inventory_updated_event(
        event_id="EVENT-2",
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        inventory_version=1,
        correlation_id="CORR-1",
        idempotency_key="IDEMP-1",
        payload={"state": "SOLD"},
        occurred_at=T0,
    )

    with pytest.raises(
        InventoryEventConflictError
    ):
        compare_event_identity(
            first,
            second,
        )


def test_event_identity_same_payload_is_compatible() -> None:
    kwargs = {
        "event_id": "EVENT-1",
        "tenant_id": "TENANT-1",
        "inventory_id": "UNIT-1",
        "inventory_version": 1,
        "correlation_id": "CORR-1",
        "idempotency_key": "IDEMP-1",
        "payload": {"state": "ACTIVE"},
        "occurred_at": T0,
    }

    first = inventory_updated_event(
        **kwargs
    )
    second = inventory_updated_event(
        **kwargs
    )

    compare_event_identity(
        first,
        second,
    )


def test_event_projection_to_core002_is_contract_only() -> None:
    event = inventory_created_event(
        event_id="EVENT-1",
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        inventory_version=1,
        correlation_id="CORR-1",
        idempotency_key="IDEMP-1",
        payload={
            "created": True,
        },
        occurred_at=T0,
    )

    payload = event.to_core002_payload()

    assert payload["producer"] == "CORE-004"
    assert payload["inventory_id"] == "UNIT-1"
    assert payload["event_id"] == "EVENT-1"
    assert payload["payload"] == {
        "created": True,
    }


def test_hierarchy_fingerprint_is_deterministic() -> None:
    from AUTONOMY_ENGINE.core.inventory.inventory_hierarchy import (
        project_property_relationship,
        InventoryHierarchy,
    )

    project = make_project()
    property_inventory = make_property()

    relationship = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-1",
        project_id="PROJECT-1",
        property_id="PROPERTY-1",
        at=T0,
    )

    hierarchy = InventoryHierarchy(
        tenant_id="TENANT-1",
        relationships=(relationship,),
    )

    first = hierarchy_fingerprint(
        hierarchy
    )
    second = hierarchy_fingerprint(
        hierarchy
    )

    assert first == second
