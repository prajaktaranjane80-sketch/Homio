"""
CORE-005 / Point 01 — Adversarial Search Domain tests.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from .search_domain import (
    SearchPagination,
    SearchRequest,
    SearchSort,
    SearchSortDirection,
    SearchSortField,
    SearchTenantContext,
)

from .search_filters import StructuredSearchFilter


def test_search_request_does_not_accept_cross_tenant_filter() -> None:
    request_tenant = SearchTenantContext(
        tenant_id="tenant-a"
    )

    foreign_filter = StructuredSearchFilter(
        tenant_id="tenant-b"
    )

    with pytest.raises(Exception):
        SearchRequest(
            tenant=request_tenant,
            filters=foreign_filter,
        )


def test_search_request_sort_order_is_not_silently_duplicated() -> None:
    with pytest.raises(Exception):
        SearchRequest(
            tenant=SearchTenantContext(
                tenant_id="tenant-a"
            ),
            sorts=(
                SearchSort(
                    field=SearchSortField.PROJECT_ID
                ),
                SearchSort(
                    field=SearchSortField.PROJECT_ID,
                    direction=SearchSortDirection.DESC,
                ),
            ),
        )


def test_pagination_never_accepts_zero_page() -> None:
    with pytest.raises(Exception):
        SearchPagination(page=0)


def test_pagination_never_accepts_zero_page_size() -> None:
    with pytest.raises(Exception):
        SearchPagination(page_size=0)


def test_identity_does_not_change_from_whitespace() -> None:
    context = SearchTenantContext(
        tenant_id="tenant-a"
    )

    first = SearchRequest(
        tenant=context,
        query="  luxury   homes ",
    )

    second = SearchRequest(
        tenant=context,
        query="luxury homes",
    )

    assert first.identity == second.identity


def test_tenant_is_part_of_search_identity() -> None:
    first = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        ),
        query="luxury homes",
    )

    second = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-b"
        ),
        query="luxury homes",
    )

    assert first.identity != second.identity


def test_search_request_is_frozen() -> None:
    request = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        ),
        query="homes",
    )

    with pytest.raises(
        (FrozenInstanceError, AttributeError)
    ):
        request.query = "changed"  # type: ignore[misc]
