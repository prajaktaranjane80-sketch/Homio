from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridQueryError,
    HybridRetrievalConfig,
    HybridRetrievalPipeline,
    HybridTenantError,
    HybridVectorError,
)
from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
)
from AUTONOMY_ENGINE.core.search_matching.search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


def make_document(
    *,
    tenant_id: str,
    inventory_id: str,
    inventory_code: str,
    name: str,
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
        name=name,
        inventory_version=1,
        index_key=index_key
        or f"{tenant_id}:{inventory_id}",
        operation=SearchIndexOperation.UPSERT,
    )


@pytest.fixture
def documents() -> tuple[
    InventoryIndexDocument,
    ...,
]:
    return (
        make_document(
            tenant_id="tenant-a",
            inventory_id="inventory-1",
            inventory_code="UNIT-001",
            name="Premium Two Bedroom",
        ),
        make_document(
            tenant_id="tenant-a",
            inventory_id="inventory-2",
            inventory_code="UNIT-002",
            name="Compact Office",
        ),
        make_document(
            tenant_id="tenant-a",
            inventory_id="inventory-3",
            inventory_code="UNIT-003",
            name="Premium Three Bedroom",
        ),
        make_document(
            tenant_id="tenant-b",
            inventory_id="inventory-4",
            inventory_code="UNIT-004",
            name="Premium Two Bedroom",
        ),
    )


@pytest.fixture
def pipeline(
    documents,
) -> HybridRetrievalPipeline:
    client = QdrantClient(":memory:")

    qdrant = QdrantIndexingPipeline(
        client=client,
        config=QdrantIndexingConfig(
            collection_name="hybrid_test",
            vector_size=4,
        ),
    )

    for index, document in enumerate(
        documents
    ):
        qdrant.upsert(
            document,
            [
                float(index + 1),
                0.0,
                0.0,
                0.0,
            ],
            tenant_id=document.tenant_id,
        )

    return HybridRetrievalPipeline(
        client=client,
        collection_name="hybrid_test",
        lexical_documents=documents,
    )


def test_lexical_candidates_are_returned(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    codes = {
        item.inventory_code
        for item in results
    }

    assert "UNIT-001" in codes
    assert "UNIT-003" in codes


def test_vector_candidates_can_be_returned(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-a",
        query_text="CompletelyUnknownTerm",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert len(results) >= 1


def test_tenant_boundary_is_enforced(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert all(
        result.tenant_id == "tenant-a"
        for result in results
    )

    assert "UNIT-004" not in {
        result.inventory_code
        for result in results
    }


def test_hybrid_candidate_contains_both_ranks(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    result = next(
        item
        for item in results
        if item.inventory_code
        == "UNIT-001"
    )

    assert result.lexical_rank is not None
    assert result.vector_rank is not None
    assert result.rrf_score > 0
    assert result.source == "HYBRID"


def test_result_order_is_deterministic(
    pipeline,
) -> None:
    first = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    second = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert [
        item.index_key
        for item in first
    ] == [
        item.index_key
        for item in second
    ]


def test_limit_is_honored(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=1,
    )

    assert len(results) == 1


def test_empty_query_is_rejected(
    pipeline,
) -> None:
    with pytest.raises(HybridQueryError):
        pipeline.search(
            tenant_id="tenant-a",
            query_text="   ",
            vector=[1.0, 0.0, 0.0, 0.0],
            limit=10,
        )


def test_empty_tenant_is_rejected(
    pipeline,
) -> None:
    with pytest.raises(HybridTenantError):
        pipeline.search(
            tenant_id="",
            query_text="Premium",
            vector=[1.0, 0.0, 0.0, 0.0],
            limit=10,
        )


def test_invalid_vector_is_rejected(
    pipeline,
) -> None:
    with pytest.raises(HybridVectorError):
        pipeline.search(
            tenant_id="tenant-a",
            query_text="Premium",
            vector=[],
            limit=10,
        )


def test_cross_tenant_documents_are_never_exposed(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-b",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert all(
        result.tenant_id == "tenant-b"
        for result in results
    )


def test_configuration_is_immutable() -> None:
    config = HybridRetrievalConfig(
        rrf_k=60,
        candidate_multiplier=3,
    )

    with pytest.raises(
        AttributeError
    ):
        config.rrf_k = 10  # type: ignore[misc]


def test_input_documents_are_not_mutated(
    pipeline,
    documents,
) -> None:
    before = tuple(
        document.to_dict()
        for document in documents
    )

    pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    after = tuple(
        document.to_dict()
        for document in documents
    )

    assert before == after


def test_rrf_score_uses_retrieval_ranks(
    pipeline,
) -> None:
    results = pipeline.search(
        tenant_id="tenant-a",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    result = next(
        item
        for item in results
        if item.inventory_code
        == "UNIT-001"
    )

    expected = (
        1.0
        / (
            60
            + result.lexical_rank
        )
        + 1.0
        / (
            60
            + result.vector_rank
        )
    )

    assert result.rrf_score == pytest.approx(
        expected
    )
