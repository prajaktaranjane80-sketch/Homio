from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.core.search_matching.matching import (
    MatchingConfigurationError,
    MatchingLimitError,
    MatchingProfile,
    MatchingRecommendationPipeline,
    MatchingTenantError,
)
from AUTONOMY_ENGINE.core.search_matching.search_ranking import RankedSearchResult


def make_candidate(
    *,
    index_key: str,
    tenant_id: str = "tenant-001",
    project_id: str = "project-001",
    inventory_code: str = "UNIT-001",
    inventory_type: str = "RESIDENTIAL_UNIT",
    name: str = "Premium Two Bedroom",
    availability: str = "AVAILABLE",
    rank: int = 1,
) -> RankedSearchResult:
    document = SimpleNamespace(
        index_key=index_key,
        tenant_id=tenant_id,
        project_id=project_id,
        inventory_id=f"inventory-{index_key}",
        inventory_code=inventory_code,
        inventory_type=inventory_type,
        name=name,
        availability=availability,
    )

    return RankedSearchResult(
        result=SimpleNamespace(document=document),
        ranking_score=1.0,
        rerank_score=1.0,
        rank=rank,
    )


@pytest.fixture
def pipeline():
    return MatchingRecommendationPipeline()


def test_basic_matching_returns_recommendation(pipeline):
    results = pipeline.match(
        (
            make_candidate(index_key="idx-001"),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
        ),
    )

    assert len(results) == 1
    assert results[0].inventory_code == "UNIT-001"
    assert results[0].rank == 1


def test_matching_is_tenant_safe(pipeline):
    with pytest.raises(MatchingTenantError):
        pipeline.match(
            (
                make_candidate(
                    index_key="idx-999",
                    tenant_id="tenant-999",
                ),
            ),
            profile=MatchingProfile(
                tenant_id="tenant-001",
            ),
        )


def test_required_inventory_type_is_enforced(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="res",
                inventory_type="RESIDENTIAL_UNIT",
            ),
            make_candidate(
                index_key="plot",
                inventory_type="PLOT",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            required_inventory_types=frozenset({"RESIDENTIAL_UNIT"}),
        ),
    )

    assert [item.inventory_code for item in results] == [
        "UNIT-001",
    ]


def test_required_project_is_enforced(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="p1",
                project_id="project-001",
            ),
            make_candidate(
                index_key="p2",
                project_id="project-002",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            required_project_ids=frozenset({"project-001"}),
        ),
    )

    assert len(results) == 1
    assert results[0].project_id == "project-001"


def test_required_availability_is_enforced(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="available",
                availability="AVAILABLE",
            ),
            make_candidate(
                index_key="reserved",
                availability="RESERVED",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            required_availability=frozenset({"AVAILABLE"}),
        ),
    )

    assert len(results) == 1
    assert results[0].document.availability == "AVAILABLE"


def test_excluded_keyword_is_hard_block(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="good",
                name="Premium Two Bedroom",
            ),
            make_candidate(
                index_key="bad",
                name="Premium Studio",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            excluded_keywords=frozenset({"studio"}),
        ),
    )

    assert len(results) == 1
    assert results[0].candidate.document.index_key == "good"


def test_preferred_inventory_type_improves_score(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="res",
                inventory_type="RESIDENTIAL_UNIT",
                rank=1,
            ),
            make_candidate(
                index_key="plot",
                inventory_type="PLOT",
                rank=1,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_inventory_types=frozenset(
                {"RESIDENTIAL_UNIT"}
            ),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert results[0].document.inventory_type == "RESIDENTIAL_UNIT"
    assert "preferred_inventory_type" in (
        results[0].explanation.matched_signals
    )


def test_preferred_project_improves_score(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="target",
                project_id="project-002",
                rank=1,
            ),
            make_candidate(
                index_key="other",
                project_id="project-001",
                rank=1,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_project_ids=frozenset({"project-002"}),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert results[0].project_id == "project-002"


def test_preferred_availability_is_explainable(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="reserved",
                availability="RESERVED",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_availability=frozenset({"RESERVED"}),
        ),
    )

    assert "preferred_availability" in (
        results[0].explanation.matched_signals
    )


def test_preferred_inventory_code_is_supported(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="target",
                inventory_code="UNIT-777",
            ),
            make_candidate(
                index_key="other",
                inventory_code="UNIT-001",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_inventory_codes=frozenset({"UNIT-777"}),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert results[0].inventory_code == "UNIT-777"


def test_keyword_preference_is_supported(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="premium",
                name="Premium Two Bedroom",
            ),
            make_candidate(
                index_key="standard",
                name="Standard Apartment",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_keywords=frozenset({"premium", "bedroom"}),
            search_weight=0.5,
            preference_weight=0.5,
        ),
    )

    assert results[0].document.index_key == "premium"
    assert "preferred_keywords" in (
        results[0].explanation.matched_signals
    )


def test_search_rank_remains_a_stable_signal(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="first",
                rank=1,
            ),
            make_candidate(
                index_key="second",
                rank=2,
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
        ),
    )

    assert results[0].document.index_key == "first"
    assert results[0].search_relevance > results[1].search_relevance


def test_limit_is_enforced(pipeline):
    results = pipeline.match(
        tuple(
            make_candidate(
                index_key=f"idx-{index}",
                rank=index,
            )
            for index in range(1, 6)
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            limit=2,
        ),
    )

    assert len(results) == 2
    assert [item.rank for item in results] == [1, 2]


def test_recommendation_order_is_deterministic(pipeline):
    candidates = (
        make_candidate(index_key="idx-a", rank=1),
        make_candidate(index_key="idx-b", rank=1),
        make_candidate(index_key="idx-c", rank=2),
    )

    profile = MatchingProfile(
        tenant_id="tenant-001",
    )

    first = pipeline.match(candidates, profile=profile)
    second = pipeline.match(candidates, profile=profile)

    assert [
        item.document.index_key for item in first
    ] == [
        item.document.index_key for item in second
    ]


def test_match_is_explainable(pipeline):
    results = pipeline.match(
        (
            make_candidate(index_key="idx-001"),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
            preferred_inventory_types=frozenset(
                {"RESIDENTIAL_UNIT"}
            ),
        ),
    )

    explanation = results[0].explanation

    assert explanation.search_relevance > 0
    assert explanation.preference_score > 0
    assert isinstance(explanation.matched_signals, tuple)


def test_empty_candidates_are_safe(pipeline):
    results = pipeline.match(
        (),
        profile=MatchingProfile(
            tenant_id="tenant-001",
        ),
    )

    assert results == ()


def test_profile_weights_are_validated():
    with pytest.raises(MatchingConfigurationError):
        MatchingProfile(
            tenant_id="tenant-001",
            search_weight=0.0,
            preference_weight=0.0,
        )


def test_negative_weight_is_rejected():
    with pytest.raises(MatchingConfigurationError):
        MatchingProfile(
            tenant_id="tenant-001",
            search_weight=-1.0,
        )


def test_limit_must_be_positive():
    with pytest.raises(MatchingLimitError):
        MatchingProfile(
            tenant_id="tenant-001",
            limit=0,
        )


def test_tenant_is_required():
    with pytest.raises(MatchingConfigurationError):
        MatchingProfile(
            tenant_id="   ",
        )


def test_input_candidates_are_not_mutated(pipeline):
    candidates = (
        make_candidate(index_key="idx-001", rank=1),
        make_candidate(index_key="idx-002", rank=2),
    )

    before = candidates

    pipeline.match(
        candidates,
        profile=MatchingProfile(
            tenant_id="tenant-001",
        ),
    )

    assert candidates == before


def test_result_preserves_downstream_inventory_identity(pipeline):
    results = pipeline.match(
        (
            make_candidate(
                index_key="idx-001",
            ),
        ),
        profile=MatchingProfile(
            tenant_id="tenant-001",
        ),
    )

    assert results[0].inventory_id == "inventory-idx-001"
    assert results[0].inventory_code == "UNIT-001"
    assert results[0].project_id == "project-001"
    assert results[0].tenant_id == "tenant-001"
