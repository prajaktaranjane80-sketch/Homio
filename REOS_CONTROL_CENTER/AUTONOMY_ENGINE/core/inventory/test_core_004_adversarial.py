from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import (
    AvailabilityState,
    Inventory,
    InventoryDomainError,
    InventoryIdentity,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
    LifecycleState,
)
from AUTONOMY_ENGINE.core.inventory.project import (
    Project,
    ProjectDomainError,
    ProjectIdentity,
    ProjectTenantViolation,
)
from AUTONOMY_ENGINE.core.inventory.inventory_hierarchy import (
    HierarchyValidationError,
    InventoryHierarchy,
    InventoryOrphanError,
    project_property_relationship,
    property_unit_relationship,
    reconstruct_hierarchy,
)
from AUTONOMY_ENGINE.core.inventory.inventory_lifecycle import (
    InvalidLifecycleTransition,
    LifecycleVersionConflict,
    transition_inventory_lifecycle,
    validate_lifecycle_history,
)
from AUTONOMY_ENGINE.core.inventory.inventory_availability import (
    AvailabilityVersionConflict,
    InvalidAvailabilityTransition,
    ReservationBoundaryError,
    AllocationBoundaryError,
    reserve_inventory,
    allocate_inventory,
    mark_inventory_sold,
    transition_inventory_availability,
)
from AUTONOMY_ENGINE.core.inventory.inventory_provenance import (
    InventoryProvenance,
    InventoryProvenanceError,
    InventorySource,
    InventorySourceType,
    ProvenanceEvidenceReference,
    ProvenanceHistoryEntry,
    ProvenanceIntegrityError,
    ProvenanceTenantViolation,
    validate_provenance_history,
)
from AUTONOMY_ENGINE.core.inventory.inventory_commercial_state import (
    CommercialEffectiveDateError,
    CommercialStateSnapshot,
    LocationAttributes,
    PhysicalAttributes,
    PricingReference,
    validate_historical_truth,
)
from AUTONOMY_ENGINE.core.inventory.inventory_consistency import (
    DuplicateInventoryCommand,
    InventoryConcurrencyConflict,
    InventoryCommandIdentity,
    InventoryConsistencySnapshot,
    InventoryMutationPrecondition,
    ReservationRaceConflict,
    ReservationRacePrecondition,
    assert_single_writer_version,
    compare_command_identity,
)
from AUTONOMY_ENGINE.core.inventory.inventory_security import (
    InventoryCapability,
    InventoryCapabilityViolation,
    InventoryOwnershipViolation,
    InventorySecurityContext,
    InventorySecurityContextError,
    InventoryTenantBoundaryViolation,
)
from AUTONOMY_ENGINE.core.inventory.inventory_reos_contract import (
    InventoryREOSAuthorityError,
    InventoryREOSContract,
    InventoryREOSExecutionError,
    InventoryREOSDiscovery,
    InventoryREOSIntegrationBoundary,
    InventoryREOSVerificationError,
    validate_reos_discovery,
)
from AUTONOMY_ENGINE.core.inventory.inventory_event_integration import (
    InventoryDomainEventType,
    InventoryEventValidationError,
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


def make_property(
    tenant_id: str = "TENANT-1",
) -> Inventory:
    return Inventory.create(
        tenant_id=tenant_id,
        developer_id="DEV-1",
        project_id="PROJECT-1",
        inventory_type=InventoryType.PROPERTY,
        property_id="PROPERTY-1",
        name="Property One",
        inventory_id="PROPERTY-1",
        at=T0,
    )


def make_unit(
    tenant_id: str = "TENANT-1",
) -> Inventory:
    return Inventory.create(
        tenant_id=tenant_id,
        developer_id="DEV-1",
        project_id="PROJECT-1",
        inventory_type=InventoryType.UNIT,
        property_id="PROPERTY-1",
        unit_id="UNIT-1",
        name="Unit One",
        inventory_id="UNIT-1",
        at=T0,
    )


def make_available(
    inventory: Inventory,
) -> Inventory:
    updated, _ = transition_inventory_availability(
        inventory,
        target=AvailabilityState.AVAILABLE,
        expected_version=inventory.version,
        transition_id="AVAIL-1",
        at=T0 + timedelta(minutes=1),
    )
    return updated


def test_project_identity_is_tenant_scoped() -> None:
    project = make_project()

    with pytest.raises(ProjectTenantViolation):
        project.assert_tenant("TENANT-2")


def test_invalid_project_identity_is_rejected() -> None:
    with pytest.raises(ProjectDomainError):
        ProjectIdentity(
            project_id="",
            tenant_id="TENANT-1",
            developer_id="DEV-1",
            project_code="PRJ-001",
        )


def test_inventory_identity_shape_is_fail_closed() -> None:
    with pytest.raises(InventoryDomainError):
        InventoryIdentity(
            inventory_id="DEV-1",
            tenant_id="TENANT-1",
            inventory_type=InventoryType.DEVELOPMENT,
            developer_id="DEV-1",
            project_id="PROJECT-1",
            property_id="PROPERTY-1",
        )

    with pytest.raises(InventoryDomainError):
        InventoryIdentity(
            inventory_id="PROPERTY-1",
            tenant_id="TENANT-1",
            inventory_type=InventoryType.PROPERTY,
            developer_id="DEV-1",
            project_id="PROJECT-1",
        )

    with pytest.raises(InventoryDomainError):
        InventoryIdentity(
            inventory_id="UNIT-1",
            tenant_id="TENANT-1",
            inventory_type=InventoryType.UNIT,
            developer_id="DEV-1",
            project_id="PROJECT-1",
            property_id="PROPERTY-1",
        )


def test_inventory_identity_fingerprint_is_deterministic() -> None:
    a = make_unit()
    b = make_unit()

    assert a.identity_fingerprint == b.identity_fingerprint
    assert a.identity_key == b.identity_key


def test_inventory_tenant_and_project_boundaries_are_fail_closed() -> None:
    inventory = make_property()

    with pytest.raises(InventoryTenantViolation):
        inventory.assert_tenant("TENANT-2")

    with pytest.raises(InventoryProjectViolation):
        inventory.assert_project("PROJECT-2")


def test_hierarchy_reconstruction_is_valid() -> None:
    project = make_project()
    property_inventory = make_property()
    unit_inventory = make_unit()

    relationship_project = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-1",
        project_id="PROJECT-1",
        property_id="PROPERTY-1",
        at=T0,
    )

    relationship_unit = property_unit_relationship(
        relationship_id="REL-2",
        tenant_id="TENANT-1",
        property_id="PROPERTY-1",
        unit_id="UNIT-1",
        at=T0,
    )

    hierarchy = reconstruct_hierarchy(
        tenant_id="TENANT-1",
        projects=(project,),
        inventories=(
            property_inventory,
            unit_inventory,
        ),
        relationships=(
            relationship_project,
            relationship_unit,
        ),
    )

    hierarchy.validate_complete(
        project_ids=("PROJECT-1",),
        inventories=(
            property_inventory,
            unit_inventory,
        ),
    )

    assert len(hierarchy.relationships) == 2


def test_hierarchy_orphan_is_rejected() -> None:
    hierarchy = InventoryHierarchy(
        tenant_id="TENANT-1",
        relationships=(),
    )

    with pytest.raises(InventoryOrphanError):
        hierarchy.validate_complete(
            project_ids=("PROJECT-1",),
            inventories=(make_property(),),
        )


def test_hierarchy_cross_tenant_is_rejected() -> None:
    relationship = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-2",
        project_id="PROJECT-1",
        property_id="PROPERTY-1",
        at=T0,
    )

    with pytest.raises(HierarchyValidationError):
        InventoryHierarchy(
            tenant_id="TENANT-1",
            relationships=(relationship,),
        )


def test_lifecycle_transition_and_history_are_versioned() -> None:
    inventory = make_property()

    updated, history = transition_inventory_lifecycle(
        inventory,
        target=LifecycleState.ACTIVE,
        expected_version=1,
        transition_id="LIFE-1",
        at=T0 + timedelta(minutes=1),
    )

    assert updated.version == 2
    assert updated.lifecycle is LifecycleState.ACTIVE
    assert history.from_version == 1
    assert history.to_version == 2

    validate_lifecycle_history((history,))


def test_invalid_lifecycle_transition_is_rejected() -> None:
    inventory = make_property()

    with pytest.raises(InvalidLifecycleTransition):
        transition_inventory_lifecycle(
            inventory,
            target=LifecycleState.SOLD,
            expected_version=1,
            transition_id="LIFE-BAD",
            at=T0,
        )


def test_stale_lifecycle_update_is_rejected() -> None:
    inventory = make_property()

    with pytest.raises(LifecycleVersionConflict):
        transition_inventory_lifecycle(
            inventory,
            target=LifecycleState.ACTIVE,
            expected_version=2,
            transition_id="LIFE-STALE",
            at=T0,
        )


def test_availability_reservation_allocation_sale_flow() -> None:
    available = make_available(make_property())

    reserved, _ = reserve_inventory(
        available,
        reservation_reference="RES-1",
        expected_version=2,
        transition_id="RES-1",
        at=T0 + timedelta(minutes=2),
    )

    allocated, _ = allocate_inventory(
        reserved,
        allocation_reference="ALLOC-1",
        reservation_reference="RES-1",
        expected_version=3,
        transition_id="ALLOC-1",
        at=T0 + timedelta(minutes=3),
    )

    sold, _ = mark_inventory_sold(
        allocated,
        allocation_reference="ALLOC-1",
        expected_version=4,
        transition_id="SOLD-1",
        at=T0 + timedelta(minutes=4),
    )

    assert sold.availability is AvailabilityState.SOLD
    assert sold.version == 5


def test_reservation_requires_available_state() -> None:
    inventory = make_property()

    with pytest.raises(ReservationBoundaryError):
        reserve_inventory(
            inventory,
            reservation_reference="RES-1",
            expected_version=1,
            transition_id="RES-1",
            at=T0,
        )


def test_allocation_requires_reserved_state() -> None:
    available = make_available(make_property())

    with pytest.raises(AllocationBoundaryError):
        allocate_inventory(
            available,
            allocation_reference="ALLOC-1",
            reservation_reference="RES-1",
            expected_version=2,
            transition_id="ALLOC-BAD",
            at=T0,
        )


def test_stale_availability_update_is_rejected() -> None:
    available = make_available(make_property())

    with pytest.raises(AvailabilityVersionConflict):
        reserve_inventory(
            available,
            reservation_reference="RES-1",
            expected_version=1,
            transition_id="RES-STALE",
            at=T0,
        )


def test_provenance_tenant_boundary_is_fail_closed() -> None:
    source = InventorySource(
        source_id="SOURCE-1",
        tenant_id="TENANT-2",
        source_type=InventorySourceType.BUILDER,
        source_reference="SRC-1",
        builder_developer_id="DEV-1",
    )

    with pytest.raises(ProvenanceTenantViolation):
        InventoryProvenance(
            inventory_id="UNIT-1",
            tenant_id="TENANT-1",
            source=source,
        )


def test_provenance_evidence_must_match_source() -> None:
    source = InventorySource(
        source_id="SOURCE-1",
        tenant_id="TENANT-1",
        source_type=InventorySourceType.BUILDER,
        source_reference="SRC-1",
        builder_developer_id="DEV-1",
    )

    evidence = ProvenanceEvidenceReference(
        evidence_reference="EVIDENCE-1",
        tenant_id="TENANT-1",
        evidence_type="BUILDER_MOU",
        evidence_fingerprint="a" * 64,
        recorded_at=T0,
        source_reference="SRC-OTHER",
    )

    with pytest.raises(ProvenanceIntegrityError):
        InventoryProvenance(
            inventory_id="UNIT-1",
            tenant_id="TENANT-1",
            source=source,
            evidence=(evidence,),
        )


def test_provenance_history_cannot_skip_version() -> None:
    first = ProvenanceHistoryEntry(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=1,
        provenance_fingerprint="a" * 64,
        occurred_at=T0,
        change_reference="CHANGE-1",
    )

    third = ProvenanceHistoryEntry(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=3,
        provenance_fingerprint="b" * 64,
        occurred_at=T0 + timedelta(minutes=1),
        change_reference="CHANGE-3",
    )

    with pytest.raises(InventoryProvenanceError):
        validate_provenance_history(
            (first, third)
        )


def test_commercial_state_slots_are_serializable() -> None:
    snapshot = CommercialStateSnapshot(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=1,
        physical=PhysicalAttributes(
            area_value="120.50",
            area_unit="SQFT",
            bedrooms=2,
            bathrooms="2",
            floor=5,
            facing="EAST",
            parking_count=1,
        ),
        location=LocationAttributes(
            country_code="IN",
            region="MH",
            city="Pune",
            locality="Kharadi",
        ),
        pricing=PricingReference(
            pricing_reference="PRICE-1",
            currency="INR",
            amount="12500000",
            price_type="TOTAL",
        ),
        availability_attributes={
            "view": "open",
        },
        commercial_metadata={
            "market": "residential",
        },
        effective_from=T0,
    )

    payload = snapshot.to_dict()

    assert payload["inventory_id"] == "UNIT-1"
    assert payload["pricing"]["amount"] == "12500000"
    assert snapshot.fingerprint


def test_commercial_overlapping_periods_are_rejected() -> None:
    first = CommercialStateSnapshot(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=1,
        physical=None,
        location=None,
        pricing=None,
        availability_attributes={},
        commercial_metadata={},
        effective_from=T0,
        effective_to=T0 + timedelta(days=2),
    )

    second = CommercialStateSnapshot(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=2,
        physical=None,
        location=None,
        pricing=None,
        availability_attributes={},
        commercial_metadata={},
        effective_from=T0 + timedelta(days=1),
        effective_to=None,
    )

    with pytest.raises(CommercialEffectiveDateError):
        validate_historical_truth(
            (first, second)
        )


def test_consistency_snapshot_rejects_stale_version() -> None:
    inventory = make_property()
    snapshot = InventoryConsistencySnapshot.capture(
        inventory
    )

    stale = Inventory(
        identity=inventory.identity,
        name=inventory.name,
        lifecycle=inventory.lifecycle,
        availability=inventory.availability,
        created_at=inventory.created_at,
        updated_at=T0 + timedelta(minutes=1),
        version=2,
        metadata=inventory.metadata,
    )

    with pytest.raises(InventoryConcurrencyConflict):
        snapshot.assert_current(stale)


def test_mutation_precondition_enforces_exact_state() -> None:
    inventory = make_property()
    snapshot = InventoryConsistencySnapshot.capture(
        inventory
    )

    precondition = InventoryMutationPrecondition(
        tenant_id="TENANT-1",
        inventory_id="PROPERTY-1",
        expected_version=1,
        expected_availability=AvailabilityState.UNAVAILABLE,
        idempotency_key="CMD-1",
    )

    precondition.validate_snapshot(snapshot)


def test_duplicate_command_identity_is_blocked() -> None:
    left = InventoryCommandIdentity(
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        operation="RESERVE",
        idempotency_key="IDEMP-1",
    )

    right = InventoryCommandIdentity(
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        operation="ALLOCATE",
        idempotency_key="IDEMP-1",
    )

    with pytest.raises(DuplicateInventoryCommand):
        compare_command_identity(left, right)


def test_single_writer_requires_one_version_advance() -> None:
    inventory = make_property()

    before = InventoryConsistencySnapshot.capture(
        inventory
    )

    after = InventoryConsistencySnapshot(
        tenant_id=before.tenant_id,
        inventory_id=before.inventory_id,
        version=before.version + 1,
        lifecycle=before.lifecycle,
        availability=before.availability,
        identity_fingerprint=(
            before.identity_fingerprint
        ),
    )

    assert_single_writer_version(
        before,
        after,
    )


def test_reservation_race_is_detected_after_state_change() -> None:
    available = make_available(make_property())

    race = ReservationRacePrecondition(
        tenant_id="TENANT-1",
        inventory_id="PROPERTY-1",
        expected_version=2,
        expected_state=AvailabilityState.AVAILABLE,
        reservation_reference="RES-1",
    )

    reserved, _ = reserve_inventory(
        available,
        reservation_reference="RES-1",
        expected_version=2,
        transition_id="RES-1",
        at=T0 + timedelta(minutes=2),
    )

    with pytest.raises(ReservationRaceConflict):
        race.validate(reserved)


def make_security_context(
    *,
    capabilities: frozenset[
        InventoryCapability
    ],
    ownership_scope: frozenset[str] = frozenset(),
    expires_at: datetime | None = None,
) -> InventorySecurityContext:
    return InventorySecurityContext(
        tenant_id="TENANT-1",
        actor_id="ACTOR-1",
        capabilities=capabilities,
        authorization_reference="AUTH-1",
        issued_at=T0,
        expires_at=expires_at,
        request_id="REQ-1",
        ownership_scope=ownership_scope,
    )


def test_security_tenant_isolation_and_ownership_scope() -> None:
    inventory = make_property()

    context = make_security_context(
        capabilities=frozenset(
            {
                InventoryCapability.READ_INVENTORY,
            }
        ),
        ownership_scope=frozenset(
            {"PROJECT-1"}
        ),
    )

    context.authorize_inventory_read(
        inventory
    )

    other_tenant = make_property(
        tenant_id="TENANT-2"
    )

    with pytest.raises(
        InventoryTenantBoundaryViolation
    ):
        context.authorize_inventory_read(
            other_tenant
        )


def test_security_idor_scope_is_rejected() -> None:
    inventory = make_property()

    context = make_security_context(
        capabilities=frozenset(
            {
                InventoryCapability.READ_INVENTORY,
            }
        ),
        ownership_scope=frozenset(
            {"PROJECT-OTHER"}
        ),
    )

    with pytest.raises(
        InventoryOwnershipViolation
    ):
        context.authorize_inventory_read(
            inventory
        )


def test_security_missing_mutation_capability_is_rejected() -> None:
    inventory = make_property()

    context = make_security_context(
        capabilities=frozenset(
            {
                InventoryCapability.READ_INVENTORY,
            }
        ),
    )

    with pytest.raises(
        InventoryCapabilityViolation
    ):
        context.authorize_inventory_mutation(
            inventory,
            InventoryCapability.UPDATE_INVENTORY,
        )


def test_security_expiry_is_fail_closed() -> None:
    context = make_security_context(
        capabilities=frozenset(
            {
                InventoryCapability.READ_INVENTORY,
            }
        ),
        expires_at=T0 - timedelta(seconds=1),
    )

    with pytest.raises(
        InventorySecurityContextError
    ):
        context.assert_active(
            now=T0
        )


def test_reos_cannot_authorize_mutation() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
    )

    contract.assert_authority_boundary()

    with pytest.raises(
        InventoryREOSExecutionError
    ):
        contract.assert_execution_compatible(
            command="verify-core-004",
            read_only=False,
        )


def test_reos_wrong_verification_command_is_rejected() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
    )

    with pytest.raises(
        InventoryREOSExecutionError
    ):
        contract.assert_execution_compatible(
            command="repair-core-004",
            read_only=True,
        )


def test_reos_discovery_mismatch_is_rejected() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
    )

    discovery = InventoryREOSDiscovery(
        gate_name="CORE-005",
        task_name="CORE-005-T01",
        gate_status="CURRENT",
        task_status="CURRENT",
        canonical_state_owner="REOS_CONTROL_CENTER",
        verification_command="verify-core-005",
    )

    with pytest.raises(
        InventoryREOSVerificationError
    ):
        validate_reos_discovery(
            contract,
            discovery,
        )


def test_reos_invalid_state_owner_is_rejected() -> None:
    with pytest.raises(
        InventoryREOSAuthorityError
    ):
        InventoryREOSContract(
            gate_name="CORE-004",
            task_name="CORE-004-T10",
            verification_command="verify-core-004",
            state_owner="CORE-004",
        )


def test_reos_transient_verification_failure_is_not_retried() -> None:
    calls = []

    class TransientFailure(Exception):
        pass

    def discover():
        return {
            "gate_name": "CORE-004",
            "task_name": "CORE-004-T10",
            "gate_status": "CURRENT",
            "task_status": "CURRENT",
            "canonical_state_owner": "REOS_CONTROL_CENTER",
            "verification_command": "verify-core-004",
        }

    def verify(command: str) -> bool:
        calls.append(command)
        raise TransientFailure("transient")

    boundary = InventoryREOSIntegrationBoundary(
        discover=discover,
        verify=verify,
    )

    with pytest.raises(TransientFailure):
        boundary.verify("verify-core-004")

    assert calls == ["verify-core-004"]


def test_reos_permanent_verification_failure_is_not_retried() -> None:
    calls = []

    class PermanentFailure(Exception):
        pass

    def verify(command: str) -> bool:
        calls.append(command)
        raise PermanentFailure("permanent")

    boundary = InventoryREOSIntegrationBoundary(
        discover=lambda: {},
        verify=verify,
    )

    with pytest.raises(PermanentFailure):
        boundary.verify("verify-core-004")

    assert calls == ["verify-core-004"]


def test_event_identity_and_producer_are_canonical() -> None:
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

    assert (
        event.event_type
        is InventoryDomainEventType.INVENTORY_CREATED
    )
    assert event.producer == "CORE-004"
    assert event.identity_key == (
        "TENANT-1",
        "UNIT-1",
        "IDEMP-1",
    )


def test_event_unknown_producer_is_rejected() -> None:
    with pytest.raises(
        InventoryEventValidationError
    ):
        inventory_updated_event(
            event_id="EVENT-1",
            tenant_id="TENANT-1",
            inventory_id="UNIT-1",
            inventory_version=1,
            correlation_id="CORR-1",
            idempotency_key="IDEMP-1",
            payload={},
            occurred_at=T0,
        ).__class__.create(
            event_id="EVENT-2",
            tenant_id="TENANT-1",
            inventory_id="UNIT-1",
            inventory_version=1,
            event_type=InventoryDomainEventType.INVENTORY_UPDATED,
            correlation_id="CORR-1",
            idempotency_key="IDEMP-2",
            payload={},
            occurred_at=T0,
            producer="UNAUTHORIZED",
        )


def test_core_004_has_no_duplicate_transport_or_outbox_files() -> None:
    root = Path(__file__).parent

    forbidden_file_names = {
        "inventory_kafka.py",
        "inventory_transport.py",
        "inventory_delivery.py",
        "inventory_outbox.py",
        "inventory_retry.py",
        "inventory_commission.py",
        "inventory_fraud.py",
        "inventory_governance.py",
        "inventory_manager.py",
        "inventory_service.py",
    }

    actual = {
        path.name.lower()
        for path in root.glob("*.py")
    }

    assert not (
        actual & forbidden_file_names
    )


def test_core_004_has_no_forbidden_infrastructure_imports() -> None:
    root = Path(__file__).parent

    forbidden = {
        "kafka",
        "confluent_kafka",
        "redis",
        "celery",
        "sqlalchemy",
    }

    for path in root.glob("inventory_*.py"):
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {
                    alias.name.split(".")[0]
                    for alias in node.names
                }
                assert not imported & forbidden

            if isinstance(node, ast.ImportFrom):
                module = (
                    node.module or ""
                ).split(".")[0]
                assert module not in forbidden
