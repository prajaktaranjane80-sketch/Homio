from __future__ import annotations

from time import perf_counter
from types import SimpleNamespace

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridRetrievalPipeline,
    HybridSearchResult,
)
from AUTONOMY_ENGINE.core.search_matching.matching import (
    MatchingProfile,
    MatchingRecommendationPipeline,
)
from AUTONOMY_ENGINE.core.search_matching.search_ranking import (
    SearchRankingPipeline,
)
from AUTONOMY_ENGINE.core.search_matching.search_visibility import (
    SearchVisibilityPolicy,
    TenantVisibilityFilter,
)


def make_hybrid_result(
    *,
    index_key: str,
    tenant_id: str = "tenant-a",
    inventory_code: str = "UNIT-001",
    inventory_type: str = "UNIT",
    project_id: str = "project-a",
    name: str = "Premium Residential Unit",
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
        inventory_id=(
            f"inventory-{index_key}"
        ),
        inventory_code=inventory_code,
        inventory_type=inventory_type,
        name=name,
        lifecycle=lifecycle,
        availability=availability,
        payload={},
    )

    return HybridSearchResult(
        document=document,
        rrf_score=rrf_score,
        lexical_rank=lexical_rank,
        vector_rank=vector_rank,
        lexical_score=1.0,
        vector_score=1.0,
    )


def test_tenant_visibility_blocks_foreign_candidate() -> None:
    candidate = make_hybrid_result(
        index_key="foreign",
        tenant_id="tenant-b",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        candidate
    )

    assert not decision.allowed
    assert not decision.tenant_allowed


def test_visibility_blocks_inactive_inventory() -> None:
    candidate = make_hybrid_result(
        index_key="inactive",
        lifecycle="SUSPENDED",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    assert not boundary.is_visible(
        candidate
    )


def test_visibility_blocks_unavailable_inventory() -> None:
    candidate = make_hybrid_result(
        index_key="unavailable",
        availability="UNAVAILABLE",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    assert not boundary.is_visible(
        candidate
    )


def test_visibility_keeps_reserved_inventory_visible() -> None:
    candidate = make_hybrid_result(
        index_key="reserved",
        availability="RESERVED",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    assert boundary.is_visible(
        candidate
    )


def test_ranking_is_deterministic_for_large_candidate_set() -> None:
    candidates = tuple(
        make_hybrid_result(
            index_key=f"idx-{index:05d}",
            tenant_id="tenant-a",
            inventory_code=(
                f"UNIT-{index:05d}"
            ),
            rank if False else None
        )
        for index in range(1)
    )
