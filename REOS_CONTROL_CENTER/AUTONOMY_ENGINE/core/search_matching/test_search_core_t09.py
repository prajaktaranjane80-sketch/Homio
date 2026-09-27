from __future__ import annotations

from time import perf_counter
from types import SimpleNamespace

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
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
            rrf_score=1.0 / (
                (index % 100) + 1
            ),
            lexical_rank=(
                (index % 100) + 1
            ),
            vector_rank=(
                (index % 100) + 1
            ),
        )
        for index in range(2000)
    )

    pipeline = SearchRankingPipeline()

    started = perf_counter()

    first = pipeline.rank(
        candidates,
        limit=100,
    )

    elapsed = (
        perf_counter() - started
    )

    second = pipeline.rank(
        candidates,
        limit=100,
    )

    assert len(first) == 100

    assert [
        (
            item.index_key,
            item.ranking_score,
            item.rank,
        )
        for item in first
    ] == [
        (
            item.index_key,
            item.ranking_score,
            item.rank,
        )
        for item in second
    ]

    assert elapsed < 2.0


def test_matching_is_deterministic_for_large_candidate_set() -> None:
    candidates = tuple(
        make_hybrid_result(
            index_key=f"idx-{index:05d}",
            tenant_id="tenant-a",
            inventory_code=(
                f"UNIT-{index:05d}"
            ),
            name=(
                "Premium Residential "
                "Bedroom Unit"
            ),
            rrf_score=1.0 / (
                (index % 100) + 1
            ),
            lexical_rank=(
                (index % 100) + 1
            ),
            vector_rank=(
                (index % 100) + 1
            ),
        )
        for index in range(2000)
    )

    ranked = SearchRankingPipeline().rank(
        candidates,
        limit=500,
    )

    pipeline = MatchingRecommendationPipeline()

    profile = MatchingProfile(
        tenant_id="tenant-a",
        preferred_keywords=frozenset(
            {
                "premium",
                "residential",
                "bedroom",
                "unit",
            }
        ),
        limit=100,
    )

    started = perf_counter()

    first = pipeline.match(
        ranked,
        profile=profile,
    )

    elapsed = (
        perf_counter() - started
    )

    second = pipeline.match(
        ranked,
        profile=profile,
    )

    assert len(first) == 100

    assert [
        (
            item.index_key,
            item.match_score,
            item.rank,
        )
        for item in first
    ] == [
        (
            item.index_key,
            item.match_score,
            item.rank,
        )
        for item in second
    ]

    assert elapsed < 2.0


def test_visibility_scales_without_reordering() -> None:
    results = tuple(
        make_hybrid_result(
            index_key=f"idx-{index:05d}",
            tenant_id=(
                "tenant-a"
                if index % 2 == 0
                else "tenant-b"
            ),
        )
        for index in range(5000)
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    started = perf_counter()

    filtered = boundary.apply(
        results
    )

    elapsed = (
        perf_counter() - started
    )

    assert len(filtered) == 2500

    assert [
        item.document.index_key
        for item in filtered[:5]
    ] == [
        "idx-00000",
        "idx-00002",
        "idx-00004",
        "idx-00006",
        "idx-00008",
    ]

    assert elapsed < 1.0


def test_visibility_never_changes_candidate_order() -> None:
    results = (
        make_hybrid_result(
            index_key="z",
        ),
        make_hybrid_result(
            index_key="a",
        ),
        make_hybrid_result(
            index_key="m",
        ),
    )

    filtered = TenantVisibilityFilter(
        tenant_id="tenant-a"
    ).apply(results)

    assert [
        item.document.index_key
        for item in filtered
    ] == [
        "z",
        "a",
        "m",
    ]


def test_custom_visibility_policy_still_enforces_tenant_first() -> None:
    policy = SearchVisibilityPolicy(
        visible_lifecycles=frozenset(
            {"ACTIVE"}
        ),
        blocked_availability=frozenset(
            {"UNAVAILABLE"}
        ),
    )

    candidate = make_hybrid_result(
        index_key="foreign",
        tenant_id="tenant-b",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a",
        policy=policy,
    )

    decision = boundary.decide(
        candidate
    )

    assert not decision.allowed
    assert not decision.tenant_allowed


def test_matching_result_contains_explanation() -> None:
    candidate = make_hybrid_result(
        index_key="premium",
        inventory_code="UNIT-777",
        name="Premium Two Bedroom",
    )

    ranked = SearchRankingPipeline().rank(
        (candidate,)
    )

    results = MatchingRecommendationPipeline().match(
        ranked,
        profile=MatchingProfile(
            tenant_id="tenant-a",
            preferred_inventory_codes=frozenset(
                {"UNIT-777"}
            ),
            preferred_keywords=frozenset(
                {
                    "premium",
                    "bedroom",
                }
            ),
        ),
    )

    assert len(results) == 1
    assert results[0].explanation.matched_signals


def test_matching_never_mutates_ranked_input() -> None:
    candidates = (
        make_hybrid_result(
            index_key="a"
        ),
        make_hybrid_result(
            index_key="b",
            inventory_code="UNIT-002",
        ),
    )

    ranked = SearchRankingPipeline().rank(
        candidates
    )

    before = tuple(ranked)

    MatchingRecommendationPipeline().match(
        ranked,
        profile=MatchingProfile(
            tenant_id="tenant-a"
        ),
    )

    assert tuple(ranked) == before


def test_visibility_policy_is_immutable() -> None:
    policy = SearchVisibilityPolicy()

    try:
        policy.visible_lifecycles = frozenset(
            {"ACTIVE", "ARCHIVED"}
        )
        assert False
    except AttributeError:
        pass
