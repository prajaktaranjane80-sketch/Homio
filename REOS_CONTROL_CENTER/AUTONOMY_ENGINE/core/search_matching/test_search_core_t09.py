from __future__ import annotations

from time import perf_counter
from types import SimpleNamespace

import pytest
from qdrant_client import QdrantClient

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridRetrievalPipeline,
    HybridSearchResult,
)
from AUTONOMY_ENGINE.core.inventory.inventory import Inventory, InventoryType
from AUTONOMY_ENGINE.core.inventory.inventory_indexing import InventoryIndexingHook
from AUTONOMY_ENGINE.core.search_matching.matching import (
    MatchingProfile,
    MatchingRecommendationPipeline,
    MatchingTenantError,
)
from AUTONOMY_ENGINE.core.search_matching.qdrant_indexing import (
    QdrantIndexingConfig,
    QdrantIndexingPipeline,
)
from AUTONOMY_ENGINE.core.search_matching.search_ranking import (
    RankedSearchResult,
    SearchRankingPipeline,
)
from AUTONOMY_ENGINE.core.search_matching.search_visibility import (
    SearchVisibilityPolicy,
    TenantVisibilityFilter,
)


def make_inventory(
    *,
    tenant_id: str,
    project_id: str,
    inventory_code: str,
    name: str,
    lifecycle: str = "ACTIVE",
    availability: str = "AVAILABLE",
) -> Inventory:
    inventory = Inventory.create(
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_code=inventory_code,
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name=name,
        metadata={},
        at="2026-08-30T10:00:00+00:00",
    )

    # Inventory.create() starts at DRAFT. Move only when required.
    if lifecycle != "DRAFT":
        from AUTONOMY_ENGINE.core.inventory.inventory import (
            InventoryAvailability,
            InventoryLifecycle,
        )

        target = InventoryLifecycle(lifecycle)

        while inventory.lifecycle != target:
            if inventory.lifecycle is InventoryLifecycle.DRAFT:
                next_state = InventoryLifecycle.ONBOARDING
            elif inventory.lifecycle is InventoryLifecycle.ONBOARDING:
                next_state = InventoryLifecycle.ACTIVE
            else:
                break

            inventory, _ = inventory.transition(
                next_state,
                tenant_id=tenant_id,
                project_id=project_id,
            )

        if availability != "AVAILABLE":
            inventory, _ = inventory.set_availability(
                InventoryAvailability(availability),
                tenant_id=tenant_id,
                project_id=project_id,
            )

    return inventory


def make_hybrid_result(
    *,
    index_key: str,
    tenant_id: str,
    rank: int,
    name: str,
    inventory_code: str = "UNIT-001",
    inventory_type: str = "RESIDENTIAL_UNIT",
    project_id: str = "project-001",
    lifecycle: str = "ACTIVE",
    availability: str = "AVAILABLE",
    rrf_score: float = 0.5,
    lexical_rank: int | None = 1,
    vector_rank: int | None = 1,
) -> HybridSearchResult:
    document = SimpleNamespace(
        index_key=index_key,
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_id=f"inventory-{index_key}",
        inventory_code=inventory_code,
        inventory_type=inventory_type,
        name=name,
        lifecycle=lifecycle,
        availability=availability,
    )

    return HybridSearchResult(
        document=document,
        rrf_score=rrf_score,
        lexical_rank=lexical_rank,
        vector_rank=vector_rank,
    )


def to_ranked(result: HybridSearchResult, rank: int) -> RankedSearchResult:
    return RankedSearchResult(
        result=result,
        ranking_score=result.rrf_score,
        rerank_score=result.rrf_score,
        rank=rank,
    )


def test_hybrid_retrieval_does_not_expose_cross_tenant_results():
    client = QdrantClient(":memory:")
    config = QdrantIndexingConfig(
        collection_name="t09_hybrid_security",
        vector_size=4,
    )
    indexer = QdrantIndexingPipeline(
        client=client,
        config=config,
    )
    indexer.ensure_collection()

    hook = InventoryIndexingHook()

    tenant_1 = make_inventory(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        name="Tenant One Premium",
    )

    tenant_2 = make_inventory(
        tenant_id="tenant-002",
        project_id="project-001",
        inventory_code="UNIT-002",
        name="Tenant Two Premium",
    )

    doc_1 = hook.build_upsert(
        tenant_1,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    doc_2 = hook.build_upsert(
        tenant_2,
        tenant_id="tenant-002",
        project_id="project-001",
    )

    indexer.upsert(
        doc_1,
        [1.0, 0.0, 0.0, 0.0],
        tenant_id="tenant-001",
    )

    indexer.upsert(
        doc_2,
        [1.0, 0.0, 0.0, 0.0],
        tenant_id="tenant-002",
    )

    pipeline = HybridRetrievalPipeline(
        client=client,
        collection_name=config.collection_name,
        lexical_documents=(doc_1, doc_2),
    )

    results = pipeline.search(
        tenant_id="tenant-001",
        query_text="Premium",
        vector=[1.0, 0.0, 0.0, 0.0],
        limit=10,
    )

    assert all(
        item.document.tenant_id == "tenant-001"
        for item in results
    )


def test_visibility_boundary_blocks_cross_tenant_result():
    result = make_hybrid_result(
        index_key="cross-tenant",
        tenant_id="tenant-999",
        rank=1,
        name="Premium",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-001",
    )

    decision = boundary.decide(result)

    assert not decision.allowed
    assert not decision.tenant_allowed


def test_visibility_boundary_blocks_non_visible_lifecycle():
    result = make_hybrid_result(
        index_key="suspended",
        tenant_id="tenant-001",
        rank=1,
        name="Premium",
        lifecycle="SUSPENDED",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-001",
    )

    assert not boundary.is_visible(result)


def test_matching_fails_closed_for_cross_tenant_candidate():
    candidate = to_ranked(
        make_hybrid_result(
            index_key="cross-tenant",
            tenant_id="tenant-999",
            rank=1,
            name="Premium",
        ),
        rank=1,
    )

    pipeline = MatchingRecommendationPipeline()

    with pytest.raises(MatchingTenantError):
        pipeline.match(
            (candidate,),
            profile=MatchingProfile(
                tenant_id="tenant-001",
            ),
        )


def test_ranking_is_deterministic():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=f"idx-{index:03d}",
                tenant_id="tenant-001",
                rank=index,
                name="Premium",
                rrf_score=1.0 / index,
            ),
            rank=index,
        )
        for index in range(1, 101)
    )

    pipeline = SearchRankingPipeline()

    first = pipeline.rank(tuple(item.result for item in candidates))
    second = pipeline.rank(tuple(item.result for item in candidates))

    assert [
        (
            item.document.index_key,
            item.ranking_score,
            item.rank,
        )
        for item in first
    ] == [
        (
            item.document.index_key,
            item.ranking_score,
            item.rank,
        )
        for item in second
    ]


def test_reranking_preserves_relevance_signal():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=index_key,
                tenant_id="tenant-001",
                rank=rank,
                name=name,
                inventory_code=code,
            ),
            rank=rank,
        )
        for index_key, rank, name, code in (
            (
                "idx-standard",
                1,
                "Standard Apartment",
                "UNIT-001",
            ),
            (
                "idx-premium",
                2,
                "Premium Two Bedroom",
                "UNIT-002",
            ),
        )
    )

    pipeline = SearchRankingPipeline()
    ranked = pipeline.rank(tuple(item.result for item in candidates))

    reranked = pipeline.rerank(
        ranked,
        query_text="Premium Two",
        window=2,
    )

    assert reranked[0].document.name == "Premium Two Bedroom"


def test_recommendation_result_is_deterministic():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=f"idx-{index}",
                tenant_id="tenant-001",
                rank=index,
                name="Premium Two Bedroom",
            ),
            rank=index,
        )
        for index in range(1, 51)
    )

    pipeline = MatchingRecommendationPipeline()

    profile = MatchingProfile(
        tenant_id="tenant-001",
        preferred_keywords=frozenset({"premium", "bedroom"}),
    )

    first = pipeline.match(candidates, profile=profile)
    second = pipeline.match(candidates, profile=profile)

    assert [
        (
            item.document.index_key,
            item.match_score,
            item.rank,
        )
        for item in first
    ] == [
        (
            item.document.index_key,
            item.match_score,
            item.rank,
        )
        for item in second
    ]


def test_relevance_prefers_exact_preferred_inventory_code():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=index_key,
                tenant_id="tenant-001",
                rank=1,
                name="Apartment",
                inventory_code=code,
            ),
            rank=1,
        )
        for index_key, code in (
            ("idx-target", "UNIT-777"),
            ("idx-other", "UNIT-111"),
        )
    )

    pipeline = MatchingRecommendationPipeline()

    results = pipeline.match(
        candidates,
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_inventory_codes=frozenset({"UNIT-777"}),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert results[0].document.inventory_code == "UNIT-777"


def test_performance_ranking_2000_candidates():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=f"idx-{index:05d}",
                tenant_id="tenant-001",
                rank=(index % 100) + 1,
                name="Premium Residential Unit",
                inventory_code=f"UNIT-{index:05d}",
                rrf_score=1.0 / ((index % 100) + 1),
            ),
            rank=(index % 100) + 1,
        )
        for index in range(2000)
    )

    pipeline = SearchRankingPipeline()

    started = perf_counter()
    result = pipeline.rank(tuple(item.result for item in candidates), limit=100)
    elapsed = perf_counter() - started

    assert len(result) == 100
    assert elapsed < 2.0


def test_performance_matching_2000_candidates():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=f"idx-{index:05d}",
                tenant_id="tenant-001",
                rank=(index % 100) + 1,
                name="Premium Residential Unit",
                inventory_code=f"UNIT-{index:05d}",
                rrf_score=1.0 / ((index % 100) + 1),
            ),
            rank=(index % 100) + 1,
        )
        for index in range(2000)
    )

    pipeline = MatchingRecommendationPipeline()

    started = perf_counter()

    result = pipeline.match(
        candidates,
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_keywords=frozenset(
                {"premium", "residential", "unit"}
            ),
            limit=100,
        ),
    )

    elapsed = perf_counter() - started

    assert len(result) == 100
    assert elapsed < 2.0


def test_visibility_filter_scales_to_5000_results():
    results = tuple(
        make_hybrid_result(
            index_key=f"idx-{index:05d}",
            tenant_id=(
                "tenant-001"
                if index % 2 == 0
                else "tenant-999"
            ),
            rank=1,
            name="Property",
        )
        for index in range(5000)
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-001",
    )

    started = perf_counter()
    filtered = boundary.apply(results)
    elapsed = perf_counter() - started

    assert len(filtered) == 2500
    assert elapsed < 1.0


def test_tenant_filter_is_fail_closed_for_custom_policy():
    policy = SearchVisibilityPolicy(
        visible_lifecycles=frozenset({"ACTIVE"}),
        blocked_availability=frozenset({"UNAVAILABLE"}),
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-001",
        policy=policy,
    )

    result = make_hybrid_result(
        index_key="foreign",
        tenant_id="tenant-002",
        rank=1,
        name="Property",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
    )

    assert not boundary.decide(result).allowed


def test_ranking_does_not_mutate_candidates():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=f"idx-{index}",
                tenant_id="tenant-001",
                rank=index,
                name="Property",
            ),
            rank=index,
        )
        for index in range(1, 20)
    )

    original = candidates

    SearchRankingPipeline().rank(tuple(item.result for item in candidates))

    assert candidates == original


def test_matching_does_not_mutate_candidates():
    candidates = tuple(
        to_ranked(
            make_hybrid_result(
                index_key=f"idx-{index}",
                tenant_id="tenant-001",
                rank=index,
                name="Property",
            ),
            rank=index,
        )
        for index in range(1, 20)
    )

    original = candidates

    MatchingRecommendationPipeline().match(
        candidates,
        profile=MatchingProfile(
            tenant_id="tenant-001",
        ),
    )

    assert candidates == original


def test_visibility_does_not_mutate_candidates():
    results = tuple(
        make_hybrid_result(
            index_key=f"idx-{index}",
            tenant_id="tenant-001",
            rank=index,
            name="Property",
        )
        for index in range(1, 20)
    )

    original = results

    TenantVisibilityFilter(
        tenant_id="tenant-001",
    ).apply(results)

    assert results == original


def test_indexing_projection_preserves_source_truth():
    inventory = make_inventory(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        name="Premium Two Bedroom",
    )

    before = inventory.to_dict()

    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert inventory.to_dict() == before
    assert document.tenant_id == inventory.tenant_id
    assert document.inventory_id == inventory.inventory_id
    assert document.inventory_version == inventory.version
