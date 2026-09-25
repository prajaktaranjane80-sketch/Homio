from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import HybridSearchResult
from AUTONOMY_ENGINE.core.search_matching.search_ranking import (
    RankingConfig,
    RankingError,
    RankingLimitError,
    RankingQueryError,
    SearchRankingPipeline,
)


def make_document(
    *,
    index_key: str,
    inventory_code: str,
    name: str,
):
    return SimpleNamespace(
        index_key=index_key,
        inventory_code=inventory_code,
        name=name,
    )


def make_result(
    *,
    index_key: str,
    inventory_code: str,
    name: str,
    rrf_score: float,
    lexical_rank: int | None,
    vector_rank: int | None,
):
    return HybridSearchResult(
        document=make_document(
            index_key=index_key,
            inventory_code=inventory_code,
            name=name,
        ),
        rrf_score=rrf_score,
        lexical_rank=lexical_rank,
        vector_rank=vector_rank,
    )


@pytest.fixture
def results():
    return (
        make_result(
            index_key="idx-001",
            inventory_code="UNIT-001",
            name="Premium Two Bedroom",
            rrf_score=0.030,
            lexical_rank=1,
            vector_rank=2,
        ),
        make_result(
            index_key="idx-002",
            inventory_code="UNIT-002",
            name="Standard Two Bedroom",
            rrf_score=0.020,
            lexical_rank=2,
            vector_rank=3,
        ),
        make_result(
            index_key="idx-003",
            inventory_code="UNIT-003",
            name="Premium Three Bedroom",
            rrf_score=0.010,
            lexical_rank=None,
            vector_rank=1,
        ),
    )


def test_rank_orders_by_score(results):
    pipeline = SearchRankingPipeline()

    ranked = pipeline.rank(results)

    assert [item.inventory_code for item in ranked] == [
        "UNIT-001",
        "UNIT-002",
        "UNIT-003",
    ]


def test_lexical_signal_contributes_to_ranking():
    pipeline = SearchRankingPipeline(
        config=RankingConfig(
            hybrid_weight=0.0,
            lexical_weight=1.0,
            vector_weight=0.0,
        )
    )

    results = (
        make_result(
            index_key="a",
            inventory_code="A",
            name="A",
            rrf_score=0.0,
            lexical_rank=1,
            vector_rank=None,
        ),
        make_result(
            index_key="b",
            inventory_code="B",
            name="B",
            rrf_score=0.0,
            lexical_rank=2,
            vector_rank=None,
        ),
    )

    ranked = pipeline.rank(results)

    assert [item.inventory_code for item in ranked] == ["A", "B"]


def test_vector_signal_contributes_to_ranking():
    pipeline = SearchRankingPipeline(
        config=RankingConfig(
            hybrid_weight=0.0,
            lexical_weight=0.0,
            vector_weight=1.0,
        )
    )

    results = (
        make_result(
            index_key="a",
            inventory_code="A",
            name="A",
            rrf_score=0.0,
            lexical_rank=None,
            vector_rank=1,
        ),
        make_result(
            index_key="b",
            inventory_code="B",
            name="B",
            rrf_score=0.0,
            lexical_rank=None,
            vector_rank=2,
        ),
    )

    ranked = pipeline.rank(results)

    assert [item.inventory_code for item in ranked] == ["A", "B"]


def test_missing_rank_signals_are_safe(results):
    pipeline = SearchRankingPipeline()

    ranked = pipeline.rank(results)

    assert len(ranked) == 3
    assert all(item.ranking_score >= 0 for item in ranked)


def test_rank_is_deterministic(results):
    pipeline = SearchRankingPipeline()

    first = pipeline.rank(results)
    second = pipeline.rank(results)

    assert [
        (item.inventory_code, item.ranking_score)
        for item in first
    ] == [
        (item.inventory_code, item.ranking_score)
        for item in second
    ]


def test_limit_is_honored(results):
    pipeline = SearchRankingPipeline()

    ranked = pipeline.rank(results, limit=2)

    assert len(ranked) == 2


def test_rerank_rewards_exact_inventory_code():
    pipeline = SearchRankingPipeline(
        config=RankingConfig(
            hybrid_weight=0.0,
            lexical_weight=0.0,
            vector_weight=0.0,
        )
    )

    results = pipeline.rank(
        (
            make_result(
                index_key="a",
                inventory_code="UNIT-001",
                name="Other Property",
                rrf_score=0.0,
                lexical_rank=None,
                vector_rank=None,
            ),
            make_result(
                index_key="b",
                inventory_code="UNIT-002",
                name="Other Property",
                rrf_score=0.0,
                lexical_rank=None,
                vector_rank=None,
            ),
        )
    )

    reranked = pipeline.rerank(
        results,
        query_text="UNIT-001",
    )

    assert [item.inventory_code for item in reranked] == [
        "UNIT-001",
        "UNIT-002",
    ]


def test_rerank_rewards_exact_phrase():
    pipeline = SearchRankingPipeline(
        config=RankingConfig(
            hybrid_weight=0.0,
            lexical_weight=0.0,
            vector_weight=0.0,
        )
    )

    results = pipeline.rank(
        (
            make_result(
                index_key="a",
                inventory_code="UNIT-001",
                name="Premium Two Bedroom",
                rrf_score=0.0,
                lexical_rank=None,
                vector_rank=None,
            ),
            make_result(
                index_key="b",
                inventory_code="UNIT-002",
                name="Luxury Apartment",
                rrf_score=0.0,
                lexical_rank=None,
                vector_rank=None,
            ),
        )
    )

    reranked = pipeline.rerank(
        results,
        query_text="Premium Two",
    )

    assert [item.inventory_code for item in reranked] == [
        "UNIT-001",
        "UNIT-002",
    ]


def test_rerank_rewards_token_coverage():
    pipeline = SearchRankingPipeline(
        config=RankingConfig(
            hybrid_weight=0.0,
            lexical_weight=0.0,
            vector_weight=0.0,
        )
    )

    results = pipeline.rank(
        (
            make_result(
                index_key="a",
                inventory_code="UNIT-001",
                name="Premium Three Bedroom",
                rrf_score=0.0,
                lexical_rank=None,
                vector_rank=None,
            ),
            make_result(
                index_key="b",
                inventory_code="UNIT-002",
                name="Standard Apartment",
                rrf_score=0.0,
                lexical_rank=None,
                vector_rank=None,
            ),
        )
    )

    reranked = pipeline.rerank(
        results,
        query_text="Premium Bedroom",
    )

    assert reranked[0].inventory_code == "UNIT-001"


def test_rerank_window_limits_second_stage(results):
    pipeline = SearchRankingPipeline()

    ranked = pipeline.rank(results)
    reranked = pipeline.rerank(
        ranked,
        query_text="Premium",
        window=2,
    )

    assert len(reranked) == 3
    assert reranked[0].rerank_score is not None
    assert reranked[1].rerank_score is not None
    assert reranked[2].rerank_score is None


def test_ranking_does_not_mutate_input(results):
    pipeline = SearchRankingPipeline()

    original = tuple(results)
    pipeline.rank(results)

    assert results == original


def test_invalid_limit_is_rejected(results):
    pipeline = SearchRankingPipeline()

    with pytest.raises(RankingLimitError):
        pipeline.rank(results, limit=0)


def test_invalid_query_is_rejected(results):
    pipeline = SearchRankingPipeline()

    ranked = pipeline.rank(results)

    with pytest.raises(RankingQueryError):
        pipeline.rerank(
            ranked,
            query_text="   ",
        )


def test_negative_weight_is_rejected():
    with pytest.raises(RankingError):
        RankingConfig(hybrid_weight=-1.0)


def test_rank_numbers_are_one_based(results):
    pipeline = SearchRankingPipeline()

    ranked = pipeline.rank(results)

    assert [item.rank for item in ranked] == [1, 2, 3]
