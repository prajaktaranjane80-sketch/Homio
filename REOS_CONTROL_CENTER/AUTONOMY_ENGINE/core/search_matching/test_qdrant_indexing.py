from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantConfigurationError,
    QdrantDocumentOperationError,
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
    QdrantTenantViolation,
    QdrantVectorError,
    QdrantVersionViolation,
    deterministic_point_id,
)
from AUTONOMY_ENGINE.core.search_matching.search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


def make_document(
    *,
    tenant_id: str = "tenant-a",
    inventory_id: str = "inventory-a",
    inventory_code: str = "UNIT-101",
    version: int = 1,
    operation: SearchIndexOperation = SearchIndexOperation.UPSERT,
    index_key: str | None = None,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id="project-a",
        inventory_id=inventory_id,
        inventory_code=inventory_code,
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
        name="Skyline Residency",
        inventory_version=version,
        index_key=index_key
        or f"{tenant_id}:{inventory_id}",
        operation=operation,
    )


@pytest.fixture
def pipeline() -> QdrantIndexingPipeline:
    return QdrantIndexingPipeline(
        client=QdrantClient(":memory:"),
        config=QdrantIndexingConfig(
            collection_name="test_inventory_vectors",
            vector_size=4,
        ),
    )


def test_deterministic_point_id_is_stable() -> None:
    first = deterministic_point_id(
        "tenant-a:inventory-a"
    )
    second = deterministic_point_id(
        "tenant-a:inventory-a"
    )

    assert first == second


def test_different_index_keys_produce_different_ids() -> None:
    first = deterministic_point_id(
        "tenant-a:inventory-a"
    )
    second = deterministic_point_id(
        "tenant-a:inventory-b"
    )

    assert first != second


def test_collection_is_created(
    pipeline: QdrantIndexingPipeline,
) -> None:
    pipeline.ensure_collection()

    collections = (
        pipeline.client
        .get_collections()
        .collections
    )

    assert any(
        item.name == "test_inventory_vectors"
        for item in collections
    )


def test_build_point_contains_canonical_payload(
    pipeline: QdrantIndexingPipeline,
) -> None:
    document = make_document()

    point = pipeline.build_point(
        document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-a",
    )

    assert str(point.id) == deterministic_point_id(
        document.index_key
    )

    assert point.payload["tenant_id"] == "tenant-a"
    assert (
        point.payload["inventory_id"]
        == document.inventory_id
    )
    assert (
        point.payload["inventory_code"]
        == document.inventory_code
    )
    assert (
        point.payload["inventory_version"]
        == document.inventory_version
    )
    assert (
        point.payload["operation"]
        == "UPSERT"
    )


def test_upsert_writes_one_point(
    pipeline: QdrantIndexingPipeline,
) -> None:
    document = make_document()

    point_id = pipeline.upsert(
        document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-a",
    )

    stored = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[point_id],
        with_payload=True,
    )

    assert len(stored) == 1
    assert (
        stored[0].payload["inventory_code"]
        == "UNIT-101"
    )


def test_upsert_is_idempotent_for_same_identity(
    pipeline: QdrantIndexingPipeline,
) -> None:
    document = make_document()

    first = pipeline.upsert(
        document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-a",
    )

    second = pipeline.upsert(
        document,
        [0.4, 0.3, 0.2, 0.1],
        tenant_id="tenant-a",
    )

    assert first == second

    stored = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[first],
        with_payload=True,
        with_vectors=True,
    )

    assert len(stored) == 1
    assert stored[0].payload[
        "inventory_version"
    ] == 1


def test_newer_version_replaces_older_version(
    pipeline: QdrantIndexingPipeline,
) -> None:
    first_document = make_document(
        version=1
    )
    second_document = make_document(
        version=2
    )

    point_id_1 = pipeline.upsert(
        first_document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-a",
    )

    point_id_2 = pipeline.upsert(
        second_document,
        [0.4, 0.3, 0.2, 0.1],
        tenant_id="tenant-a",
    )

    assert point_id_1 == point_id_2

    stored = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[point_id_2],
        with_payload=True,
    )

    assert (
        stored[0].payload["inventory_version"]
        == 2
    )


def test_stale_version_cannot_replace_newer_version(
    pipeline: QdrantIndexingPipeline,
) -> None:
    newer = make_document(version=2)
    stale = make_document(version=1)

    pipeline.upsert(
        newer,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-a",
    )

    with pytest.raises(QdrantVersionViolation):
        pipeline.upsert(
            stale,
            [0.4, 0.3, 0.2, 0.1],
            tenant_id="tenant-a",
        )


def test_wrong_tenant_is_blocked(
    pipeline: QdrantIndexingPipeline,
) -> None:
    with pytest.raises(QdrantTenantViolation):
        pipeline.build_point(
            make_document(),
            [0.1, 0.2, 0.3, 0.4],
            tenant_id="tenant-b",
        )


@pytest.mark.parametrize(
    "vector",
    [
        [0.1, 0.2, 0.3],
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.1, float("nan"), 0.3, 0.4],
        [0.1, float("inf"), 0.3, 0.4],
    ],
)
def test_invalid_vector_is_blocked(
    pipeline: QdrantIndexingPipeline,
    vector,
) -> None:
    with pytest.raises(QdrantVectorError):
        pipeline.build_point(
            make_document(),
            vector,
            tenant_id="tenant-a",
        )


def test_expected_version_mismatch_is_blocked(
    pipeline: QdrantIndexingPipeline,
) -> None:
    with pytest.raises(QdrantVersionViolation):
        pipeline.build_point(
            make_document(version=1),
            [0.1, 0.2, 0.3, 0.4],
            tenant_id="tenant-a",
            expected_version=2,
        )


def test_delete_requires_delete_operation(
    pipeline: QdrantIndexingPipeline,
) -> None:
    with pytest.raises(QdrantDocumentOperationError):
        pipeline.delete(
            make_document(
                operation=SearchIndexOperation.UPSERT
            ),
            tenant_id="tenant-a",
        )


def test_delete_removes_existing_point(
    pipeline: QdrantIndexingPipeline,
) -> None:
    upsert_document = make_document(
        version=1
    )

    point_id = pipeline.upsert(
        upsert_document,
        [0.1, 0.2, 0.3, 0.4],
        tenant_id="tenant-a",
    )

    delete_document = make_document(
        version=1,
        operation=SearchIndexOperation.DELETE,
    )

    deleted = pipeline.delete(
        delete_document,
        tenant_id="tenant-a",
        expected_version=1,
    )

    assert deleted == point_id

    stored = pipeline.client.retrieve(
        collection_name="test_inventory_vectors",
        ids=[point_id],
    )

    assert stored == []


def test_batch_upsert_is_supported(
    pipeline: QdrantIndexingPipeline,
) -> None:
    first = make_document(
        inventory_id="inventory-a",
        inventory_code="UNIT-A",
    )

    second = make_document(
        inventory_id="inventory-b",
        inventory_code="UNIT-B",
    )

    ids = pipeline.upsert_many(
        [
            (
                first,
                [0.1, 0.2, 0.3, 0.4],
            ),
            (
                second,
                [0.4, 0.3, 0.2, 0.1],
            ),
        ],
        tenant_id="tenant-a",
    )

    assert len(ids) == 2
    assert len(set(ids)) == 2


def test_empty_batch_is_safe(
    pipeline: QdrantIndexingPipeline,
) -> None:
    assert (
        pipeline.upsert_many(
            [],
            tenant_id="tenant-a",
        )
        == ()
    )


@pytest.mark.parametrize(
    "collection_name,vector_size",
    [
        ("", 4),
        ("inventory_vectors", 0),
        ("inventory_vectors", -1),
    ],
)
def test_invalid_configuration_is_rejected(
    collection_name: str,
    vector_size: int,
) -> None:
    with pytest.raises(QdrantConfigurationError):
        QdrantIndexingConfig(
            collection_name=collection_name,
            vector_size=vector_size,
        )
