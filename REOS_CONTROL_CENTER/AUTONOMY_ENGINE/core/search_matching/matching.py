from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from .search_ranking import RankedSearchResult


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


class MatchingError(ValueError):
    """Base CORE-005 matching error."""


class MatchingTenantError(MatchingError):
    """Raised when a candidate crosses the tenant boundary."""


class MatchingConfigurationError(MatchingError):
    """Raised when a matching profile is invalid."""


class MatchingLimitError(MatchingError):
    """Raised when a matching limit is invalid."""


class MatchingCandidateError(MatchingError):
    """Raised when a matching candidate is malformed."""


def _normalize_text(
    value: str,
    *,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise MatchingConfigurationError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise MatchingConfigurationError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _normalize_set(
    values: Iterable[str],
    *,
    field_name: str,
) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise MatchingConfigurationError(
            f"{field_name} must be an iterable."
        )

    try:
        normalized = frozenset(
            _normalize_text(
                value,
                field_name=field_name,
            ).casefold()
            for value in values
        )
    except TypeError as exc:
        raise MatchingConfigurationError(
            f"{field_name} must be iterable."
        ) from exc

    return normalized


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        token.casefold()
        for token in _TOKEN_PATTERN.findall(
            value
        )
    )


def _require_positive_limit(
    value: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise MatchingLimitError(
            "limit must be a positive integer."
        )

    return value


def _rank_relevance(
    rank: int,
) -> float:
    if (
        isinstance(rank, bool)
        or not isinstance(rank, int)
        or rank < 1
    ):
        raise MatchingCandidateError(
            "candidate rank must be a positive integer."
        )

    return 1.0 / float(rank)


@dataclass(frozen=True, slots=True)
class MatchingProfile:
    """
    Immutable recommendation profile.

    Hard constraints:
        required_inventory_types
        required_project_ids
        required_availability
        excluded_keywords

    Soft preferences:
        preferred_inventory_types
        preferred_project_ids
        preferred_availability
        preferred_inventory_codes
        preferred_keywords

    Matching remains deterministic and explainable.
    It never makes an irreversible business decision.
    """

    tenant_id: str

    required_inventory_types: frozenset[str] = field(
        default_factory=frozenset
    )
    required_project_ids: frozenset[str] = field(
        default_factory=frozenset
    )
    required_availability: frozenset[str] = field(
        default_factory=frozenset
    )

    preferred_inventory_types: frozenset[str] = field(
        default_factory=frozenset
    )
    preferred_project_ids: frozenset[str] = field(
        default_factory=frozenset
    )
    preferred_availability: frozenset[str] = field(
        default_factory=frozenset
    )
    preferred_inventory_codes: frozenset[str] = field(
        default_factory=frozenset
    )
    preferred_keywords: frozenset[str] = field(
        default_factory=frozenset
    )

    excluded_keywords: frozenset[str] = field(
        default_factory=frozenset
    )

    search_weight: float = 0.60
    preference_weight: float = 0.40

    limit: int = 20

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _normalize_text(
                self.tenant_id,
                field_name="tenant_id",
            ),
        )

        for field_name in (
            "required_inventory_types",
            "required_project_ids",
            "required_availability",
            "preferred_inventory_types",
            "preferred_project_ids",
            "preferred_availability",
            "preferred_inventory_codes",
            "preferred_keywords",
            "excluded_keywords",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_set(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        if (
            isinstance(
                self.search_weight,
                bool,
            )
            or not isinstance(
                self.search_weight,
                (int, float),
            )
            or self.search_weight < 0
        ):
            raise MatchingConfigurationError(
                "search_weight must be "
                "a non-negative number."
            )

        if (
            isinstance(
                self.preference_weight,
                bool,
            )
            or not isinstance(
                self.preference_weight,
                (int, float),
            )
            or self.preference_weight < 0
        ):
            raise MatchingConfigurationError(
                "preference_weight must be "
                "a non-negative number."
            )

        if (
            self.search_weight
            + self.preference_weight
            <= 0
        ):
            raise MatchingConfigurationError(
                "At least one matching weight "
                "must be greater than zero."
            )

        object.__setattr__(
            self,
            "limit",
            _require_positive_limit(
                self.limit
            ),
        )


@dataclass(frozen=True, slots=True)
class MatchExplanation:
    """Immutable explanation of deterministic matching signals."""

    search_relevance: float
    preference_score: float
    matched_signals: tuple[str, ...]
    rejected_signals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MatchRecommendation:
    """Final deterministic recommendation candidate."""

    candidate: RankedSearchResult
    match_score: float
    search_relevance: float
    preference_score: float
    rank: int
    explanation: MatchExplanation

    @property
    def document(self):
        return self.candidate.document

    @property
    def inventory_id(self) -> str:
        return self.candidate.inventory_id

    @property
    def inventory_code(self) -> str:
        return self.candidate.inventory_code

    @property
    def tenant_id(self) -> str:
        return self.candidate.tenant_id

    @property
    def project_id(self) -> str:
        return self.document.project_id


def _extract_candidate_document(
    candidate: RankedSearchResult,
):
    if not isinstance(
        candidate,
        RankedSearchResult,
    ):
        raise MatchingCandidateError(
            "candidate must be RankedSearchResult."
        )

    document = candidate.document

    required = (
        "tenant_id",
        "project_id",
        "inventory_id",
        "inventory_code",
        "inventory_type",
        "name",
        "availability",
        "index_key",
    )

    for field_name in required:
        if not hasattr(
            document,
            field_name,
        ):
            raise MatchingCandidateError(
                f"candidate document is missing "
                f"{field_name}."
            )

    return document


def _hard_constraints_pass(
    document,
    profile: MatchingProfile,
) -> tuple[bool, tuple[str, ...]]:
    rejected: list[str] = []

    inventory_type = str(
        document.inventory_type
    ).casefold()

    project_id = str(
        document.project_id
    ).casefold()

    availability = str(
        document.availability
    ).casefold()

    name_tokens = _tokens(
        str(document.name)
    )

    inventory_code = str(
        document.inventory_code
    ).casefold()

    if (
        profile.required_inventory_types
        and inventory_type
        not in profile.required_inventory_types
    ):
        rejected.append(
            "required_inventory_type"
        )

    if (
        profile.required_project_ids
        and project_id
        not in profile.required_project_ids
    ):
        rejected.append(
            "required_project_id"
        )

    if (
        profile.required_availability
        and availability
        not in profile.required_availability
    ):
        rejected.append(
            "required_availability"
        )

    if (
        profile.excluded_keywords
        and name_tokens.intersection(
            profile.excluded_keywords
        )
    ):
        rejected.append(
            "excluded_keyword"
        )

    if (
        profile.excluded_keywords
        and any(
            keyword
            in inventory_code
            for keyword
            in profile.excluded_keywords
        )
    ):
        rejected.append(
            "excluded_inventory_code"
        )

    return (
        not rejected,
        tuple(rejected),
    )


def _preference_score(
    document,
    profile: MatchingProfile,
) -> tuple[
    float,
    tuple[str, ...],
]:
    matched: list[str] = []
    score = 0.0
    maximum = 0.0

    inventory_type = str(
        document.inventory_type
    ).casefold()

    project_id = str(
        document.project_id
    ).casefold()

    availability = str(
        document.availability
    ).casefold()

    inventory_code = str(
        document.inventory_code
    ).casefold()

    name_tokens = _tokens(
        str(document.name)
    )

    if profile.preferred_inventory_types:
        maximum += 1.0

        if (
            inventory_type
            in profile.preferred_inventory_types
        ):
            score += 1.0
            matched.append(
                "preferred_inventory_type"
            )

    if profile.preferred_project_ids:
        maximum += 1.0

        if (
            project_id
            in profile.preferred_project_ids
        ):
            score += 1.0
            matched.append(
                "preferred_project"
            )

    if profile.preferred_availability:
        maximum += 1.0

        if (
            availability
            in profile.preferred_availability
        ):
            score += 1.0
            matched.append(
                "preferred_availability"
            )

    if profile.preferred_inventory_codes:
        maximum += 1.0

        if (
            inventory_code
            in profile.preferred_inventory_codes
        ):
            score += 1.0
            matched.append(
                "preferred_inventory_code"
            )

    if profile.preferred_keywords:
        maximum += 1.0

        keyword_coverage = (
            len(
                name_tokens.intersection(
                    profile.preferred_keywords
                )
            )
            / len(
                profile.preferred_keywords
            )
        )

        if keyword_coverage > 0:
            score += keyword_coverage
            matched.append(
                "preferred_keywords"
            )

    if maximum <= 0:
        return (
            0.0,
            tuple(),
        )

    return (
        score / maximum,
        tuple(
            sorted(
                matched
            )
        ),
    )


@dataclass(frozen=True, slots=True)
class MatchingRecommendationPipeline:
    """
    Deterministic matching/recommendation layer.

    Inputs:
        T05 ranked search candidates.

    Outputs:
        explainable match recommendations.

    Does not:
        mutate inventory
        modify ownership
        authorize users
        calculate commission
        invoke AI decisions
    """

    def match(
        self,
        candidates: Iterable[
            RankedSearchResult
        ],
        *,
        profile: MatchingProfile,
    ) -> tuple[
        MatchRecommendation,
        ...,
    ]:
        if not isinstance(
            profile,
            MatchingProfile,
        ):
            raise MatchingConfigurationError(
                "profile must be MatchingProfile."
            )

        materialized = tuple(
            candidates
        )

        recommendations: list[
            MatchRecommendation
        ] = []

        for candidate in materialized:
            document = _extract_candidate_document(
                candidate
            )

            # Defense-in-depth: tenant must never cross here.
            if (
                document.tenant_id
                != profile.tenant_id
            ):
                raise MatchingTenantError(
                    "Matching candidate belongs to "
                    "another tenant."
                )

            hard_pass, rejected = (
                _hard_constraints_pass(
                    document,
                    profile,
                )
            )

            if not hard_pass:
                continue

            search_relevance = _rank_relevance(
                candidate.rank
            )

            preference_score, matched = (
                _preference_score(
                    document,
                    profile,
                )
            )

            total_weight = (
                profile.search_weight
                + profile.preference_weight
            )

            match_score = (
                (
                    profile.search_weight
                    * search_relevance
                )
                + (
                    profile.preference_weight
                    * preference_score
                )
            ) / total_weight

            recommendations.append(
                MatchRecommendation(
                    candidate=candidate,
                    match_score=match_score,
                    search_relevance=search_relevance,
                    preference_score=preference_score,
                    rank=0,
                    explanation=MatchExplanation(
                        search_relevance=search_relevance,
                        preference_score=preference_score,
                        matched_signals=tuple(
                            sorted(
                                matched
                            )
                        ),
                        rejected_signals=rejected,
                    ),
                )
            )

        recommendations.sort(
            key=lambda item: (
                -item.match_score,
                -item.preference_score,
                -item.search_relevance,
                item.document.index_key.casefold(),
            )
        )

        limited = recommendations[
            :profile.limit
        ]

        return tuple(
            MatchRecommendation(
                candidate=item.candidate,
                match_score=item.match_score,
                search_relevance=item.search_relevance,
                preference_score=item.preference_score,
                rank=position,
                explanation=item.explanation,
            )
            for position, item in enumerate(
                limited,
                start=1,
            )
        )


__all__ = [
    "MatchExplanation",
    "MatchRecommendation",
    "MatchingCandidateError",
    "MatchingConfigurationError",
    "MatchingError",
    "MatchingLimitError",
    "MatchingProfile",
    "MatchingRecommendationPipeline",
    "MatchingTenantError",
]
