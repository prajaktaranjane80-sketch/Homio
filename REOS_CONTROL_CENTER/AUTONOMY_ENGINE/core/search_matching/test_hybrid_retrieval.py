
from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridQueryError,
    HybridRetrievalPipeline,
    HybridTenantError,
)
from AUTONOMY_ENGINE.core.inventory.inventory import (
    Inventory,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory.inventory_indexing import (
    build_inventory_index,
)
from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
)


def make_document(
    *,
    tenant_id: str,
    project_id: str,
    inventory_code: str,
    name: str,
):
    inventory = Inventory.create(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_code=inventory_code,
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name=name,
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
            inventory_code="UNIT-001",
            name="Premium Two Bedroom",
        ),
        make_document(
            tenant_id="tenant-001",
            project_id="project-002",
            inventory_code="UNIT-002",
            name="Compact Office",
        ),
        make_document(
            tenant_id="tenant-001",
            project_id="project-003",
            inventory_code="UNIT-003",
            name="Premium Three Bedroom",
        ),
        make_document(
            tenant_id="tenant-002",
            project_id="project-004",
            inventory_code="UNIT-004",
            name="Premium Two Bedroom",
        ),
    )


@pytest.fixture
def pipeline(documents):
    client = QdrantClient(":memory:")

    qdrant = QdrantIndexingPipeline(
        client=client,
        config=QdrantIndexingConfig(
            collection_name="hybrid_test",
            vector_size=4,
        ),
    )

    for index, document in enumerate(documents):
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


def test_lexical_matches_are_returned(pipeline):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert {
        "UNIT-001",
        "UNIT-003",
    }.issubset({
        item.inventory_code
        for item in result
    })


def test_vector_candidates_are_included(pipeline):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="UnknownTerm",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert len(result) >= 1


def test_cross_tenant_results_are_blocked(pipeline):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert all(
        item.tenant_id == "tenant-001"
        for item in result
    )

    assert "UNIT-004" not in {
        item.inventory_code
        for item in result
    }


def test_lexical_and_vector_overlap_has_both_ranks(
    pipeline,
):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    item = next(
        item
        for item in result
        if item.inventory_code == "UNIT-001"
    )

    assert item.lexical_rank is not None
    assert item.vector_rank is not None
    assert item.rrf_score > 0


def test_result_order_is_deterministic(pipeline):
    first = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    second = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert [
        item.index_key for item in first
    ] == [
        item.index_key for item in second
    ]


def test_limit_is_honored(pipeline):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=1,
    )

    assert len(result) == 1


def test_empty_query_is_rejected(pipeline):
    with pytest.raises(HybridQueryError):
        pipeline.search(
            tenant_id="tenant-001",
            query_text="",
            vector=[1.0, 0.0, 0.0, 0.0],
            limit=10,
        )


def test_empty_tenant_is_rejected(pipeline):
    with pytest.raises(HybridTenantError):
        pipeline.search(
            tenant_id="",
            query_text="Premium",
            vector=[1.0, 0.0, 0.0, 0.0],
            limit=10,
        )


def test_lexical_only_candidate_is_allowed(pipeline):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="Compact Office",
        vector=[0.0, 0.0, 0.0, 1.0],
        limit=10,
    )

    assert any(
        item.inventory_code == "UNIT-002"
        for item in result
    )


def test_vector_only_candidate_is_allowed(pipeline):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="UnknownTerm",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert len(result) >= 1


def test_search_does_not_mutate_documents(
    pipeline,
    documents,
):
    before = tuple(
        item.to_dict()
        for item in documents
    )

    pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    after = tuple(
        item.to_dict()
        for item in documents
    )

    assert before == after


def test_rrf_score_uses_both_rank_contributions(
    pipeline,
):
    result = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    item = next(
        item
        for item in result
        if item.inventory_code == "UNIT-001"
    )

    expected = (
        1.0 / (60 + item.lexical_rank)
        + 1.0 / (60 + item.vector_rank)
    )

    assert item.rrf_score == pytest.approx(
        expected
    )
