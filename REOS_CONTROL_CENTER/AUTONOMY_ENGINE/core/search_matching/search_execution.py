"""
CORE-005 / Point 04 — Search Execution.

Owns:
- query execution boundary
- candidate acquisition boundary
- structured filtering
- deterministic sorting
- pagination
- empty-result handling
- invalid-query handling
- bounded query execution
- deterministic result assembly

This module does NOT own:
- Qdrant client behavior
- PostGIS
- lexical retrieval implementation
- vector retrieval implementation
- ranking policy
- matching policy
- authorization engine
- source-of-truth mutation
- Control Center state

Actual retrieval is injected through a candidate provider.

This avoids creating another retrieval/search engine.
Existing retrieval components such as hybrid_retrieval.py
remain runtime candidate providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Iterable, Protocol

from .search_domain import (
    SearchRequest,
    SearchResultItem,
    SearchResultPage,
    SearchSort,
    SearchSortDirection,
    SearchSortField,
)
from .search_filters import StructuredSearchFilter
from .search_index_contract import (
    InventoryIndexDocument,
)


class SearchExecutionError(ValueError):
    """Base CORE-005 search execution error."""


class SearchExecutionBoundsError(SearchExecutionError):
    """Raised when query execution exceeds configured bounds."""


class SearchExecutionCandidateError(SearchExecutionError):
    """Raised when a candidate violates the execution contract."""


class SearchExecutionQueryError(SearchExecutionError):
    """Raised when a query cannot be executed."""


@dataclass(frozen=True, slots=True)
class SearchExecutionConfig:
    """
    Search execution safety bounds.
    """

    max_candidates: int = 10_000
    max_page_size: int = 100
    max_query_length: int = 1_000

    def __post_init__(self) -> None:
        for field_name in (
            "max_candidates",
            "max_page_size",
            "max_query_length",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
            ):
                raise SearchExecutionError(
                    f"{field_name} must be a positive integer."
                )


@dataclass(frozen=True, slots=True)
class SearchExecutionCandidate:
    """
    Candidate supplied by an upstream retrieval boundary.

    score is an upstream retrieval/relevance signal only.
    This module never computes business relevance.
    """

    document: InventoryIndexDocument
    score: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.document,
            InventoryIndexDocument,
        ):
            raise SearchExecutionCandidateError(
                "document must be InventoryIndexDocument."
            )

        if self.score is not None:
            if isinstance(
                self.score,
                bool,
            ):
                raise SearchExecutionCandidateError(
                    "score must be numeric or None."
                )

            try:
                value = float(
                    self.score
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise SearchExecutionCandidateError(
                    "score must be numeric or None."
                ) from exc

            if not isfinite(value):
                raise SearchExecutionCandidateError(
                    "score must be finite."
                )

            object.__setattr__(
                self,
                "score",
                value,
            )


class SearchCandidateProvider(Protocol):
    """
    Retrieval adapter contract.

    A provider may internally use:
    - lexical retrieval
    - vector retrieval
    - hybrid retrieval
    - future backend adapters

    The Search Execution layer remains backend-independent.
    """

    def candidates(
        self,
        request: SearchRequest,
    ) -> Iterable[SearchExecutionCandidate]:
        ...


class CallableSearchCandidateProvider:
    """
    Adapter for a callable candidate source.

    Keeps the execution layer independent from the
    implementation of the retrieval system.
    """

    def __init__(
        self,
        callback: Callable[
            [SearchRequest],
            Iterable[SearchExecutionCandidate],
        ],
    ) -> None:
        if not callable(callback):
            raise SearchExecutionCandidateError(
                "callback must be callable."
            )

        self._callback = callback

    def candidates(
        self,
        request: SearchRequest,
    ) -> Iterable[SearchExecutionCandidate]:
        return self._callback(request)


def _document_sort_value(
    candidate: SearchExecutionCandidate,
    sort_field: SearchSortField,
):
    document = candidate.document

    if sort_field is SearchSortField.RELEVANCE:
        return (
            candidate.score
            if candidate.score is not None
            else float("-inf")
        )

    if sort_field is SearchSortField.INVENTORY_CODE:
        return document.inventory_code.casefold()

    if sort_field is SearchSortField.NAME:
        return document.name.casefold()

    if sort_field is SearchSortField.PROJECT_ID:
        return document.project_id.casefold()

    if sort_field is SearchSortField.INVENTORY_TYPE:
        return document.inventory_type.casefold()

    if sort_field is SearchSortField.LIFECYCLE:
        return document.lifecycle.casefold()

    if sort_field is SearchSortField.AVAILABILITY:
        return document.availability.casefold()

    if sort_field is SearchSortField.INVENTORY_VERSION:
        return document.inventory_version

    if sort_field is SearchSortField.INDEX_KEY:
        return document.index_key.casefold()

    raise SearchExecutionError(
        f"Unsupported sort field: {sort_field!r}."
    )


def _sort_candidates(
    candidates: list[
        SearchExecutionCandidate
    ],
    sorts: tuple[SearchSort, ...],
) -> None:
    """
    Stable multi-field deterministic sorting.

    A final index_key ASC tie-breaker is always applied.
    """
    effective_sorts = list(sorts)

    if not any(
        sort.field is SearchSortField.INDEX_KEY
        for sort in effective_sorts
    ):
        effective_sorts.append(
            SearchSort(
                field=SearchSortField.INDEX_KEY,
                direction=SearchSortDirection.ASC,
            )
        )

    for sort in reversed(effective_sorts):
        reverse = (
            sort.direction
            is SearchSortDirection.DESC
        )

        candidates.sort(
            key=lambda candidate: (
                _document_sort_value(
                    candidate,
                    sort.field,
                )
            ),
            reverse=reverse,
        )


def _apply_filter(
    candidates: Iterable[
        SearchExecutionCandidate
    ],
    search_filter: StructuredSearchFilter | None,
    tenant_id: str,
) -> list[SearchExecutionCandidate]:
    if search_filter is not None:
        search_filter_tenant = (
            search_filter.tenant_id
        )

        if search_filter_tenant != tenant_id:
            raise SearchExecutionCandidateError(
                "Search filter tenant does not match "
                "request tenant."
            )

    filtered: list[
        SearchExecutionCandidate
    ] = []

    for candidate in candidates:
        document = candidate.document

        # Tenant boundary is always first.
        if document.tenant_id != tenant_id:
            continue

        if (
            search_filter is not None
            and not search_filter.matches(
                document
            )
        ):
            continue

        filtered.append(candidate)

    return filtered


@dataclass(slots=True)
class SearchExecutionEngine:
    """
    Backend-independent search execution boundary.

    It assembles the request pipeline:

        candidate provider
            -> tenant boundary
            -> structured filters
            -> deterministic sorting
            -> bounded pagination
            -> SearchResultPage

    No new retrieval engine is created here.
    """

    provider: SearchCandidateProvider
    config: SearchExecutionConfig = SearchExecutionConfig()

    def __post_init__(self) -> None:
        if not hasattr(
            self.provider,
            "candidates",
        ):
            raise SearchExecutionCandidateError(
                "provider must implement candidates()."
            )

    def _validate_request(
        self,
        request: SearchRequest,
    ) -> None:
        if not isinstance(
            request,
            SearchRequest,
        ):
            raise SearchExecutionQueryError(
                "request must be SearchRequest."
            )

        if (
            len(request.query)
            > self.config.max_query_length
        ):
            raise SearchExecutionBoundsError(
                "Search query exceeds max_query_length."
            )

        if (
            request.pagination.page_size
            > self.config.max_page_size
        ):
            raise SearchExecutionBoundsError(
                "Requested page size exceeds execution bound."
            )

        if (
            request.filters is not None
            and request.filters.tenant_id
            != request.tenant.tenant_id
        ):
            raise SearchExecutionCandidateError(
                "Filter tenant does not match request tenant."
            )

        # A non-empty query needs an actual retrieval provider.
        # The provider is already mandatory at engine construction.
        if not isinstance(
            request.query,
            str,
        ):
            raise SearchExecutionQueryError(
                "Normalized query must be a string."
            )

    def _materialize_candidates(
        self,
        request: SearchRequest,
    ) -> list[SearchExecutionCandidate]:
        try:
            supplied = self.provider.candidates(
                request
            )
        except SearchExecutionError:
            raise
        except Exception as exc:
            raise SearchExecutionQueryError(
                "Candidate provider failed."
            ) from exc

        if supplied is None:
            raise SearchExecutionCandidateError(
                "Candidate provider returned None."
            )

        if isinstance(
            supplied,
            (str, bytes),
        ):
            raise SearchExecutionCandidateError(
                "Candidate provider must return candidates."
            )

        materialized = list(supplied)

        if (
            len(materialized)
            > self.config.max_candidates
        ):
            raise SearchExecutionBoundsError(
                "Candidate count exceeds max_candidates."
            )

        seen_keys: set[str] = set()
        normalized: list[
            SearchExecutionCandidate
        ] = []

        for candidate in materialized:
            if not isinstance(
                candidate,
                SearchExecutionCandidate,
            ):
                raise SearchExecutionCandidateError(
                    "Candidate provider returned an invalid "
                    "candidate object."
                )

            key = candidate.document.index_key

            if key in seen_keys:
                raise SearchExecutionCandidateError(
                    "Duplicate search candidate identity detected."
                )

            seen_keys.add(key)
            normalized.append(candidate)

        return normalized

    def execute(
        self,
        request: SearchRequest,
    ) -> SearchResultPage:
        """
        Execute one deterministic search request.

        Empty candidate sets are valid and return an empty page.
        """
        self._validate_request(request)

        candidates = self._materialize_candidates(
            request
        )

        filtered = _apply_filter(
            candidates,
            request.filters,
            request.tenant.tenant_id,
        )

        _sort_candidates(
            filtered,
            request.sorts,
        )

        total_hits = len(filtered)

        start = request.pagination.offset
        end = (
            start
            + request.pagination.limit
        )

        page_candidates = filtered[
            start:end
        ]

        items = tuple(
            SearchResultItem(
                document=candidate.document,
                position=index,
                score=candidate.score,
            )
            for index, candidate in enumerate(
                page_candidates,
                start=1,
            )
        )

        return SearchResultPage(
            request_identity=request.identity,
            items=items,
            total_hits=total_hits,
            page=request.pagination.page,
            page_size=request.pagination.page_size,
        )


__all__ = [
    "SearchExecutionError",
    "SearchExecutionBoundsError",
    "SearchExecutionCandidateError",
    "SearchExecutionQueryError",
    "SearchExecutionConfig",
    "SearchExecutionCandidate",
    "SearchCandidateProvider",
    "CallableSearchCandidateProvider",
    "SearchExecutionEngine",
]
