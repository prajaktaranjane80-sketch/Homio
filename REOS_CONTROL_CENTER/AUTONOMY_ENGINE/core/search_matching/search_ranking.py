from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .hybrid_retrieval import HybridSearchResult


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


class RankingError(ValueError):
    """Base CORE-005 ranking error."""


class RankingLimitError(RankingError):
    """Raised for invalid ranking limits."""


class RankingQueryError(RankingError):
    """Raised for invalid reranking queries."""


class RankingResultError(RankingError):
    """Raised for malformed retrieval results."""


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(
        token.casefold()
        for token in _TOKEN_PATTERN.findall(value)
    )


def _require_query(
    query_text: str,
) -> str:
    if not isinstance(
        query_text,
        str,
    ):
        raise RankingQueryError(
            "query_text must be a string."
        )

    normalized = query_text.strip()

    if not normalized:
        raise RankingQueryError(
            "query_text must be non-empty."
        )

    return normalized


def _require_limit(
    value: int,
    *,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise RankingLimitError(
            f"{field_name} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class RankingConfig:
    """
    Deterministic production ranking configuration.

    Retrieval fusion remains T04.
    Business relevance policy starts here.
    """

    hybrid_weight: float = 0.55
    lexical_weight: float = 0.25
    vector_weight: float = 0.20

    rerank_base_weight: float = 0.70
    rerank_signal_weight: float = 0.30

    exact_code_boost: float = 0.45
    exact_phrase_boost: float = 0.30
    token_coverage_boost: float = 0.25

    default_rerank_window: int = 20

    def __post_init__(self) -> None:
        weights = (
            self.hybrid_weight,
            self.lexical_weight,
            self.vector_weight,
            self.rerank_base_weight,
            self.rerank_signal_weight,
            self.exact_code_boost,
            self.exact_phrase_boost,
            self.token_coverage_boost,
        )

        for weight in weights:
            if (
                isinstance(weight, bool)
                or not isinstance(
                    weight,
                    (int, float),
                )
            ):
                raise RankingError(
                    "ranking weights must be numeric."
                )

            if weight < 0:
                raise RankingError(
                    "ranking weights cannot be negative."
                )

        if (
            self.hybrid_weight
            + self.lexical_weight
            + self.vector_weight
            <= 0
        ):
            raise RankingError(
                "at least one primary ranking weight "
                "must be greater than zero."
            )

        if (
            self.rerank_base_weight
            + self.rerank_signal_weight
            <= 0
        ):
            raise RankingError(
                "rerank weights must have a "
                "positive total."
            )

        if (
            self.exact_code_boost
            + self.exact_phrase_boost
            + self.token_coverage_boost
            <= 0
        ):
            raise RankingError(
                "rerank signal weights must have "
                "a positive total."
            )

        if (
            isinstance(
                self.default_rerank_window,
                bool,
            )
            or not isinstance(
                self.default_rerank_window,
                int,
            )
            or self.default_rerank_window < 1
        ):
            raise RankingError(
                "default_rerank_window must be "
                "a positive integer."
            )


@dataclass(frozen=True, slots=True)
class RankedSearchResult:
    """
    Immutable deterministic ranking result.

    ranking_score:
        First-stage relevance.

    rerank_score:
        Second-stage relevance if reranking occurred.

    final_score:
        Effective score used for ordering.
    """

    retrieval: HybridSearchResult
    ranking_score: float
    rank: int
    rerank_score: float | None = None
    rerank_rank: int | None = None

    @property
    def document(self):
        return self.retrieval.document

    @property
    def inventory_id(self) -> str:
        return self.retrieval.inventory_id

    @property
    def inventory_code(self) -> str:
        return self.retrieval.inventory_code

    @property
    def tenant_id(self) -> str:
        return self.retrieval.tenant_id

    @property
    def index_key(self) -> str:
        return self.retrieval.index_key

    @property
    def final_score(self) -> float:
        if self.rerank_score is not None:
            return self.rerank_score

        return self.ranking_score


def _rank_signal(
    rank: int | None,
) -> float:
    if rank is None:
        return 0.0

    if rank < 1:
        return 0.0

    return 1.0 / float(rank)


def _normalize(
    value: float,
    *,
    maximum: float,
) -> float:
    if maximum <= 0:
        return 0.0

    normalized = value / maximum

    return max(
        0.0,
        min(
            1.0,
            normalized,
        ),
    )


@dataclass(frozen=True, slots=True)
class SearchRankingPipeline:
    """
    Deterministic ranking and second-stage reranking.

    No model call.
    No AI decision engine.
    No source-of-truth mutation.
    """

    config: RankingConfig = RankingConfig()

    def rank(
        self,
        results: Iterable[HybridSearchResult],
        *,
        limit: int | None = None,
    ) -> tuple[RankedSearchResult, ...]:
        materialized = tuple(results)

        for result in materialized:
            if not isinstance(
                result,
                HybridSearchResult,
            ):
                raise RankingResultError(
                    "rank expects HybridSearchResult values."
                )

        if limit is not None:
            limit = _require_limit(
                limit,
                field_name="limit",
            )

        if not materialized:
            return ()

        maximum_rrf = max(
            (
                result.rrf_score
                for result in materialized
            ),
            default=0.0,
        )

        primary_weight_total = (
            self.config.hybrid_weight
            + self.config.lexical_weight
            + self.config.vector_weight
        )

        scored: list[
            tuple[
                HybridSearchResult,
                float,
            ]
        ] = []

        for result in materialized:
            hybrid_component = _normalize(
                result.rrf_score,
                maximum=maximum_rrf,
            )

            lexical_component = _rank_signal(
                result.lexical_rank
            )

            vector_component = _rank_signal(
                result.vector_rank
            )

            score = (
                (
                    self.config.hybrid_weight
                    * hybrid_component
                )
                + (
                    self.config.lexical_weight
                    * lexical_component
                )
                + (
                    self.config.vector_weight
                    * vector_component
                )
            ) / primary_weight_total

            scored.append(
                (
                    result,
                    score,
                )
            )

        scored.sort(
            key=lambda item: (
                -item[1],
                -item[0].rrf_score,
                item[0].index_key.casefold(),
            )
        )

        if limit is not None:
            scored = scored[:limit]

        return tuple(
            RankedSearchResult(
                retrieval=result,
                ranking_score=score,
                rank=position,
            )
            for position, (
                result,
                score,
            ) in enumerate(
                scored,
                start=1,
            )
        )

    def _rerank_signal(
        self,
        result: RankedSearchResult,
        *,
        query_text: str,
    ) -> float:
        document = result.document

        query = query_text.casefold()

        inventory_code = (
            document.inventory_code
            .casefold()
        )

        name = document.name.casefold()

        complete_text = (
            f"{name} "
            f"{inventory_code} "
            f"{document.inventory_type} "
            f"{document.lifecycle} "
            f"{document.availability}"
        ).casefold()

        query_tokens = set(
            _tokens(query_text)
        )

        document_tokens = set(
            _tokens(complete_text)
        )

        exact_code = (
            1.0
            if (
                query == inventory_code
                or inventory_code in query
            )
            else 0.0
        )

        exact_phrase = (
            1.0
            if query in complete_text
            else 0.0
        )

        token_coverage = 0.0

        if query_tokens:
            token_coverage = (
                len(
                    query_tokens.intersection(
                        document_tokens
                    )
                )
                / len(query_tokens)
            )

        signal_weight_total = (
            self.config.exact_code_boost
            + self.config.exact_phrase_boost
            + self.config.token_coverage_boost
        )

        return (
            (
                self.config.exact_code_boost
                * exact_code
            )
            + (
                self.config.exact_phrase_boost
                * exact_phrase
            )
            + (
                self.config.token_coverage_boost
                * token_coverage
            )
        ) / signal_weight_total

    def rerank(
        self,
        ranked_results: Iterable[
            RankedSearchResult
        ],
        *,
        query_text: str,
        window: int | None = None,
    ) -> tuple[RankedSearchResult, ...]:
        query_text = _require_query(
            query_text
        )

        materialized = tuple(
            ranked_results
        )

        for result in materialized:
            if not isinstance(
                result,
                RankedSearchResult,
            ):
                raise RankingResultError(
                    "rerank expects RankedSearchResult values."
                )

        if not materialized:
            return ()

        if window is None:
            window = (
                self.config.default_rerank_window
            )

        window = _require_limit(
            window,
            field_name="window",
        )

        actual_window = min(
            window,
            len(materialized),
        )

        base_weight_total = (
            self.config.rerank_base_weight
            + self.config.rerank_signal_weight
        )

        reranked_head: list[
            tuple[
                RankedSearchResult,
                float,
                float,
            ]
        ] = []

        for result in materialized[
            :actual_window
        ]:
            signal = self._rerank_signal(
                result,
                query_text=query_text,
            )

            final_score = (
                (
                    self.config.rerank_base_weight
                    * result.ranking_score
                )
                + (
                    self.config.rerank_signal_weight
                    * signal
                )
            ) / base_weight_total

            reranked_head.append(
                (
                    result,
                    final_score,
                    signal,
                )
            )

        reranked_head.sort(
            key=lambda item: (
                -item[1],
                -item[0].ranking_score,
                item[0].index_key.casefold(),
            )
        )

        output: list[
            RankedSearchResult
        ] = []

        for result, final_score, signal in (
            reranked_head
        ):
            output.append(
                RankedSearchResult(
                    retrieval=result.retrieval,
                    ranking_score=result.ranking_score,
                    rank=0,
                    rerank_score=final_score,
                    rerank_rank=0,
                )
            )

        # Tail is deliberately not re-scored.
        output.extend(
            materialized[actual_window:]
        )

        normalized_output: list[
            RankedSearchResult
        ] = []

        for position, result in enumerate(
            output,
            start=1,
        ):
            rerank_rank = (
                position
                if position <= actual_window
                else None
            )

            normalized_output.append(
                RankedSearchResult(
                    retrieval=result.retrieval,
                    ranking_score=result.ranking_score,
                    rank=position,
                    rerank_score=(
                        result.rerank_score
                        if position
                        <= actual_window
                        else None
                    ),
                    rerank_rank=rerank_rank,
                )
            )

        return tuple(
            normalized_output
        )


__all__ = [
    "RankedSearchResult",
    "RankingError",
    "RankingLimitError",
    "RankingQueryError",
    "RankingResultError",
    "RankingConfig",
    "SearchRankingPipeline",
]
