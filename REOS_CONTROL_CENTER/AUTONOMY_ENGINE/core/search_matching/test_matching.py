from __future__ import annotations

from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridSearchResult,
)
from AUTONOMY_ENGINE.core.search_matching.matching import (
    MatchRecommendation,
    MatchingCandidateError,
    MatchingConfigurationError,
    MatchingLimitError,
    MatchingProfile,
    MatchingRecommendationPipeline,
    MatchingTenantError,
)
from AUTONOMY_ENGINE.core.search_matching.search_ranking import (
    RankedSearchResult,
)


def make_candidate(
    *,
    index_key: str,
    tenant_id: str = "tenant-a",
    project_id: str = "project-a",
    inventory_code: str = "UNIT-001",
    inventory_type: str = "UNIT",
    name: str = "Premium Two Bedroom",
    availability: str = "AVAILABLE",
    rank: int = 1,
) -> RankedSearchResult:
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
        availability=availability,
    )

    retrieval = HybridSearchResult(
        document=document,
        rrf_score=0.5,
        lexical_rank=1,
        vector_rank=1,
        lexical_score=1.0,
        vector_score=1.0,
    )

    return RankedSearchResult(
        retrieval=retrieval,
        ranking_score=0.8,
        rank=rank,
    )


@pytest.fixture
def pipeline():
    return MatchingRecommendationPipeline()


def test_basic_matching_returns_recommendation(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="idx-001"
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a"
        ),
    )

    assert len(results) == 1
    assert isinstance(
        results[0],
        MatchRecommendation,
    )
    assert (
        results[0].inventory_code
        == "UNIT-001"
    )
    assert results[0].rank == 1


def test_matching_is_tenant_safe(
    pipeline,
) -> None:
    with pytest.raises(
        MatchingTenantError
    ):
        pipeline.match(
            (
                make_candidate(
                    index_key="foreign",
                    tenant_id="tenant-b",
                ),
            ),
            profile=MatchingProfile(
                tenant_id="tenant-a"
            ),
        )


def test_required_inventory_type_is_enforced(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="residential",
                inventory_type="UNIT",
            ),
            make_candidate(
                index_key="property",
                inventory_type="PROPERTY",
                inventory_code="PROPERTY-001",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            required_inventory_types=frozenset(
                {"UNIT"}
            ),
        ),
    )

    assert [
        item.inventory_code
        for item in results
    ] == ["UNIT-001"]


def test_required_project_is_enforced(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="project-a",
                project_id="project-a",
            ),
            make_candidate(
                index_key="project-b",
                project_id="project-b",
                inventory_code="UNIT-002",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            required_project_ids=frozenset(
                {"project-a"}
            ),
        ),
    )

    assert len(results) == 1
    assert (
        results[0].project_id
        == "project-a"
    )


def test_required_availability_is_enforced(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="available",
                availability="AVAILABLE",
            ),
            make_candidate(
                index_key="sold",
                inventory_code="UNIT-002",
                availability="SOLD",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            required_availability=frozenset(
                {"AVAILABLE"}
            ),
        ),
    )

    assert len(results) == 1
    assert (
        results[0].document.availability
        == "AVAILABLE"
    )


def test_excluded_keyword_is_hard_block(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="good",
                name="Premium Two Bedroom",
            ),
            make_candidate(
                index_key="blocked",
                inventory_code="UNIT-002",
                name="Premium Studio",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            excluded_keywords=frozenset(
                {"studio"}
            ),
        ),
    )

    assert len(results) == 1
    assert (
        results[0].document.index_key
        == "good"
    )


def test_preferred_inventory_type_improves_score(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="unit",
                inventory_type="UNIT",
                rank=1,
            ),
            make_candidate(
                index_key="property",
                inventory_type="PROPERTY",
                inventory_code="PROPERTY-001",
                rank=1,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            preferred_inventory_types=frozenset(
                {"UNIT"}
            ),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert (
        results[0].document.inventory_type
        == "UNIT"
    )

    assert (
        "preferred_inventory_type"
        in results[0]
        .explanation
        .matched_signals
    )


def test_preferred_project_improves_score(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="target",
                project_id="project-b",
                rank=1,
            ),
            make_candidate(
                index_key="other",
                project_id="project-a",
                inventory_code="UNIT-002",
                rank=1,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            preferred_project_ids=frozenset(
                {"project-b"}
            ),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert (
        results[0].project_id
        == "project-b"
    )


def test_preferred_availability_is_explainable(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="reserved",
                availability="RESERVED",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            preferred_availability=frozenset(
                {"RESERVED"}
            ),
        ),
    )

    assert (
        "preferred_availability"
        in results[0]
        .explanation
        .matched_signals
    )


def test_preferred_inventory_code_is_supported(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="target",
                inventory_code="UNIT-777",
            ),
            make_candidate(
                index_key="other",
                inventory_code="UNIT-001",
                rank=1,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            preferred_inventory_codes=frozenset(
                {"unit-777"}
            ),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert (
        results[0].inventory_code
        == "UNIT-777"
    )


def test_keyword_preference_is_supported(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="premium",
                name="Premium Two Bedroom",
            ),
            make_candidate(
                index_key="standard",
                inventory_code="UNIT-002",
                name="Standard Apartment",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a",
            preferred_keywords=frozenset(
                {"premium", "bedroom"}
            ),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert (
        results[0].document.index_key
        == "premium"
    )


def test_search_rank_is_a_stable_signal(
    pipeline,
) -> None:
    results = pipeline.match(
        (
            make_candidate(
                index_key="first",
                rank=1,
            ),
            make_candidate(
                index_key="second",
                inventory_code="UNIT-002",
                rank=2,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-a"
        ),
    )

    assert (
        results[0]
        .search_relevance
        >
        results[1]
        .search_relevance
    )


def test_limit_is_enforced(
    pipeline,
) -> None:
    candidates = tuple(
        make_candidate(
            index_key=f"idx-{index}",
            inventory_code=(
                f"UNIT-{index}"
            ),
            rank=index,
        )
        for index in range(1, 6)
    )

    results = pipeline.match(
        candidates,
        profile=MatchingProfile(
            tenant_id="tenant-a",
            limit=2,
        ),
    )

    assert len(results) == 2
    assert [
        item.rank
        for item in results
    ] == [1, 2]


def test_recommendation_order_is_deterministic(
    pipeline,
) -> None:
    candidates = (
        make_candidate(
            index_key="idx-a",
            rank=1,
        ),
        make_candidate(
            index_key="idx-b",
            inventory_code="UNIT-002",
            rank=1,
        ),
        make_candidate(
            index_key="idx-c",
            inventory_code="UNIT-003",
            rank=2,
        ),
    )

    profile = MatchingProfile(
        tenant_id="tenant-a"
    )

    first = pipeline.match(
        candidates,
        profile=profile,
    )

    second = pipeline.match(
        candidates,
        profile=profile,
    )

    assert [
        item.document.index_key
        for item in first
    ] == [
        item.document.index_key
        for item in second
    ]


def test_empty_candidates_are_safe(
    pipeline,
) -> None:
    results = pipeline.match(
        (),
        profile=MatchingProfile(
            tenant_id="tenant-a"
        ),
    )

    assert results == ()


def test_profile_weights_must_have_positive_total(
) -> None:
    with pytest.raises(
        MatchingConfigurationError
    ):
        MatchingProfile(
            tenant_id="tenant-a",
            search_weight=0.0,
            preference_weight=0.0,
        )


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(
        MatchingConfigurationError
    ):
        MatchingProfile(
            tenant_id="tenant-a",
            search_weight=-1.0,
        )


def test_limit_must_be_positive() -> None:
    with pytest.raises(
        MatchingLimitError
    ):
        MatchingProfile(
            tenant_id="tenant-a",
            limit=0,
        )


def test_tenant_is_required() -> None:
    with pytest.raises(
        MatchingConfigurationError
    ):
        MatchingProfile(
            tenant_id="   "
        )


def test_input_candidates_are_not_mutated(
    pipeline,
) -> None:
    candidates = (
        make_candidate(
            index_key="idx-a",
            rank=1,
        ),
        make_candidate(
            index_key="idx-b",
            inventory_code="UNIT-002",
            rank=2,
        ),
    )

    before = candidates

    pipeline.match(
        candidates,
        profile=MatchingProfile(
            tenant_id="tenant-a"
        ),
    )

    assert candidates == before


def test_invalid_candidate_type_is_rejected(
    pipeline,
) -> None:
    with pytest.raises(
        MatchingCandidateError
    ):
        pipeline.match(
            (object(),),  # type: ignore[arg-type]
            profile=MatchingProfile(
                tenant_id="tenant-a"
            ),
        )
