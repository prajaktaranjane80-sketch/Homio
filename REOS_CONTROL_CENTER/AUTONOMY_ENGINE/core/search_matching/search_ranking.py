"""
CORE-005 / Point 06 — Ranking & Relevance.

Owns:
- relevance contract
- ranking inputs
- deterministic tie-breaking
- ranking version
- ranking explanation
- feature provenance
- ranking reproducibility
- explicit non-autonomous business boundary

Does NOT own:
- search retrieval
- matching policy
- commercial decisions
- commission
- ownership
- fraud
- governance
- AI decision authority
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from math import isfinite
from typing import Any, Iterable, Mapping

from .search_index_contract import (
    InventoryIndexDocument,
)


class SearchRankingError(ValueError):
    """Base ranking error."""


class SearchRankingInputError(SearchRankingError):
    """Raised when ranking input is invalid."""


class SearchRankingVersionError(SearchRankingError):
    """Raised when ranking version metadata is invalid."""


RANKING_VERSION = 1


@dataclass(frozen=True, slots=True)
class RankingFeature:
    """
    One deterministic relevance feature.

    Provenance identifies exactly how the feature was produced.
    """

    name: str
    value: float
    provenance: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
        ):
            raise SearchRankingInputError(
                "feature name must be non-empty."
            )

        if isinstance(self.value, bool):
            raise SearchRankingInputError(
                "feature value must be numeric."
            )

        try:
            normalized = float(
                self.value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise SearchRankingInputError(
                "feature value must be numeric."
            ) from exc

        if not isfinite(normalized):
            raise SearchRankingInputError(
                "feature value must be finite."
            )

        if (
            not isinstance(
                self.provenance,
                str,
            )
            or not self.provenance.strip()
        ):
            raise SearchRankingInputError(
                "feature provenance must be non-empty."
            )

        object.__setattr__(
            self,
            "value",
            normalized,
        )


@dataclass(frozen=True, slots=True)
class RankingExplanation:
    """
    Transparent explanation of ranking inputs.
    """

    features: tuple[RankingFeature, ...]
    ranking_version: int

    def __post_init__(self) -> None:
        if (
            isinstance(
                self.ranking_version,
                bool,
            )
            or not isinstance(
                self.ranking_version,
                int,
            )
            or self.ranking_version < 1
        ):
            raise SearchRankingVersionError(
                "ranking_version must be positive."
            )

        names = [
            feature.name
            for feature in self.features
        ]

        if len(names) != len(set(names)):
            raise SearchRankingInputError(
                "Duplicate ranking feature names."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranking_version": self.ranking_version,
            "features": [
                {
                    "name": feature.name,
                    "value": feature.value,
                    "provenance": feature.provenance,
                }
                for feature in self.features
            ],
        }


@dataclass(frozen=True, slots=True)
class RankingCandidate:
    """
    Input to the ranking boundary.

    `retrieval_score` is an upstream retrieval signal.
    It is not business value.
    """

    document: InventoryIndexDocument
    retrieval_score: float = 0.0
    lexical_score: float = 0.0
    vector_score: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(
            self.document,
            InventoryIndexDocument,
        ):
            raise SearchRankingInputError(
                "document must be InventoryIndexDocument."
            )

        values = (
            "retrieval_score",
            "lexical_score",
            "vector_score",
        )

        for field_name in values:
            value = getattr(
                self,
                field_name,
            )

            if isinstance(value, bool):
                raise SearchRankingInputError(
                    f"{field_name} must be numeric."
                )

            try:
                normalized = float(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise SearchRankingInputError(
                    f"{field_name} must be numeric."
                ) from exc

            if not isfinite(normalized):
                raise SearchRankingInputError(
                    f"{field_name} must be finite."
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )


@dataclass(frozen=True, slots=True)
class RankedSearchResult:
    """
    Immutable ranked result.

    Ranking is deterministic and reproducible.
    No autonomous business decision is made.
    """

    document: InventoryIndexDocument
    score: float
    rank: int
    explanation: RankingExplanation

    def __post_init__(self) -> None:
        if (
            isinstance(self.rank, bool)
            or not isinstance(self.rank, int)
            or self.rank < 1
        ):
            raise SearchRankingError(
                "rank must be positive."
            )

        if isinstance(self.score, bool):
            raise SearchRankingError(
                "score must be numeric."
            )

        try:
            normalized = float(
                self.score
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise SearchRankingError(
                "score must be numeric."
            ) from exc

        if not isfinite(normalized):
            raise SearchRankingError(
                "score must be finite."
            )

        object.__setattr__(
            self,
            "score",
            normalized,
        )

        if not isinstance(
            self.explanation,
            RankingExplanation,
        ):
            raise SearchRankingError(
                "explanation must be RankingExplanation."
            )

    @property
    def retrieval(self) -> RankingCandidate:
        """
        Compatibility-facing view for downstream consumers.

        It preserves ranking output without creating another result engine.
        """
        return RankingCandidate(
            document=self.document
        )

    @property
    def result(self) -> InventoryIndexDocument:
        """
        Compatibility alias for consumers expecting `.result`.
        """
        return self.document


@dataclass(frozen=True, slots=True)
class RankingConfig:
    """
    Explicit deterministic ranking weights.

    These are retrieval/relevance weights only.
    """

    retrieval_weight: float = 1.0
    lexical_weight: float = 0.5
    vector_weight: float = 0.5

    def __post_init__(self) -> None:
        for field_name in (
            "retrieval_weight",
            "lexical_weight",
            "vector_weight",
        ):
            value = getattr(
                self,
                field_name,
            )

            if isinstance(value, bool):
                raise SearchRankingInputError(
                    f"{field_name} must be numeric."
                )

            try:
                normalized = float(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise SearchRankingInputError(
                    f"{field_name} must be numeric."
                ) from exc

            if not isfinite(normalized):
                raise SearchRankingInputError(
                    f"{field_name} must be finite."
                )

            if normalized < 0:
                raise SearchRankingInputError(
                    f"{field_name} cannot be negative."
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )


@dataclass(frozen=True, slots=True)
class SearchRankingPipeline:
    """
    Deterministic ranking/reranking boundary.
    """

    config: RankingConfig = RankingConfig()
    ranking_version: int = RANKING_VERSION

    def __post_init__(self) -> None:
        if (
            isinstance(
                self.ranking_version,
                bool,
            )
            or not isinstance(
                self.ranking_version,
                int,
            )
            or self.ranking_version < 1
        ):
            raise SearchRankingVersionError(
                "ranking_version must be positive."
            )

    def _calculate_features(
        self,
        candidate: RankingCandidate,
    ) -> tuple[RankingFeature, ...]:
        return (
            RankingFeature(
                name="retrieval_score",
                value=candidate.retrieval_score,
                provenance="UPSTREAM_RETRIEVAL",
            ),
            RankingFeature(
                name="lexical_score",
                value=candidate.lexical_score,
                provenance="LEXICAL_RETRIEVAL",
            ),
            RankingFeature(
                name="vector_score",
                value=candidate.vector_score,
                provenance="VECTOR_RETRIEVAL",
            ),
        )

    def _score(
        self,
        candidate: RankingCandidate,
    ) -> float:
        return (
            candidate.retrieval_score
            * self.config.retrieval_weight
            + candidate.lexical_score
            * self.config.lexical_weight
            + candidate.vector_score
            * self.config.vector_weight
        )

    def rank(
        self,
        candidates: Iterable[RankingCandidate],
    ) -> tuple[RankedSearchResult, ...]:
        if isinstance(
            candidates,
            (str, bytes),
        ):
            raise SearchRankingInputError(
                "candidates must be iterable."
            )

        materialized = list(candidates)

        seen: set[str] = set()
        scored: list[
            tuple[
                RankingCandidate,
                float,
                RankingExplanation,
            ]
        ] = []

        for candidate in materialized:
            if not isinstance(
                candidate,
                RankingCandidate,
            ):
                raise SearchRankingInputError(
                    "candidates must contain RankingCandidate."
                )

            key = candidate.document.index_key

            if key in seen:
                raise SearchRankingInputError(
                    "Duplicate ranking candidate identity."
                )

            seen.add(key)

            features = self._calculate_features(
                candidate
            )

            score = self._score(
                candidate
            )

            explanation = RankingExplanation(
                features=features,
                ranking_version=self.ranking_version,
            )

            scored.append(
                (
                    candidate,
                    score,
                    explanation,
                )
            )

        scored.sort(
            key=lambda item: (
                -item[1],
                item[0].document.index_key.casefold(),
            )
        )

        return tuple(
            RankedSearchResult(
                document=candidate.document,
                score=score,
                rank=index,
                explanation=explanation,
            )
            for index, (
                candidate,
                score,
                explanation,
            ) in enumerate(
                scored,
                start=1,
            )
        )

    def rerank(
        self,
        results: Iterable[
            RankedSearchResult
        ],
        *,
        exact_inventory_codes: Iterable[str] = (),
        exact_phrase: str | None = None,
    ) -> tuple[RankedSearchResult, ...]:
        """
        Deterministic second-stage reranking.

        Still retrieval relevance only.
        """
        exact_codes = {
            str(value).casefold()
            for value in exact_inventory_codes
        }

        phrase = (
            exact_phrase.casefold().strip()
            if exact_phrase is not None
            else ""
        )

        adjusted: list[
            tuple[
                RankedSearchResult,
                float,
            ]
        ] = []

        for result in results:
            if not isinstance(
                result,
                RankedSearchResult,
            ):
                raise SearchRankingInputError(
                    "results must contain RankedSearchResult."
                )

            score = result.score

            if (
                result.document.inventory_code.casefold()
                in exact_codes
            ):
                score += 10.0

            if phrase:
                if (
                    phrase
                    in result.document.name.casefold()
                ):
                    score += 5.0

            adjusted.append(
                (
                    result,
                    score,
                )
            )

        adjusted.sort(
            key=lambda item: (
                -item[1],
                item[0].document.index_key.casefold(),
            )
        )

        return tuple(
            RankedSearchResult(
                document=result.document,
                score=score,
                rank=index,
                explanation=result.explanation,
            )
            for index, (
                result,
                score,
            ) in enumerate(
                adjusted,
                start=1,
            )
        )

    def reproducibility_fingerprint(
        self,
        results: Iterable[
            RankedSearchResult
        ],
    ) -> str:
        canonical = []

        for result in results:
            canonical.append(
                {
                    "index_key": result.document.index_key,
                    "score": result.score,
                    "rank": result.rank,
                    "ranking_version": (
                        result.explanation.ranking_version
                    ),
                }
            )

        payload = {
            "ranking_version": self.ranking_version,
            "results": canonical,
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            encoded.encode("utf-8")
        ).hexdigest()


__all__ = [
    "RANKING_VERSION",
    "SearchRankingError",
    "SearchRankingInputError",
    "SearchRankingVersionError",
    "RankingFeature",
    "RankingExplanation",
    "RankingCandidate",
    "RankedSearchResult",
    "RankingConfig",
    "SearchRankingPipeline",
]
