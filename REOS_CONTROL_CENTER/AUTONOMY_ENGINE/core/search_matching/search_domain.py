"""
CORE-005 / Point 01 Ã¢â‚¬â€ Search Domain.

Owns the stable domain contract for a search request and result.

This module does NOT:
- execute searches
- call Qdrant
- call PostGIS
- rank candidates
- perform matching
- enforce commercial/business authorization
- mutate CORE-004 Inventory
- mutate REOS Control Center state

It defines:
- tenant context
- query normalization
- search identity
- filter contract composition
- sort contract
- pagination contract
- result contract

Runtime execution belongs to later CORE-005 boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping

from .search_filters import StructuredSearchFilter
from .search_index_contract import InventoryIndexDocument


class SearchDomainError(ValueError):
    """Base CORE-005 Search Domain error."""


class SearchTenantContextError(SearchDomainError):
    """Raised when tenant execution context is invalid."""


class SearchQueryError(SearchDomainError):
    """Raised when a search query is invalid."""


class SearchSortError(SearchDomainError):
    """Raised when a search sort contract is invalid."""


class SearchPaginationError(SearchDomainError):
    """Raised when a pagination contract is invalid."""


class SearchResultError(SearchDomainError):
    """Raised when a search result contract is invalid."""


class SearchSortField(str, Enum):
    """
    Domain-level sortable fields.

    RELEVANCE is a contract only.
    This module does not calculate relevance.
    """

    RELEVANCE = "relevance"
    INVENTORY_CODE = "inventory_code"
    NAME = "name"
    PROJECT_ID = "project_id"
    INVENTORY_TYPE = "inventory_type"
    LIFECYCLE = "lifecycle"
    AVAILABILITY = "availability"
    INVENTORY_VERSION = "inventory_version"
    INDEX_KEY = "index_key"


class SearchSortDirection(str, Enum):
    """Deterministic sort direction."""

    ASC = "asc"
    DESC = "desc"


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise SearchDomainError(
            f"{field_name} must be a string."
        )

    value = value.strip()

    if not value:
        raise SearchDomainError(
            f"{field_name} cannot be empty."
        )

    return value


def _normalize_sequence(
    values: tuple[str, ...] | list[str] | None,
    field_name: str,
) -> tuple[str, ...]:
    if values is None:
        return ()

    if isinstance(values, (str, bytes)):
        raise SearchDomainError(
            f"{field_name} must be a sequence of strings."
        )

    try:
        iterator = iter(values)
    except TypeError as exc:
        raise SearchDomainError(
            f"{field_name} must be iterable."
        ) from exc

    normalized: list[str] = []

    for value in iterator:
        normalized.append(
            _required_text(value, field_name)
        )

    return tuple(
        sorted(
            set(normalized),
            key=lambda value: (
                value.casefold(),
                value.islower(),
                value,
            ),
        )
    )


def normalize_search_query(query: str | None) -> str:
    """
    Normalize user query deterministically.

    Rules:
    - None becomes empty query.
    - Unicode whitespace is normalized to spaces.
    - repeated whitespace collapses.
    - surrounding whitespace is removed.
    - case is normalized using casefold().
    """
    if query is None:
        return ""

    if not isinstance(query, str):
        raise SearchQueryError(
            "query must be a string or None."
        )

    normalized = " ".join(
        query.strip().split()
    )

    return normalized.casefold()


def _freeze_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise SearchDomainError(
            "mapping value must be a mapping."
        )

    frozen: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            raise SearchDomainError(
                "mapping keys must be strings."
            )

        frozen[key] = item

    return MappingProxyType(frozen)


@dataclass(frozen=True, slots=True)
class SearchTenantContext:
    """
    Minimal tenant execution context.

    Tenant ID is mandatory.
    Identity and permission decisions remain outside this contract.
    """

    tenant_id: str
    actor_id: str | None = None
    roles: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        try:
            tenant_id = _required_text(
                self.tenant_id,
                "tenant_id",
            )
        except SearchDomainError as exc:
            raise SearchTenantContextError(
                str(exc)
            ) from exc

        object.__setattr__(
            self,
            "tenant_id",
            tenant_id,
        )

        if self.actor_id is not None:
            object.__setattr__(
                self,
                "actor_id",
                _required_text(
                    self.actor_id,
                    "actor_id",
                ),
            )

        object.__setattr__(
            self,
            "roles",
            _normalize_sequence(
                self.roles,
                "roles",
            ),
        )

        object.__setattr__(
            self,
            "capabilities",
            _normalize_sequence(
                self.capabilities,
                "capabilities",
            ),
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _required_text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise SearchTenantContextError(
                "Search tenant context mismatch."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "roles": list(self.roles),
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True, slots=True)
class SearchSort:
    """
    Immutable search sorting contract.

    A deterministic final index-key tie breaker is always added by
    the search-domain canonical representation.
    """

    field: SearchSortField
    direction: SearchSortDirection = (
        SearchSortDirection.ASC
    )

    def __post_init__(self) -> None:
        try:
            object.__setattr__(
                self,
                "field",
                SearchSortField(self.field),
            )
            object.__setattr__(
                self,
                "direction",
                SearchSortDirection(self.direction),
            )
        except (TypeError, ValueError) as exc:
            raise SearchSortError(
                "Invalid search sort contract."
            ) from exc

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field.value,
            "direction": self.direction.value,
        }


@dataclass(frozen=True, slots=True)
class SearchPagination:
    """
    Bounded page-based pagination contract.

    The domain does not execute pagination.
    It only validates and canonicalizes the request.
    """

    page: int = 1
    page_size: int = 20
    max_page_size: int = 100

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_page_size, bool)
            or not isinstance(self.max_page_size, int)
            or self.max_page_size < 1
        ):
            raise SearchPaginationError(
                "max_page_size must be a positive integer."
            )

        if (
            isinstance(self.page, bool)
            or not isinstance(self.page, int)
            or self.page < 1
        ):
            raise SearchPaginationError(
                "page must be a positive integer."
            )

        if (
            isinstance(self.page_size, bool)
            or not isinstance(self.page_size, int)
            or self.page_size < 1
        ):
            raise SearchPaginationError(
                "page_size must be a positive integer."
            )

        if self.page_size > self.max_page_size:
            raise SearchPaginationError(
                "page_size exceeds max_page_size."
            )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size

    def to_dict(self) -> dict[str, int]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "max_page_size": self.max_page_size,
        }


def _filter_to_dict(
    search_filter: StructuredSearchFilter,
) -> dict[str, Any]:
    return {
        "tenant_id": search_filter.tenant_id,
        "project_ids": list(
            search_filter.project_ids
        ),
        "inventory_codes": list(
            search_filter.inventory_codes
        ),
        "inventory_types": [
            item.value
            for item in search_filter.inventory_types
        ],
        "lifecycle_states": [
            item.value
            for item in search_filter.lifecycle_states
        ],
        "availability_states": [
            item.value
            for item in search_filter.availability_states
        ],
        "name_contains": search_filter.name_contains,
    }


@dataclass(frozen=True, slots=True)
class SearchRequest:
    """
    Canonical Search Domain request.

    The tenant context and structured filter must agree on tenant.
    """

    tenant: SearchTenantContext
    query: str = ""
    filters: StructuredSearchFilter | None = None
    sorts: tuple[SearchSort, ...] = ()
    pagination: SearchPagination = field(
        default_factory=SearchPagination
    )
    attributes: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        normalized_query = normalize_search_query(
            self.query
        )
        object.__setattr__(
            self,
            "query",
            normalized_query,
        )

        if not isinstance(
            self.tenant,
            SearchTenantContext,
        ):
            raise SearchTenantContextError(
                "tenant must be SearchTenantContext."
            )

        if self.filters is not None:
            if not isinstance(
                self.filters,
                StructuredSearchFilter,
            ):
                raise SearchDomainError(
                    "filters must be StructuredSearchFilter."
                )

            self.tenant.assert_tenant(
                self.filters.tenant_id
            )

        normalized_sorts: list[SearchSort] = []

        if isinstance(self.sorts, (str, bytes)):
            raise SearchSortError(
                "sorts must be iterable."
            )

        try:
            iterator = iter(self.sorts)
        except TypeError as exc:
            raise SearchSortError(
                "sorts must be iterable."
            ) from exc

        for sort in iterator:
            if not isinstance(sort, SearchSort):
                raise SearchSortError(
                    "sorts must contain SearchSort values."
                )

            normalized_sorts.append(sort)

        # Prevent duplicated sort fields from creating ambiguous ordering.
        seen_fields: set[SearchSortField] = set()
        canonical_sorts: list[SearchSort] = []

        for sort in normalized_sorts:
            if sort.field in seen_fields:
                raise SearchSortError(
                    f"Duplicate sort field: {sort.field.value}."
                )

            seen_fields.add(sort.field)
            canonical_sorts.append(sort)

        object.__setattr__(
            self,
            "sorts",
            tuple(canonical_sorts),
        )

        if not isinstance(
            self.pagination,
            SearchPagination,
        ):
            raise SearchPaginationError(
                "pagination must be SearchPagination."
            )

        object.__setattr__(
            self,
            "attributes",
            _freeze_mapping(self.attributes),
        )

    def to_identity_payload(self) -> dict[str, Any]:
        """
        Canonical representation used for deterministic identity.
        """
        sorts = [
            sort.to_dict()
            for sort in self.sorts
        ]

        # Always make final deterministic tie-breaking explicit.
        if not any(
            sort.field is SearchSortField.INDEX_KEY
            for sort in self.sorts
        ):
            sorts.append(
                SearchSort(
                    field=SearchSortField.INDEX_KEY,
                    direction=SearchSortDirection.ASC,
                ).to_dict()
            )

        return {
            "tenant_id": self.tenant.tenant_id,
            "query": self.query,
            "filters": (
                _filter_to_dict(self.filters)
                if self.filters is not None
                else None
            ),
            "sorts": sorts,
            "pagination": self.pagination.to_dict(),
            "attributes": dict(self.attributes),
        }

    @property
    def identity(self) -> "SearchIdentity":
        return SearchIdentity.from_request(self)


@dataclass(frozen=True, slots=True)
class SearchIdentity:
    """
    Stable deterministic identity of a canonical search request.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise SearchDomainError(
                "Search identity must be a string."
            )

        if not re.fullmatch(
            r"[0-9a-f]{64}",
            self.value,
        ):
            raise SearchDomainError(
                "Search identity must be a SHA-256 hex digest."
            )

    @classmethod
    def from_request(
        cls,
        request: SearchRequest,
    ) -> "SearchIdentity":
        payload = request.to_identity_payload()

        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return cls(value=digest)


@dataclass(frozen=True, slots=True)
class SearchResultItem:
    """
    One immutable result contract.

    The document remains a derived projection.
    No ranking authority is embedded here.
    """

    document: InventoryIndexDocument
    position: int
    score: float | None = None
    highlights: Mapping[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.document,
            InventoryIndexDocument,
        ):
            raise SearchResultError(
                "document must be InventoryIndexDocument."
            )

        if (
            isinstance(self.position, bool)
            or not isinstance(self.position, int)
            or self.position < 1
        ):
            raise SearchResultError(
                "position must be a positive integer."
            )

        if self.score is not None:
            if isinstance(self.score, bool) or not isinstance(
                self.score,
                (int, float),
            ):
                raise SearchResultError(
                    "score must be numeric or None."
                )

        if not isinstance(
            self.highlights,
            Mapping,
        ):
            raise SearchResultError(
                "highlights must be a mapping."
            )

        normalized: dict[str, str] = {}

        for key, value in self.highlights.items():
            if not isinstance(key, str):
                raise SearchResultError(
                    "highlight keys must be strings."
                )

            if not isinstance(value, str):
                raise SearchResultError(
                    "highlight values must be strings."
                )

            normalized[key] = value

        object.__setattr__(
            self,
            "highlights",
            MappingProxyType(normalized),
        )


@dataclass(frozen=True, slots=True)
class SearchResultPage:
    """
    Immutable paginated search result contract.
    """

    request_identity: SearchIdentity
    items: tuple[SearchResultItem, ...]
    total_hits: int
    page: int
    page_size: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.request_identity,
            SearchIdentity,
        ):
            raise SearchResultError(
                "request_identity must be SearchIdentity."
            )

        if (
            isinstance(self.total_hits, bool)
            or not isinstance(self.total_hits, int)
            or self.total_hits < 0
        ):
            raise SearchResultError(
                "total_hits must be a non-negative integer."
            )

        if (
            isinstance(self.page, bool)
            or not isinstance(self.page, int)
            or self.page < 1
        ):
            raise SearchResultError(
                "page must be a positive integer."
            )

        if (
            isinstance(self.page_size, bool)
            or not isinstance(self.page_size, int)
            or self.page_size < 1
        ):
            raise SearchResultError(
                "page_size must be a positive integer."
            )

        normalized_items: list[SearchResultItem] = []

        for item in self.items:
            if not isinstance(
                item,
                SearchResultItem,
            ):
                raise SearchResultError(
                    "items must contain SearchResultItem values."
                )

            normalized_items.append(item)

        positions = [
            item.position
            for item in normalized_items
        ]

        if positions != list(
            range(1, len(positions) + 1)
        ):
            raise SearchResultError(
                "result positions must be contiguous "
                "and 1-based."
            )

        if len(normalized_items) > self.page_size:
            raise SearchResultError(
                "result item count exceeds page_size."
            )

        if (
            self.total_hits == 0
            and normalized_items
        ):
            raise SearchResultError(
                "zero total_hits cannot contain results."
            )

        object.__setattr__(
            self,
            "items",
            tuple(normalized_items),
        )

    @property
    def has_next(self) -> bool:
        consumed = (
            (self.page - 1) * self.page_size
            + len(self.items)
        )

        return consumed < self.total_hits

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_identity": self.request_identity.value,
            "items": [
                {
                    "position": item.position,
                    "score": item.score,
                    "document": item.document.to_dict(),
                    "highlights": dict(
                        item.highlights
                    ),
                }
                for item in self.items
            ],
            "total_hits": self.total_hits,
            "page": self.page,
            "page_size": self.page_size,
            "has_next": self.has_next,
        }


__all__ = [
    "SearchDomainError",
    "SearchTenantContextError",
    "SearchQueryError",
    "SearchSortError",
    "SearchPaginationError",
    "SearchResultError",
    "SearchSortField",
    "SearchSortDirection",
    "normalize_search_query",
    "SearchTenantContext",
    "SearchSort",
    "SearchPagination",
    "SearchRequest",
    "SearchIdentity",
    "SearchResultItem",
    "SearchResultPage",
]
