from __future__ import annotations

import pytest

from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.core.inventory.inventory import (
    Inventory,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory.inventory_indexing import (
    build_inventory_index,
    build_inventory_index_delete,
)
from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
    QdrantTenantViolation,
    QdrantVectorError,
    QdrantVersionViolation,
    deterministic_point_id,
)


def make_document(
    *,
    operation: str = "UPSERT",
):
    inventory = Inventory.create(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Test Unit",
    )

    if operation == "DELETE":
        return build_inventory_index_delete(
            inventory,
            tenant_id="tenant-001",
            project_id="project-001",
        )

    return build_inventory_index(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )


@pytest.fixture
def pipeline():
    return QdrantIndexingPipeline(
        client=QdrantClient(":memory:"),
        config=QdrantIndexingConfig(
            collection_name="test_inventory_vectors",
            vector_size=4,
        ),
    )


def test_deterministic_point_id_is_stable():
    first = deterministic_point_id(
        "tenant-001:project-001:UNIT-001"
    )
    second = deterministic_point_id(
        "tenant-001:project-001:UNIT-001"
    )

    assert first == second


def test_different_inventory_keys_get_different_ids():
    first = deterministic_point_id(
        "tenant-001:project-001:UNIT-001"
    )
    second = deterministic_point_id(
        "tenant-001:project-001:UNIT-002"
    )

    assert first != second


def test_collection_is_created(pipeline):
    pipeline.ensure_collection()

    collections = pipeline.client.get_collections().collections

    assert any(
        item.name == "test_inventory_vectors"
        for item in collections
    )


def test_build_point_preserves_canonical_identity(pipeline):
    document = make_document()

    point = pipeline.build_point(
        document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-001",
    )

    assert str(point.id) == deterministic_point_id(
        document.index_key
    )
    assert point.payload["inventory_id"] == document.inventory_id
    assert point.payload["tenant_id"] == "tenant-001"
    assert point.payload["project_id"] == "project-001"
    assert point.payload["inventory_version"] == 1


def test_upsert_writes_one_point(pipeline):
    document = make_document()

    point_id = pipeline.upsert(
        document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-001",
    )

    points = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[point_id],
    )

    assert len(points) == 1
    assert points[0].payload["inventory_code"] == "UNIT-001"


def test_upsert_is_idempotent_for_same_inventory(pipeline):
    document = make_document()

    first = pipeline.upsert(
        document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-001",
    )

    second = pipeline.upsert(
        document,
        [0.4, 0.3, 0.2, 0.1],
        tenant_id="tenant-001",
    )

    assert first == second

    points = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[first],
        with_vectors=True,
    )

    assert len(points) == 1

    stored = points[0].vector
    assert stored is not None

    expected_source = [0.4, 0.3, 0.2, 0.1]
    norm = sum(value * value for value in expected_source) ** 0.5
    expected_normalized = [
        value / norm
        for value in expected_source
    ]

    assert stored == pytest.approx(
        expected_normalized,
        rel=1e-6,
        abs=1e-6,
    )


def test_batch_upsert(pipeline):
    first = make_document()

    inventory = Inventory.create(
        tenant_id="tenant-001",
        project_id="project-002",
        inventory_code="UNIT-002",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Second Unit",
    )

    second = build_inventory_index(
        inventory,
        tenant_id="tenant-001",
        project_id="project-002",
    )

    ids = pipeline.upsert_many(
        [
            (first, [0.1, 0.2, 0.3, 0.4]),
            (second, [0.4, 0.3, 0.2, 0.1]),
        ],
        tenant_id="tenant-001",
    )

    assert len(ids) == 2
    assert len(set(ids)) == 2


def test_wrong_tenant_is_blocked(pipeline):
    with pytest.raises(QdrantTenantViolation):
        pipeline.build_point(
            make_document(),
            [0.1, 0.2, 0.3, 0.4],
            tenant_id="tenant-999",
        )


def test_wrong_vector_size_is_blocked(pipeline):
    with pytest.raises(QdrantVectorError):
        pipeline.build_point(
            make_document(),
            [0.1, 0.2, 0.3],
            tenant_id="tenant-001",
        )


def test_non_finite_vector_is_blocked(pipeline):
    with pytest.raises(QdrantVectorError):
        pipeline.build_point(
            make_document(),
            [0.1, float("nan"), 0.3, 0.4],
            tenant_id="tenant-001",
        )


def test_stale_version_is_blocked(pipeline):
    with pytest.raises(QdrantVersionViolation):
        pipeline.build_point(
            make_document(),
            [0.1, 0.2, 0.3, 0.4],
            tenant_id="tenant-001",
            expected_version=2,
        )


def test_delete_removes_existing_point(pipeline):
    upsert_document = make_document()

    point_id = pipeline.upsert(
        upsert_document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-001",
    )

    delete_document = make_document(operation="DELETE")

    deleted_id = pipeline.delete(
        delete_document,
        tenant_id="tenant-001",
    )

    assert deleted_id == point_id

    points = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[point_id],
    )

    assert points == []


def test_batch_empty_input_is_safe(pipeline):
    assert pipeline.upsert_many(
        [],
        tenant_id="tenant-001",
    ) == ()
