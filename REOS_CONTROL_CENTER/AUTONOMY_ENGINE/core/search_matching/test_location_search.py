from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory.inventory import (
    Inventory,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory.inventory_indexing import (
    build_inventory_index,
)
from AUTONOMY_ENGINE.core.search_matching.location_search import (
    GeoPoint,
    InvalidGeoPointError,
    InvalidLocationRadiusError,
    LocationSearchDocument,
    LocationSearchFilter,
    LocationSearchTenantError,
    haversine_distance_km,
)


def make_document(
    *,
    tenant_id: str,
    project_id: str,
    inventory_code: str,
):
    inventory = Inventory.create(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_code=inventory_code,
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name=f"Unit {inventory_code}",
    )

    return build_inventory_index(
        inventory,
        tenant_id=tenant_id,
        project_id=project_id,
    )


@pytest.fixture
def documents():
    return (
        LocationSearchDocument(
            document=make_document(
                tenant_id="tenant-001",
                project_id="project-001",
                inventory_code="UNIT-001",
            ),
            point=GeoPoint(18.5204, 73.8567),
        ),
        LocationSearchDocument(
            document=make_document(
                tenant_id="tenant-001",
                project_id="project-002",
                inventory_code="UNIT-002",
            ),
            point=GeoPoint(18.5310, 73.8470),
        ),
        LocationSearchDocument(
            document=make_document(
                tenant_id="tenant-002",
                project_id="project-003",
                inventory_code="UNIT-003",
            ),
            point=GeoPoint(18.5204, 73.8567),
        ),
    )


def test_valid_geo_point():
    point = GeoPoint(18.5204, 73.8567)
    assert point.latitude == 18.5204
    assert point.longitude == 73.8567


@pytest.mark.parametrize(
    "latitude,longitude",
    [
        (91.0, 73.8567),
        (-91.0, 73.8567),
        (18.5204, 181.0),
        (18.5204, -181.0),
    ],
)
def test_invalid_geo_point_rejected(latitude, longitude):
    with pytest.raises(InvalidGeoPointError):
        GeoPoint(latitude, longitude)


def test_empty_tenant_rejected():
    with pytest.raises(LocationSearchTenantError):
        LocationSearchFilter(
            tenant_id="",
            origin=GeoPoint(18.5204, 73.8567),
            radius_km=10,
        )


@pytest.mark.parametrize("radius", [0, -1, float("inf")])
def test_invalid_radius_rejected(radius):
    with pytest.raises(InvalidLocationRadiusError):
        LocationSearchFilter(
            tenant_id="tenant-001",
            origin=GeoPoint(18.5204, 73.8567),
            radius_km=radius,
        )


def test_same_point_distance_is_zero():
    point = GeoPoint(18.5204, 73.8567)

    assert haversine_distance_km(point, point) == pytest.approx(0.0)


def test_tenant_isolation(documents):
    result = LocationSearchFilter(
        tenant_id="tenant-001",
        origin=GeoPoint(18.5204, 73.8567),
        radius_km=100,
    ).apply(documents)

    assert len(result) == 2
    assert all(
        item.tenant_id == "tenant-001"
        for item in result
    )


def test_radius_excludes_far_document(documents):
    result = LocationSearchFilter(
        tenant_id="tenant-001",
        origin=GeoPoint(18.5204, 73.8567),
        radius_km=0.1,
    ).apply(documents)

    assert [item.inventory_code for item in result] == ["UNIT-001"]


def test_radius_boundary_is_included(documents):
    origin = GeoPoint(18.5204, 73.8567)
    boundary_distance = haversine_distance_km(
        origin,
        documents[1].point,
    )

    result = LocationSearchFilter(
        tenant_id="tenant-001",
        origin=origin,
        radius_km=boundary_distance + 1e-9,
    ).apply(documents)

    assert {
        item.inventory_code
        for item in result
    } == {"UNIT-001", "UNIT-002"}


def test_results_sorted_by_distance(documents):
    result = LocationSearchFilter(
        tenant_id="tenant-001",
        origin=GeoPoint(18.5204, 73.8567),
        radius_km=100,
    ).apply(reversed(documents))

    distances = [item.distance_km for item in result]

    assert distances == sorted(distances)


def test_search_does_not_mutate_documents(documents):
    before = tuple(
        item.document.to_dict()
        for item in documents
    )

    LocationSearchFilter(
        tenant_id="tenant-001",
        origin=GeoPoint(18.5204, 73.8567),
        radius_km=100,
    ).apply(documents)

    after = tuple(
        item.document.to_dict()
        for item in documents
    )

    assert before == after
