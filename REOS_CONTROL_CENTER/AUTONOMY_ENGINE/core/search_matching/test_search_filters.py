from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import (
    AvailabilityState,
    InventoryType,
    LifecycleState,
)
from AUTONOMY_ENGINE.core.search_matching.search_filters import (
    StructuredSearchFilter,
    StructuredSearchFilterError,
    StructuredSearchTenantError,
)
from AUTONOMY_ENGINE.core.search_matching.search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


def make_document(
    *,
    tenant_id: str = "tenant-a",
    project_id: str = "project-a",
    inventory_id: str = "inventory-a",
    inventory_code: str = "UNIT-101",
    inventory_type: str = "UNIT",
    lifecycle: str = "ACTIVE",
    availability: str = "AVAILABLE",
    name: str = "Skyline Residency",
    index_key: str | None = None,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_id=inventory_id,
        inventory_code=inventory_code,
        inventory_type=inventory_type,
        lifecycle=lifecycle,
        availability=availability,
        name=name,
        inventory_version=1,
        index_key=index_key or f"{tenant_id}:{inventory_id}",
        operation=SearchIndexOperation.UPSERT,
    )


def test_tenant_is_mandatory() -> None:
    with pytest.raises(StructuredSearchTenantError):
        StructuredSearchFilter(tenant_id="")


def test_invalid_enum_value_is_rejected() -> None:
    with pytest.raises(StructuredSearchFilterError):
        StructuredSearchFilter(
            tenant_id="tenant-a",
            inventory_types=("NOT_A_TYPE",),
        )


def test_single_string_collection_is_rejected() -> None:
    with pytest.raises(StructuredSearchFilterError):
        StructuredSearchFilter(
            tenant_id="tenant-a",
            project_ids="project-a",
        )


def test_tenant_boundary_is_enforced_first() -> None:
    document = make_document(
        tenant_id="tenant-b",
        project_id="project-a",
    )

    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
        project_ids=("project-a",),
    )

    assert search_filter.matches(document) is False


def test_all_structured_predicates_can_match() -> None:
    document = make_document(
        tenant_id="tenant-a",
        project_id="project-a",
        inventory_code="UNIT-101",
        inventory_type=InventoryType.UNIT.value,
        lifecycle=LifecycleState.ACTIVE.value,
        availability=AvailabilityState.AVAILABLE.value,
        name="Skyline Luxury Residency",
    )

    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
        project_ids=("project-a",),
        inventory_codes=("UNIT-101",),
        inventory_types=(InventoryType.UNIT,),
        lifecycle_states=(LifecycleState.ACTIVE,),
        availability_states=(AvailabilityState.AVAILABLE,),
        name_contains="luxury",
    )

    assert search_filter.matches(document) is True


def test_non_matching_project_is_rejected() -> None:
    document = make_document(
        project_id="project-b",
    )

    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
        project_ids=("project-a",),
    )

    assert search_filter.matches(document) is False


def test_apply_is_deterministic() -> None:
    first = make_document(
        inventory_id="b",
        index_key="tenant-a:b",
    )
    second = make_document(
        inventory_id="a",
        index_key="tenant-a:a",
    )

    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
    )

    result = search_filter.apply(
        [first, second]
    )

    assert tuple(
        item.inventory_id
        for item in result
    ) == ("a", "b")


def test_apply_never_mutates_source_sequence() -> None:
    first = make_document(
        inventory_id="b",
        index_key="tenant-a:b",
    )
    second = make_document(
        inventory_id="a",
        index_key="tenant-a:a",
    )

    source = [first, second]

    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
    )

    result = search_filter.apply(source)

    assert source == [first, second]
    assert result == (second, first)


def test_invalid_document_type_is_rejected() -> None:
    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
    )

    with pytest.raises(StructuredSearchFilterError):
        search_filter.matches(
            object()  # type: ignore[arg-type]
        )


def test_filter_is_immutable() -> None:
    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
        project_ids=("project-a",),
    )

    with pytest.raises(AttributeError):
        search_filter.tenant_id = "tenant-b"  # type: ignore[misc]


def test_empty_result_is_stable() -> None:
    search_filter = StructuredSearchFilter(
        tenant_id="tenant-a",
    )

    assert search_filter.apply([]) == ()
