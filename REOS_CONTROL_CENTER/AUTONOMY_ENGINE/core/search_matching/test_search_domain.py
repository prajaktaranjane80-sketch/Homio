"""
CORE-005 / Point 01 — Search Domain tests.
"""

from __future__ import annotations

import pytest

from .search_domain import (
    SearchIdentity,
    SearchPagination,
    SearchPaginationError,
    SearchQueryError,
    SearchRequest,
    SearchResultItem,
    SearchResultPage,
    SearchResultError,
    SearchSort,
    SearchSortDirection,
    SearchSortError,
    SearchSortField,
    SearchTenantContext,
    SearchTenantContextError,
    normalize_search_query,
)

from .search_filters import StructuredSearchFilter
from .search_index_contract import (
    InventoryIndexDocument,
    SearchIndexOperation,
)


def make_document(
    tenant_id: str = "tenant-a",
    index_key: str = "inventory-001",
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id="project-001",
        inventory_id=index_key,
        inventory_code=index_key,
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
        name="Premium Apartment",
        inventory_version=1,
        index_key=index_key,
        operation=SearchIndexOperation.UPSERT,
    )


def test_query_normalization_is_deterministic() -> None:
    assert (
        normalize_search_query(
            "  Premium   APARTMENT  "
        )
        == "premium apartment"
    )


def test_none_query_becomes_empty_string() -> None:
    assert normalize_search_query(None) == ""


def test_invalid_query_type_is_rejected() -> None:
    with pytest.raises(SearchQueryError):
        normalize_search_query(123)  # type: ignore[arg-type]


def test_tenant_context_requires_tenant() -> None:
    with pytest.raises(SearchTenantContextError):
        SearchTenantContext(tenant_id="   ")


def test_tenant_context_normalizes_roles_and_capabilities() -> None:
    context = SearchTenantContext(
        tenant_id="tenant-a",
        actor_id="agent-001",
        roles=("Broker", "broker", "Admin"),
        capabilities=(
            "search:read",
            "search:read",
        ),
    )

    assert context.roles == ("Admin", "Broker", "broker")
    assert context.capabilities == ("search:read",)


def test_tenant_context_rejects_cross_tenant() -> None:
    context = SearchTenantContext(
        tenant_id="tenant-a"
    )

    with pytest.raises(SearchTenantContextError):
        context.assert_tenant("tenant-b")


def test_sort_contract_is_canonical() -> None:
    sort = SearchSort(
        field=SearchSortField.NAME,
        direction=SearchSortDirection.DESC,
    )

    assert sort.to_dict() == {
        "field": "name",
        "direction": "desc",
    }


def test_duplicate_sort_fields_are_rejected() -> None:
    with pytest.raises(SearchSortError):
        SearchRequest(
            tenant=SearchTenantContext("tenant-a"),
            sorts=(
                SearchSort(SearchSortField.NAME),
                SearchSort(SearchSortField.NAME),
            ),
        )


def test_pagination_is_bounded() -> None:
    page = SearchPagination(
        page=3,
        page_size=25,
        max_page_size=100,
    )

    assert page.offset == 50
    assert page.limit == 25


def test_pagination_rejects_unbounded_page() -> None:
    with pytest.raises(SearchPaginationError):
        SearchPagination(
            page_size=101,
            max_page_size=100,
        )


def test_filter_tenant_must_match_request_tenant() -> None:
    search_filter = StructuredSearchFilter(
        tenant_id="tenant-b"
    )

    with pytest.raises(SearchTenantContextError):
        SearchRequest(
            tenant=SearchTenantContext("tenant-a"),
            filters=search_filter,
        )


def test_search_identity_is_deterministic() -> None:
    context = SearchTenantContext("tenant-a")

    request_a = SearchRequest(
        tenant=context,
        query="  Premium   Apartment ",
        sorts=(
            SearchSort(
                SearchSortField.NAME,
                SearchSortDirection.ASC,
            ),
        ),
        pagination=SearchPagination(
            page=1,
            page_size=20,
        ),
    )

    request_b = SearchRequest(
        tenant=context,
        query="premium apartment",
        sorts=(
            SearchSort(
                SearchSortField.NAME,
                SearchSortDirection.ASC,
            ),
        ),
        pagination=SearchPagination(
            page=1,
            page_size=20,
        ),
    )

    assert request_a.identity == request_b.identity
    assert len(request_a.identity.value) == 64
    assert isinstance(
        request_a.identity,
        SearchIdentity,
    )


def test_search_identity_changes_when_query_changes() -> None:
    context = SearchTenantContext("tenant-a")

    request_a = SearchRequest(
        tenant=context,
        query="villa",
    )

    request_b = SearchRequest(
        tenant=context,
        query="apartment",
    )

    assert request_a.identity != request_b.identity


def test_search_identity_contains_explicit_tie_breaker() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext("tenant-a"),
        sorts=(
            SearchSort(
                SearchSortField.NAME,
                SearchSortDirection.ASC,
            ),
        ),
    )

    payload = request.to_identity_payload()

    assert payload["sorts"][-1] == {
        "field": "index_key",
        "direction": "asc",
    }


def test_result_item_accepts_derived_index_document() -> None:
    item = SearchResultItem(
        document=make_document(),
        position=1,
        score=0.95,
    )

    assert item.position == 1
    assert item.score == 0.95
    assert item.document.tenant_id == "tenant-a"


def test_result_page_is_deterministic() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext("tenant-a")
    )

    item = SearchResultItem(
        document=make_document(),
        position=1,
    )

    page = SearchResultPage(
        request_identity=request.identity,
        items=(item,),
        total_hits=2,
        page=1,
        page_size=1,
    )

    assert page.has_next is True
    assert page.items[0].position == 1


def test_result_page_rejects_invalid_positions() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext("tenant-a")
    )

    item = SearchResultItem(
        document=make_document(),
        position=2,
    )

    with pytest.raises(SearchResultError):
        SearchResultPage(
            request_identity=request.identity,
            items=(item,),
            total_hits=1,
            page=1,
            page_size=10,
        )


def test_result_page_rejects_results_above_page_size() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext("tenant-a")
    )

    item_a = SearchResultItem(
        document=make_document(index_key="inventory-001"),
        position=1,
    )

    item_b = SearchResultItem(
        document=make_document(index_key="inventory-002"),
        position=2,
    )

    with pytest.raises(SearchResultError):
        SearchResultPage(
            request_identity=request.identity,
            items=(item_a, item_b),
            total_hits=2,
            page=1,
            page_size=1,
        )


def test_search_result_contract_is_immutable() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext("tenant-a")
    )

    item = SearchResultItem(
        document=make_document(),
        position=1,
    )

    page = SearchResultPage(
        request_identity=request.identity,
        items=(item,),
        total_hits=1,
        page=1,
        page_size=10,
    )

    with pytest.raises(AttributeError):
        page.page = 2  # type: ignore[misc]
