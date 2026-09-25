from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import (
    Inventory,
    InventoryAvailability,
    InventoryLifecycle,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory.inventory_indexing import (
    build_inventory_index,
)
from AUTONOMY_ENGINE.core.search_matching.search_filters import (
    StructuredSearchFilter,
    StructuredSearchFilterError,
)


def make_document(
    *,
    tenant_id: str,
    project_id: str,
    inventory_code: str,
    inventory_type: InventoryType = InventoryType.RESIDENTIAL_UNIT,
    name: str = "Test Unit",
    lifecycle: InventoryLifecycle = InventoryLifecycle.ACTIVE,
    availability: InventoryAvailability = InventoryAvailability.AVAILABLE,
):
    inventory = Inventory.create(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_code=inventory_code,
        inventory_type=inventory_type,
        name=name,
    )

    if lifecycle is InventoryLifecycle.DRAFT:
        pass
    elif lifecycle is InventoryLifecycle.ARCHIVED:
        inventory, _ = inventory.transition(
            lifecycle,
            tenant_id=tenant_id,
            project_id=project_id,
        )
    else:
        if lifecycle is not InventoryLifecycle.ONBOARDING:
            inventory, _ = inventory.transition(
                InventoryLifecycle.ONBOARDING,
                tenant_id=tenant_id,
                project_id=project_id,
            )

        inventory, _ = inventory.transition(
            lifecycle,
            tenant_id=tenant_id,
            project_id=project_id,
        )

    if availability is not InventoryAvailability.AVAILABLE:
        inventory, _ = inventory.set_availability(
            availability,
            tenant_id=tenant_id,
            project_id=project_id,
        )

    return build_inventory_index(
        inventory,
        tenant_id=tenant_id,
        project_id=project_id,
    )


@pytest.fixture
def documents():
    return (
        make_document(
            tenant_id="tenant-001",
            project_id="project-001",
            inventory_code="UNIT-002",
            name="Premium Two Bedroom",
        ),
        make_document(
            tenant_id="tenant-001",
            project_id="project-002",
            inventory_code="UNIT-001",
            name="Compact Office",
            inventory_type=InventoryType.OFFICE,
        ),
        make_document(
            tenant_id="tenant-002",
            project_id="project-003",
            inventory_code="UNIT-003",
            name="Other Tenant Unit",
        ),
    )


def test_tenant_scope_is_mandatory():
    with pytest.raises(StructuredSearchFilterError):
        StructuredSearchFilter(tenant_id="")


def test_tenant_isolation_is_always_enforced(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
    ).apply(documents)

    assert len(result) == 2
    assert all(item.tenant_id == "tenant-001" for item in result)


def test_project_filter(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        project_ids=("project-002",),
    ).apply(documents)

    assert [item.inventory_code for item in result] == ["UNIT-001"]


def test_inventory_type_filter(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        inventory_types=(InventoryType.OFFICE,),
    ).apply(documents)

    assert len(result) == 1
    assert result[0].inventory_type == InventoryType.OFFICE.value


def test_availability_filter(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        availability_states=(InventoryAvailability.AVAILABLE,),
    ).apply(documents)

    assert len(result) == 2


def test_lifecycle_filter(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        lifecycle_states=(InventoryLifecycle.ACTIVE,),
    ).apply(documents)

    assert len(result) == 2


def test_inventory_code_filter(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        inventory_codes=("UNIT-002",),
    ).apply(documents)

    assert [item.inventory_code for item in result] == ["UNIT-002"]


def test_name_contains_is_case_insensitive(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        name_contains="PREMIUM",
    ).apply(documents)

    assert len(result) == 1
    assert result[0].inventory_code == "UNIT-002"


def test_multiple_filters_are_combined(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
        project_ids=("project-001",),
        inventory_types=(InventoryType.RESIDENTIAL_UNIT,),
        availability_states=(InventoryAvailability.AVAILABLE,),
    ).apply(documents)

    assert len(result) == 1
    assert result[0].inventory_code == "UNIT-002"


def test_empty_filter_returns_only_tenant_records(documents):
    result = StructuredSearchFilter(
        tenant_id="tenant-001",
    ).apply(documents)

    assert [item.tenant_id for item in result] == [
        "tenant-001",
        "tenant-001",
    ]

    assert [item.index_key for item in result] == sorted(
        [item.index_key for item in result],
        key=str.casefold,
    )


def test_result_order_is_deterministic(documents):
    first = StructuredSearchFilter(
        tenant_id="tenant-001",
    ).apply(reversed(documents))

    second = StructuredSearchFilter(
        tenant_id="tenant-001",
    ).apply(documents)

    assert [
        item.index_key for item in first
    ] == [
        item.index_key for item in second
    ]


def test_filter_does_not_mutate_documents(documents):
    before = tuple(item.to_dict() for item in documents)

    StructuredSearchFilter(
        tenant_id="tenant-001",
        project_ids=("project-001",),
    ).apply(documents)

    after = tuple(item.to_dict() for item in documents)

    assert before == after
