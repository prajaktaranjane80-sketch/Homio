"""
CORE-005 / Point 05 — Matching Domain.

Owns:
- matching request contract
- candidate selection
- hard constraints
- soft preferences
- compatibility rules
- match explanation
- deterministic matching boundary

Does NOT own:
- search execution
- ranking
- ownership
- commission
- fraud
- governance
- AI business decisions
- source-of-truth mutation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from ..inventory.inventory import (
    AvailabilityState,
    InventoryType,
)
from .search_index_contract import InventoryIndexDocument


class MatchingDomainError(ValueError):
    """Base matching-domain error."""


class MatchingTenantError(MatchingDomainError):
    """Raised for tenant-boundary violations."""


class MatchingCriteriaError(MatchingDomainError):
    """Raised for invalid matching criteria."""


class MatchingCandidateError(MatchingDomainError):
    """Raised for invalid matching candidates."""


def _required_text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise MatchingCriteriaError(
            f"{field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise MatchingCriteriaError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _normalize_strings(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise MatchingCriteriaError(
            f"{field_name} must be iterable."
        )

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise MatchingCriteriaError(
            f"{field_name} must be iterable."
        ) from exc

    normalized = {
        _required_text(value, field_name)
        for value in iterator
    }

    return tuple(
        sorted(
            normalized,
            key=str.casefold,
        )
    )


def _normalize_enum_values(
    values,
    enum_type,
    field_name: str,
):
    if isinstance(values, (str, bytes)):
        raise MatchingCriteriaError(
            f"{field_name} must be iterable."
        )

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise MatchingCriteriaError(
            f"{field_name} must be iterable."
        ) from exc

    normalized = set()

    for value in iterator:
        try:
            normalized.add(
                enum_type(value)
            )
        except (TypeError, ValueError) as exc:
            raise MatchingCriteriaError(
                f"{field_name} contains invalid "
                f"value: {value!r}."
            ) from exc

    return tuple(
        sorted(
            normalized,
            key=lambda item: item.value,
        )
    )


@dataclass(frozen=True, slots=True)
class MatchingProfile:
    """
    Immutable matching criteria.

    Hard constraints must be satisfied.
    Soft preferences contribute only to the explanation/score.
    """

    tenant_id: str

    required_inventory_types: tuple[
        InventoryType, ...
    ] = ()

    required_project_ids: tuple[
        str, ...
    ] = ()

    required_availability: tuple[
        AvailabilityState, ...
    ] = ()

    excluded_keywords: tuple[
        str, ...
    ] = ()

    preferred_inventory_types: tuple[
        InventoryType, ...
    ] = ()

    preferred_project_ids: tuple[
        str, ...
    ] = ()

    preferred_availability: tuple[
        AvailabilityState, ...
    ] = ()

    preferred_inventory_codes: tuple[
        str, ...
    ] = ()

    preferred_keywords: tuple[
        str, ...
    ] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tenant_id",
            _required_text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        object.__setattr__(
            self,
            "required_inventory_types",
            _normalize_enum_values(
                self.required_inventory_types,
                InventoryType,
                "required_inventory_types",
            ),
        )

        object.__setattr__(
            self,
            "required_project_ids",
            _normalize_strings(
                self.required_project_ids,
                "required_project_ids",
            ),
        )

        object.__setattr__(
            self,
            "required_availability",
            _normalize_enum_values(
                self.required_availability,
                AvailabilityState,
                "required_availability",
            ),
        )

        object.__setattr__(
            self,
            "excluded_keywords",
            _normalize_strings(
                self.excluded_keywords,
                "excluded_keywords",
            ),
        )

        object.__setattr__(
            self,
            "preferred_inventory_types",
            _normalize_enum_values(
                self.preferred_inventory_types,
                InventoryType,
                "preferred_inventory_types",
            ),
        )

        object.__setattr__(
            self,
            "preferred_project_ids",
            _normalize_strings(
                self.preferred_project_ids,
                "preferred_project_ids",
            ),
        )

        object.__setattr__(
            self,
            "preferred_availability",
            _normalize_enum_values(
                self.preferred_availability,
                AvailabilityState,
                "preferred_availability",
            ),
        )

        object.__setattr__(
            self,
            "preferred_inventory_codes",
            _normalize_strings(
                self.preferred_inventory_codes,
                "preferred_inventory_codes",
            ),
        )

        object.__setattr__(
            self,
            "preferred_keywords",
            _normalize_strings(
                self.preferred_keywords,
                "preferred_keywords",
            ),
        )


@dataclass(frozen=True, slots=True)
class MatchExplanation:
    """
    Transparent deterministic explanation.

    This is explanatory metadata, not an autonomous business decision.
    """

    hard_constraints_passed: tuple[str, ...]
    soft_preferences_matched: tuple[str, ...]
    soft_preferences_missed: tuple[str, ...]
    excluded_reasons: tuple[str, ...] = ()

    @property
    def hard_constraint_count(self) -> int:
        return len(self.hard_constraints_passed)

    @property
    def preference_match_count(self) -> int:
        return len(self.soft_preferences_matched)

    def to_dict(self) -> dict[str, object]:
        return {
            "hard_constraints_passed": list(
                self.hard_constraints_passed
            ),
            "soft_preferences_matched": list(
                self.soft_preferences_matched
            ),
            "soft_preferences_missed": list(
                self.soft_preferences_missed
            ),
            "excluded_reasons": list(
                self.excluded_reasons
            ),
        }


@dataclass(frozen=True, slots=True)
class MatchRecommendation:
    """
    Deterministic matching result.

    The result remains advisory/explanatory.
    No business action is triggered.
    """

    document: InventoryIndexDocument
    score: float
    explanation: MatchExplanation

    def __post_init__(self) -> None:
        if not isinstance(
            self.document,
            InventoryIndexDocument,
        ):
            raise MatchingCandidateError(
                "document must be InventoryIndexDocument."
            )

        if not isinstance(self.score, (int, float)):
            raise MatchingDomainError(
                "score must be numeric."
            )

    @property
    def tenant_id(self) -> str:
        return self.document.tenant_id

    @property
    def inventory_id(self) -> str:
        return self.document.inventory_id

    @property
    def index_key(self) -> str:
        return self.document.index_key


def _document_text(
    document: InventoryIndexDocument,
) -> str:
    return " ".join(
        (
            document.name,
            document.inventory_code,
            document.inventory_type,
            document.project_id,
            document.lifecycle,
            document.availability,
        )
    ).casefold()


@dataclass(frozen=True, slots=True)
class MatchingRecommendationPipeline:
    """
    Deterministic matching pipeline.

    Hard constraints eliminate candidates.
    Soft preferences score remaining candidates.

    The final ordering is deterministic by:
        score DESC
        index_key ASC
    """

    def _tenant_guard(
        self,
        profile: MatchingProfile,
        document: InventoryIndexDocument,
    ) -> None:
        if document.tenant_id != profile.tenant_id:
            raise MatchingTenantError(
                "Matching candidate belongs to another tenant."
            )

    def _evaluate(
        self,
        profile: MatchingProfile,
        document: InventoryIndexDocument,
    ) -> MatchRecommendation | None:
        self._tenant_guard(
            profile,
            document,
        )

        passed: list[str] = []
        matched: list[str] = []
        missed: list[str] = []
        excluded: list[str] = []

        inventory_type = InventoryType(
            document.inventory_type
        )

        availability = AvailabilityState(
            document.availability
        )

        # Hard constraint: inventory type.
        if profile.required_inventory_types:
            if (
                inventory_type
                not in profile.required_inventory_types
            ):
                excluded.append(
                    "required_inventory_type_mismatch"
                )
            else:
                passed.append(
                    "required_inventory_type"
                )

        # Hard constraint: project.
        if profile.required_project_ids:
            if (
                document.project_id
                not in profile.required_project_ids
            ):
                excluded.append(
                    "required_project_mismatch"
                )
            else:
                passed.append(
                    "required_project"
                )

        # Hard constraint: availability.
        if profile.required_availability:
            if (
                availability
                not in profile.required_availability
            ):
                excluded.append(
                    "required_availability_mismatch"
                )
            else:
                passed.append(
                    "required_availability"
                )

        # Hard constraint: excluded keywords.
        text = _document_text(document)

        for keyword in profile.excluded_keywords:
            if keyword.casefold() in text:
                excluded.append(
                    f"excluded_keyword:{keyword}"
                )

        if excluded:
            return None

        score = 0.0

        if profile.required_inventory_types:
            score += 1.0

        if profile.required_project_ids:
            score += 1.0

        if profile.required_availability:
            score += 1.0

        # Soft inventory-type preference.
        if profile.preferred_inventory_types:
            if (
                inventory_type
                in profile.preferred_inventory_types
            ):
                score += 2.0
                matched.append(
                    "preferred_inventory_type"
                )
            else:
                missed.append(
                    "preferred_inventory_type"
                )

        # Soft project preference.
        if profile.preferred_project_ids:
            if (
                document.project_id
                in profile.preferred_project_ids
            ):
                score += 2.0
                matched.append(
                    "preferred_project"
                )
            else:
                missed.append(
                    "preferred_project"
                )

        # Soft availability preference.
        if profile.preferred_availability:
            if (
                availability
                in profile.preferred_availability
            ):
                score += 2.0
                matched.append(
                    "preferred_availability"
                )
            else:
                missed.append(
                    "preferred_availability"
                )

        # Soft inventory-code preference.
        if profile.preferred_inventory_codes:
            if (
                document.inventory_code
                in profile.preferred_inventory_codes
            ):
                score += 3.0
                matched.append(
                    "preferred_inventory_code"
                )
            else:
                missed.append(
                    "preferred_inventory_code"
                )

        # Soft keyword preference.
        if profile.preferred_keywords:
            keyword_matches = [
                keyword
                for keyword
                in profile.preferred_keywords
                if keyword.casefold() in text
            ]

            if keyword_matches:
                score += (
                    1.0
                    * len(keyword_matches)
                )

                matched.append(
                    "preferred_keywords"
                )
            else:
                missed.append(
                    "preferred_keywords"
                )

        explanation = MatchExplanation(
            hard_constraints_passed=tuple(
                passed
            ),
            soft_preferences_matched=tuple(
                matched
            ),
            soft_preferences_missed=tuple(
                missed
            ),
            excluded_reasons=(),
        )

        return MatchRecommendation(
            document=document,
            score=score,
            explanation=explanation,
        )

    def match(
        self,
        profile: MatchingProfile,
        candidates: Iterable[
            InventoryIndexDocument
        ],
    ) -> tuple[MatchRecommendation, ...]:
        if not isinstance(
            profile,
            MatchingProfile,
        ):
            raise MatchingCriteriaError(
                "profile must be MatchingProfile."
            )

        if isinstance(
            candidates,
            (str, bytes),
        ):
            raise MatchingCandidateError(
                "candidates must be iterable."
            )

        materialized = list(candidates)

        seen: set[str] = set()
        results: list[
            MatchRecommendation
        ] = []

        for document in materialized:
            if not isinstance(
                document,
                InventoryIndexDocument,
            ):
                raise MatchingCandidateError(
                    "candidates must contain "
                    "InventoryIndexDocument values."
                )

            if document.index_key in seen:
                raise MatchingCandidateError(
                    "Duplicate candidate identity detected."
                )

            seen.add(
                document.index_key
            )

            result = self._evaluate(
                profile,
                document,
            )

            if result is not None:
                results.append(result)

        results.sort(
            key=lambda result: (
                -result.score,
                result.index_key.casefold(),
            )
        )

        return tuple(results)


__all__ = [
    "MatchingDomainError",
    "MatchingTenantError",
    "MatchingCriteriaError",
    "MatchingCandidateError",
    "MatchingProfile",
    "MatchExplanation",
    "MatchRecommendation",
    "MatchingRecommendationPipeline",
]
