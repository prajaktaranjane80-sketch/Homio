from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import (
    AvailabilityState,
    Inventory,
    InventoryDomainError,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
    LifecycleState,
)
from AUTONOMY_ENGINE.core.inventory.project import (
    Project,
    ProjectIdentity,
    ProjectTenantViolation,
)
from AUTONOMY_ENGINE.core.inventory.inventory_hierarchy import (
    HierarchyNodeRef,
    HierarchyNodeType,
    InventoryHierarchy,
    InventoryHierarchyError,
    InventoryOrphanError,
    project_property_relationship,
    property_unit_relationship,
    reconstruct_hierarchy,
)
from AUTONOMY_ENGINE.core.inventory.inventory_lifecycle import (
    InvalidLifecycleTransition,
    LifecycleVersionConflict,
    InventoryLifecycleError,
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
    release_reservation,
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
    CommercialIntegrityError,
    CommercialStateSnapshot,
    LocationAttributes,
    PhysicalAttributes,
    PricingReference,
    validate_historical_truth,
)
from AUTONOMY_ENGINE.core.inventory.inventory_consistency import (
    DuplicateInventoryCommand,
    InventoryConcurrencyConflict,
    InventoryConsistencySnapshot,
    InventoryCommandIdentity,
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
    InventoryREOSDiscovery,
    InventoryREOSExecutionError,
    InventoryREOSIntegrationBoundary,
    InventoryREOSVerificationError,
    REOSVerificationMode,
    validate_reos_discovery,
)


UTC = timezone.utc
T0 = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)


def make_project(
    *,
    tenant_id: str = "TENANT-1",
    project_id: str = "PROJECT-1",
    developer_id: str = "DEV-1",
    project_code: str = "PRJ-001",
) -> Project:
    return Project(
        identity=ProjectIdentity(
            project_id=project_id,
            tenant_id=tenant_id,
            developer_id=developer_id,
            project_code=project_code,
        ),
        name="Project One",
        metadata={"region": "IN"},
    )


def make_property(
    *,
    tenant_id: str = "TENANT-1",
    project_id: str = "PROJECT-1",
    inventory_id: str = "PROPERTY-1",
) -> Inventory:
    return Inventory.create(
        tenant_id=tenant_id,
        developer_id="DEV-1",
        project_id=project_id,
        inventory_type=InventoryType.PROPERTY,
        name="Property One",
        property_id=inventory_id,
        inventory_id=inventory_id,
        at=T0,
        metadata={"source": "builder"},
    )


def make_unit(
    *,
    tenant_id: str = "TENANT-1",
    project_id: str = "PROJECT-1",
    property_id: str = "PROPERTY-1",
    inventory_id: str = "UNIT-1",
) -> Inventory:
    return Inventory.create(
        tenant_id=tenant_id,
        developer_id="DEV-1",
        project_id=project_id,
        inventory_type=InventoryType.UNIT,
        name="Unit One",
        property_id=property_id,
        unit_id=inventory_id,
        inventory_id=inventory_id,
        at=T0,
    )


def make_available(inventory: Inventory) -> Inventory:
    updated, _ = transition_inventory_availability(
        inventory,
        target=AvailabilityState.AVAILABLE,
        expected_version=inventory.version,
        transition_id="AVAIL-1",
        at=T0 + timedelta(minutes=1),
    )
    return updated


def make_source(
    *,
    tenant_id: str = "TENANT-1",
    source_reference: str = "SRC-1",
) -> InventorySource:
    return InventorySource(
        source_id="SOURCE-1",
        tenant_id=tenant_id,
        source_type=InventorySourceType.BUILDER,
        source_reference=source_reference,
        builder_developer_id="DEV-1",
        acquisition_reference="ACQ-1",
        channel_reference="CHANNEL-1",
        metadata={"origin": "builder"},
    )


def make_snapshot(
    inventory: Inventory,
) -> InventoryConsistencySnapshot:
    return InventoryConsistencySnapshot.capture(inventory)


# ---------------------------------------------------------------------------
# T01 — DOMAIN / IDENTITY
# ---------------------------------------------------------------------------


def test_development_identity_cannot_carry_property_or_unit() -> None:
    with pytest.raises(InventoryDomainError):
        Inventory.create(
            tenant_id="TENANT-1",
            developer_id="DEV-1",
            project_id="PROJECT-1",
            inventory_type=InventoryType.DEVELOPMENT,
            name="Development",
            property_id="PROPERTY-1",
            inventory_id="DEV-INV-1",
            at=T0,
        )


def test_property_identity_requires_property_id() -> None:
    with pytest.raises(InventoryDomainError):
        Inventory.create(
            tenant_id="TENANT-1",
            developer_id="DEV-1",
            project_id="PROJECT-1",
            inventory_type=InventoryType.PROPERTY,
            name="Property",
            inventory_id="PROPERTY-1",
            at=T0,
        )


def test_unit_identity_requires_property_and_unit() -> None:
    with pytest.raises(InventoryDomainError):
        Inventory.create(
            tenant_id="TENANT-1",
            developer_id="DEV-1",
            project_id="PROJECT-1",
            inventory_type=InventoryType.UNIT,
            name="Unit",
            unit_id="UNIT-1",
            inventory_id="UNIT-1",
            at=T0,
        )


def test_project_tenant_boundary_is_enforced() -> None:
    project = make_project()

    with pytest.raises(ProjectTenantViolation):
        project.assert_tenant("TENANT-2")


def test_inventory_tenant_and_project_boundaries_are_enforced() -> None:
    inventory = make_property()

    with pytest.raises(InventoryTenantViolation):
        inventory.assert_tenant("TENANT-2")

    with pytest.raises(InventoryProjectViolation):
        inventory.assert_project("PROJECT-2")


def test_identity_fingerprint_is_deterministic() -> None:
    left = make_property(inventory_id="PROPERTY-A")
    right = make_property(inventory_id="PROPERTY-A")

    assert left.identity_fingerprint == right.identity_fingerprint
    assert left.identity_key == right.identity_key


def test_identity_fingerprint_changes_for_identity_mutation() -> None:
    left = make_property(inventory_id="PROPERTY-A")
    right = make_property(inventory_id="PROPERTY-B")

    assert left.identity_fingerprint != right.identity_fingerprint


def test_inventory_baseline_is_immutable_and_versioned() -> None:
    inventory = make_property()

    assert inventory.lifecycle is LifecycleState.DRAFT
    assert inventory.availability is AvailabilityState.UNAVAILABLE
    assert inventory.version == 1

    with pytest.raises(Exception):
        inventory.version = 9  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T03 — HIERARCHY
# ---------------------------------------------------------------------------


def test_project_property_and_property_unit_edges_are_valid() -> None:
    project = make_project()
    property_inventory = make_property()
    unit_inventory = make_unit()

    project_edge = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-1",
        project_id=project.project_id,
        property_id=property_inventory.inventory_id,
        at=T0,
    )

    unit_edge = property_unit_relationship(
        relationship_id="REL-2",
        tenant_id="TENANT-1",
        property_id=property_inventory.inventory_id,
        unit_id=unit_inventory.inventory_id,
        at=T0,
    )

    hierarchy = InventoryHierarchy(
        tenant_id="TENANT-1",
        relationships=(project_edge, unit_edge),
    )

    hierarchy.validate_complete(
        project_ids=(project.project_id,),
        inventories=(property_inventory, unit_inventory),
    )

    assert len(hierarchy.relationships) == 2


def test_hierarchy_reconstruction_preserves_structure() -> None:
    project = make_project()
    property_inventory = make_property()
    unit_inventory = make_unit()

    project_edge = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-1",
        project_id=project.project_id,
        property_id=property_inventory.inventory_id,
        at=T0,
    )

    unit_edge = property_unit_relationship(
        relationship_id="REL-2",
        tenant_id="TENANT-1",
        property_id=property_inventory.inventory_id,
        unit_id=unit_inventory.inventory_id,
        at=T0,
    )

    reconstructed = reconstruct_hierarchy(
        tenant_id="TENANT-1",
        projects=(project,),
        inventories=(property_inventory, unit_inventory),
        relationships=(project_edge, unit_edge),
    )

    assert reconstructed.tenant_id == "TENANT-1"
    assert len(reconstructed.relationships) == 2
    assert reconstructed.parent_of(
        HierarchyNodeRef(
            HierarchyNodeType.PROPERTY,
            "PROPERTY-1",
        )
    ) is not None


def test_property_without_project_parent_is_rejected() -> None:
    project = make_project()
    property_inventory = make_property()

    hierarchy = InventoryHierarchy(
        tenant_id="TENANT-1",
        relationships=(),
    )

    with pytest.raises(InventoryOrphanError):
        hierarchy.validate_complete(
            project_ids=(project.project_id,),
            inventories=(property_inventory,),
        )


def test_unit_without_property_parent_is_rejected() -> None:
    project = make_project()
    property_inventory = make_property()
    unit_inventory = make_unit()

    project_edge = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-1",
        project_id=project.project_id,
        property_id=property_inventory.inventory_id,
        at=T0,
    )

    hierarchy = InventoryHierarchy(
        tenant_id="TENANT-1",
        relationships=(project_edge,),
    )

    with pytest.raises(InventoryOrphanError):
        hierarchy.validate_complete(
            project_ids=(project.project_id,),
            inventories=(property_inventory, unit_inventory),
        )


def test_duplicate_relationship_is_rejected() -> None:
    relationship = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-1",
        project_id="PROJECT-1",
        property_id="PROPERTY-1",
        at=T0,
    )

    with pytest.raises(InventoryHierarchyError):
        InventoryHierarchy(
            tenant_id="TENANT-1",
            relationships=(relationship, relationship),
        )


def test_cross_tenant_hierarchy_is_rejected() -> None:
    relationship = project_property_relationship(
        relationship_id="REL-1",
        tenant_id="TENANT-2",
        project_id="PROJECT-1",
        property_id="PROPERTY-1",
        at=T0,
    )

    with pytest.raises(InventoryHierarchyError):
        InventoryHierarchy(
            tenant_id="TENANT-1",
            relationships=(relationship,),
        )


# ---------------------------------------------------------------------------
# T04 — LIFECYCLE
# ---------------------------------------------------------------------------


def test_lifecycle_transition_advances_exactly_one_version() -> None:
    inventory = make_property()

    updated, history = transition_inventory_lifecycle(
        inventory,
        target=LifecycleState.ACTIVE,
        expected_version=1,
        transition_id="LIFE-1",
        actor_reference="ACTOR-1",
        reason="publish",
        at=T0 + timedelta(minutes=5),
    )

    assert updated.version == 2
    assert updated.lifecycle is LifecycleState.ACTIVE
    assert history.from_version == 1
    assert history.to_version == 2
    assert history.to_state is LifecycleState.ACTIVE


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


def test_stale_lifecycle_version_is_rejected() -> None:
    inventory = make_property()

    with pytest.raises(LifecycleVersionConflict):
        transition_inventory_lifecycle(
            inventory,
            target=LifecycleState.ACTIVE,
            expected_version=0,
            transition_id="LIFE-STALE",
            at=T0,
        )


def test_lifecycle_history_continuity_is_validated() -> None:
    inventory = make_property()

    active, first = transition_inventory_lifecycle(
        inventory,
        target=LifecycleState.ACTIVE,
        expected_version=1,
        transition_id="LIFE-1",
        at=T0 + timedelta(minutes=1),
    )

    reserved, second = transition_inventory_lifecycle(
        active,
        target=LifecycleState.RESERVED,
        expected_version=2,
        transition_id="LIFE-2",
        at=T0 + timedelta(minutes=2),
    )

    validate_lifecycle_history((first, second))

    assert reserved.version == 3


# ---------------------------------------------------------------------------
# T05 — AVAILABILITY / RESERVATION / ALLOCATION
# ---------------------------------------------------------------------------


def test_reservation_requires_available_inventory() -> None:
    inventory = make_property()

    with pytest.raises(ReservationBoundaryError):
        reserve_inventory(
            inventory,
            reservation_reference="RES-1",
            expected_version=1,
            transition_id="RES-1",
            at=T0,
        )


def test_full_availability_flow_is_monotonic() -> None:
    available = make_available(make_property())

    reserved, reservation = reserve_inventory(
        available,
        reservation_reference="RES-1",
        expected_version=2,
        transition_id="AV-RES-1",
        at=T0 + timedelta(minutes=2),
    )

    allocated, allocation = allocate_inventory(
        reserved,
        allocation_reference="ALLOC-1",
        reservation_reference="RES-1",
        expected_version=3,
        transition_id="AV-ALLOC-1",
        at=T0 + timedelta(minutes=3),
    )

    sold, sale = mark_inventory_sold(
        allocated,
        allocation_reference="ALLOC-1",
        expected_version=4,
        transition_id="AV-SOLD-1",
        at=T0 + timedelta(minutes=4),
    )

    assert reservation.to_state is AvailabilityState.RESERVED
    assert allocation.to_state is AvailabilityState.ALLOCATED
    assert sale.to_state is AvailabilityState.SOLD
    assert sold.availability is AvailabilityState.SOLD
    assert sold.version == 5


def test_allocation_without_reservation_is_rejected() -> None:
    available = make_available(make_property())

    with pytest.raises(AllocationBoundaryError):
        allocate_inventory(
            available,
            allocation_reference="ALLOC-1",
            reservation_reference="RES-1",
            expected_version=2,
            transition_id="AV-ALLOC-BAD",
            at=T0,
        )


def test_stale_availability_version_is_rejected() -> None:
    available = make_available(make_property())

    with pytest.raises(AvailabilityVersionConflict):
        reserve_inventory(
            available,
            reservation_reference="RES-1",
            expected_version=1,
            transition_id="AV-STALE",
            at=T0,
        )


def test_invalid_direct_availability_transition_is_rejected() -> None:
    inventory = make_property()

    with pytest.raises(
        (
            InvalidAvailabilityTransition,
            ReservationBoundaryError,
        )
    ):
        transition_inventory_availability(
            inventory,
            target=AvailabilityState.RESERVED,
            expected_version=1,
            transition_id="AV-BAD",
            at=T0,
        )


def test_reservation_can_be_released_only_from_reserved_state() -> None:
    available = make_available(make_property())

    with pytest.raises(Exception):
        release_reservation(
            available,
            reservation_reference="RES-1",
            expected_version=2,
            transition_id="REL-RES-BAD",
            at=T0,
        )


# ---------------------------------------------------------------------------
# T06 — PROVENANCE
# ---------------------------------------------------------------------------


def test_provenance_source_and_evidence_integrity() -> None:
    source = make_source()

    evidence = ProvenanceEvidenceReference(
        evidence_reference="EVIDENCE-1",
        tenant_id="TENANT-1",
        evidence_type="BUILDER_MOU",
        evidence_fingerprint="a" * 64,
        recorded_at=T0,
        source_reference="SRC-1",
    )

    provenance = InventoryProvenance(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        source=source,
        evidence=(evidence,),
        provenance_version=1,
    )

    provenance.assert_integrity()

    assert provenance.to_dict()["inventory_id"] == "UNIT-1"
    assert len(provenance.evidence) == 1
    assert provenance.fingerprint


def test_provenance_cross_tenant_source_is_rejected() -> None:
    with pytest.raises(ProvenanceTenantViolation):
        InventoryProvenance(
            inventory_id="UNIT-1",
            tenant_id="TENANT-1",
            source=make_source(tenant_id="TENANT-2"),
        )


def test_provenance_cross_source_evidence_is_rejected() -> None:
    source = make_source(source_reference="SRC-1")

    evidence = ProvenanceEvidenceReference(
        evidence_reference="EVIDENCE-1",
        tenant_id="TENANT-1",
        evidence_type="BUILDER_MOU",
        evidence_fingerprint="a" * 64,
        recorded_at=T0,
        source_reference="SRC-2",
    )

    with pytest.raises(ProvenanceIntegrityError):
        InventoryProvenance(
            inventory_id="UNIT-1",
            tenant_id="TENANT-1",
            source=source,
            evidence=(evidence,),
        )


def test_provenance_history_requires_contiguous_versions() -> None:
    first = ProvenanceHistoryEntry(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=1,
        provenance_fingerprint="a" * 64,
        occurred_at=T0,
        change_reference="CHANGE-1",
    )

    gap = ProvenanceHistoryEntry(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=3,
        provenance_fingerprint="b" * 64,
        occurred_at=T0 + timedelta(minutes=1),
        change_reference="CHANGE-3",
    )

    with pytest.raises(InventoryProvenanceError):
        validate_provenance_history((first, gap))


# ---------------------------------------------------------------------------
# T07 — COMMERCIAL STATE / HISTORICAL TRUTH
# ---------------------------------------------------------------------------


def make_commercial_snapshot(
    *,
    version: int,
    effective_from: datetime,
    effective_to: datetime | None,
) -> CommercialStateSnapshot:
    return CommercialStateSnapshot(
        inventory_id="UNIT-1",
        tenant_id="TENANT-1",
        version=version,
        physical=PhysicalAttributes(
            area_value=Decimal("120.50"),
            area_unit="SQFT",
            bedrooms=2,
            bathrooms=Decimal("2.00"),
            floor=5,
            facing="EAST",
            parking_count=1,
        ),
        location=LocationAttributes(
            country_code="IN",
            region="MH",
            city="Pune",
            locality="Kharadi",
            postal_code="411014",
            address_line="Test Address",
            latitude=Decimal("18.5510"),
            longitude=Decimal("73.9340"),
        ),
        pricing=PricingReference(
            pricing_reference="PRICE-1",
            currency="INR",
            amount=Decimal("12500000"),
            price_type="TOTAL",
            external_version="P1",
        ),
        availability_attributes={"view": "open"},
        commercial_metadata={"market": "residential"},
        effective_from=effective_from,
        effective_to=effective_to,
    )


def test_commercial_snapshot_serialization_and_fingerprint() -> None:
    snapshot = make_commercial_snapshot(
        version=1,
        effective_from=T0,
        effective_to=T0 + timedelta(days=1),
    )

    serialized = snapshot.to_dict()

    assert serialized["inventory_id"] == "UNIT-1"
    assert serialized["tenant_id"] == "TENANT-1"
    assert serialized["version"] == 1
    assert snapshot.fingerprint


def test_commercial_history_accepts_adjacent_effective_periods() -> None:
    first = make_commercial_snapshot(
        version=1,
        effective_from=T0,
        effective_to=T0 + timedelta(days=1),
    )
    second = make_commercial_snapshot(
        version=2,
        effective_from=T0 + timedelta(days=1),
        effective_to=None,
    )

    validate_historical_truth((first, second))


def test_commercial_history_rejects_overlapping_periods() -> None:
    first = make_commercial_snapshot(
        version=1,
        effective_from=T0,
        effective_to=T0 + timedelta(days=1),
    )
    second = make_commercial_snapshot(
        version=2,
        effective_from=T0 + timedelta(hours=12),
        effective_to=None,
    )

    with pytest.raises(
        (
            CommercialEffectiveDateError,
            CommercialIntegrityError,
        )
    ):
        validate_historical_truth((first, second))


# ---------------------------------------------------------------------------
# T08 — CONSISTENCY / CONCURRENCY / IDEMPOTENCY / RACE
# ---------------------------------------------------------------------------


def test_consistency_snapshot_matches_current_inventory() -> None:
    inventory = make_property()
    snapshot = make_snapshot(inventory)

    snapshot.assert_current(inventory)


def test_consistency_snapshot_rejects_stale_inventory() -> None:
    inventory = make_property()
    snapshot = make_snapshot(inventory)

    newer = replace(
        inventory,
        version=2,
        updated_at=T0 + timedelta(minutes=1),
    )

    with pytest.raises(InventoryConcurrencyConflict):
        snapshot.assert_current(newer)


def test_mutation_precondition_accepts_matching_snapshot() -> None:
    inventory = make_property()
    snapshot = make_snapshot(inventory)

    precondition = InventoryMutationPrecondition(
        tenant_id="TENANT-1",
        inventory_id="PROPERTY-1",
        expected_version=1,
        expected_availability=AvailabilityState.UNAVAILABLE,
        idempotency_key="CMD-1",
    )

    precondition.validate_snapshot(snapshot)


def test_mutation_precondition_rejects_wrong_version() -> None:
    inventory = make_property()
    snapshot = make_snapshot(inventory)

    precondition = InventoryMutationPrecondition(
        tenant_id="TENANT-1",
        inventory_id="PROPERTY-1",
        expected_version=2,
        expected_availability=AvailabilityState.UNAVAILABLE,
        idempotency_key="CMD-1",
    )

    with pytest.raises(InventoryConcurrencyConflict):
        precondition.validate_snapshot(snapshot)


def test_duplicate_command_identity_conflict_is_blocked() -> None:
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


def test_same_command_identity_and_operation_is_allowed() -> None:
    left = InventoryCommandIdentity(
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        operation="RESERVE",
        idempotency_key="IDEMP-1",
    )
    right = InventoryCommandIdentity(
        tenant_id="TENANT-1",
        inventory_id="UNIT-1",
        operation="RESERVE",
        idempotency_key="IDEMP-1",
    )

    compare_command_identity(left, right)


def test_single_writer_requires_exactly_one_version_advance() -> None:
    inventory = make_property()
    before = make_snapshot(inventory)

    after = replace(
        before,
        version=2,
    )

    assert_single_writer_version(before, after)


def test_single_writer_rejects_multiple_version_jump() -> None:
    inventory = make_property()
    before = make_snapshot(inventory)

    after = replace(
        before,
        version=4,
    )

    with pytest.raises(InventoryConcurrencyConflict):
        assert_single_writer_version(before, after)


def test_reservation_race_precondition_matches_available_inventory() -> None:
    available = make_available(make_property())

    precondition = ReservationRacePrecondition(
        tenant_id="TENANT-1",
        inventory_id="PROPERTY-1",
        expected_version=2,
        expected_state=AvailabilityState.AVAILABLE,
        reservation_reference="RES-1",
    )

    precondition.validate(available)


def test_reservation_race_rejects_stale_state() -> None:
    available = make_available(make_property())

    reserved, _ = reserve_inventory(
        available,
        reservation_reference="RES-1",
        expected_version=2,
        transition_id="RES-TRANS-1",
        at=T0 + timedelta(minutes=2),
    )

    precondition = ReservationRacePrecondition(
        tenant_id="TENANT-1",
        inventory_id="PROPERTY-1",
        expected_version=2,
        expected_state=AvailabilityState.AVAILABLE,
        reservation_reference="RES-1",
    )

    with pytest.raises(ReservationRaceConflict):
        precondition.validate(reserved)


# ---------------------------------------------------------------------------
# T09 — SECURITY / TENANT / AUTHORIZATION / IDOR
# ---------------------------------------------------------------------------


def security_context(
    *,
    tenant_id: str = "TENANT-1",
    actor_id: str = "ACTOR-1",
    capabilities: frozenset[InventoryCapability] | None = None,
    ownership_scope: frozenset[str] = frozenset(),
    expires_at: datetime | None = None,
) -> InventorySecurityContext:
    return InventorySecurityContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        capabilities=(
            capabilities
            if capabilities is not None
            else frozenset(
                {
                    InventoryCapability.READ_INVENTORY,
                    InventoryCapability.UPDATE_INVENTORY,
                    InventoryCapability.READ_COMMERCIAL_STATE,
                }
            )
        ),
        authorization_reference="AUTH-1",
        issued_at=T0,
        expires_at=expires_at,
        request_id="REQ-1",
        ownership_scope=ownership_scope,
    )


def test_security_read_authorization_accepts_same_tenant_and_scope() -> None:
    inventory = make_property()

    context = security_context(
        ownership_scope=frozenset({"PROJECT-1"}),
    )

    context.authorize_inventory_read(inventory)


def test_security_cross_tenant_access_is_rejected() -> None:
    inventory = make_property(tenant_id="TENANT-2")
    context = security_context()

    with pytest.raises(InventoryTenantBoundaryViolation):
        context.authorize_inventory_read(inventory)


def test_security_missing_mutation_capability_is_rejected() -> None:
    inventory = make_property()

    context = security_context(
        capabilities=frozenset(
            {InventoryCapability.READ_INVENTORY}
        )
    )

    with pytest.raises(InventoryCapabilityViolation):
        context.authorize_inventory_mutation(
            inventory,
            InventoryCapability.UPDATE_INVENTORY,
        )


def test_security_idor_scope_is_rejected() -> None:
    inventory = make_property()

    context = security_context(
        ownership_scope=frozenset({"PROJECT-OTHER"}),
    )

    with pytest.raises(InventoryOwnershipViolation):
        context.authorize_inventory_read(inventory)


def test_expired_security_context_is_rejected() -> None:
    context = security_context(
        expires_at=T0 - timedelta(seconds=1),
    )

    with pytest.raises(InventorySecurityContextError):
        context.assert_active(now=T0)


# ---------------------------------------------------------------------------
# T10 / T11 — REOS / ACRL BOUNDARY
# ---------------------------------------------------------------------------


def test_reos_contract_keeps_canonical_state_external() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
        verification_mode=REOSVerificationMode.VERIFY_ONLY,
    )

    contract.assert_authority_boundary()
    contract.assert_execution_compatible(
        command="verify-core-004",
        read_only=True,
    )


def test_reos_contract_blocks_state_mutating_execution() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
    )

    with pytest.raises(InventoryREOSExecutionError):
        contract.assert_execution_compatible(
            command="verify-core-004",
            read_only=False,
        )


def test_reos_contract_blocks_wrong_verification_command() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
    )

    with pytest.raises(InventoryREOSExecutionError):
        contract.assert_execution_compatible(
            command="repair-core-004",
            read_only=True,
        )


def test_reos_contract_blocks_invalid_state_owner() -> None:
    contract = InventoryREOSContract(
        gate_name="CORE-004",
        task_name="CORE-004-T10",
        verification_command="verify-core-004",
        state_owner="CORE-004",
    )

    with pytest.raises(InventoryREOSAuthorityError):
        contract.assert_authority_boundary()


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

    with pytest.raises(InventoryREOSVerificationError):
        validate_reos_discovery(contract, discovery)


def test_reos_boundary_is_read_verify_only() -> None:
    calls: list[str] = []

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
        return command == "verify-core-004"

    boundary = InventoryREOSIntegrationBoundary(
        discover=discover,
        verify=verify,
    )

    result = boundary.discover_contract()

    assert result.gate_name == "CORE-004"
    assert boundary.verify("verify-core-004") is True
    assert calls == ["verify-core-004"]
