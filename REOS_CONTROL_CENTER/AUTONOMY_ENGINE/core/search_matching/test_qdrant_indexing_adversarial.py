from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantDocumentOperationError,
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
    QdrantTenantViolation,
    QdrantVersionViolation,
)
from AUTONOMY_ENGINE.core.search_matching.search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


def make_document(
    *,
    tenant_id: str = "tenant-a",
    inventory_id: str = "inventory-a",
    version: int = 1,
    operation: SearchIndexOperation = SearchIndexOperation.UPSERT,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id="project-a",
        inventory_id=inventory_id,
        inventory_code=f"UNIT-{inventory_id}",
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
        name="Adversarial Test Unit",
        inventory_version=version,
        index_key=f"{tenant_id}:{inventory_id}",
        operation=operation,
    )


@pytest.fixture
def pipeline() -> QdrantIndexingPipeline:
    return QdrantIndexingPipeline(
        client=QdrantClient(":memory:"),
        config=QdrantIndexingConfig(
            collection_name="adversarial_vectors",
            vector_size=3,
        ),
    )


def test_cross_tenant_write_cannot_build_point(
    pipeline: QdrantIndexingPipeline,
) -> None:
    with pytest.raises(QdrantTenantViolation):
        pipeline.build_point(
            make_document(
                tenant_id="tenant-a"
            ),
            [1.0, 0.0, 0.0],
            tenant_id="tenant-b",
        )


def test_cross_tenant_write_cannot_reach_qdrant(
    pipeline: QdrantIndexingPipeline,
) -> None:
    with pytest.raises(QdrantTenantViolation):
        pipeline.upsert(
            make_document(
                tenant_id="tenant-a"
            ),
            [1.0, 0.0, 0.0],
            tenant_id="tenant-b",
        )

    collections = (
        pipeline.client
        .get_collections()
        .collections
    )

    assert any(
        collection.name == "adversarial_vectors"
        for collection in collections
    )

    points = pipeline.client.scroll(
        collection_name="adversarial_vectors",
        limit=100,
    )[0]

    assert points == []


def test_older_version_cannot_delete_newer_version(
    pipeline: QdrantIndexingPipeline,
) -> None:
    newer = make_document(
        version=2
    )

    pipeline.upsert(
        newer,
        [1.0, 0.0, 0.0],
        tenant_id="tenant-a",
    )

    stale_delete = make_document(
        version=1,
        operation=SearchIndexOperation.DELETE,
    )

    with pytest.raises(QdrantVersionViolation):
        pipeline.delete(
            stale_delete,
            tenant_id="tenant-a",
        )


def test_delete_of_missing_point_is_idempotent(
    pipeline: QdrantIndexingPipeline,
) -> None:
    delete_document = make_document(
        operation=SearchIndexOperation.DELETE
    )

    point_id = pipeline.delete(
        delete_document,
        tenant_id="tenant-a",
    )

    assert isinstance(point_id, str)

    points = pipeline.client.retrieve(
        collection_name="adversarial_vectors",
        ids=[point_id],
    )

    assert points == []


def test_upsert_rejects_delete_document(
    pipeline: QdrantIndexingPipeline,
) -> None:
    delete_document = make_document(
        operation=SearchIndexOperation.DELETE
    )

    with pytest.raises(QdrantDocumentOperationError):
        pipeline.upsert(
            delete_document,
            [1.0, 0.0, 0.0],
            tenant_id="tenant-a",
        )


def test_zero_vector_is_allowed_as_valid_finite_input(
    pipeline: QdrantIndexingPipeline,
) -> None:
    document = make_document()

    point_id = pipeline.upsert(
        document,
        [0.0, 0.0, 0.0],
        tenant_id="tenant-a",
    )

    assert isinstance(point_id, str)


def test_source_document_is_not_mutated(
    pipeline: QdrantIndexingPipeline,
) -> None:
    document = make_document()

    before = document.to_dict()

    pipeline.upsert(
        document,
        [1.0, 0.0, 0.0],
        tenant_id="tenant-a",
    )

    after = document.to_dict()

    assert after == before
