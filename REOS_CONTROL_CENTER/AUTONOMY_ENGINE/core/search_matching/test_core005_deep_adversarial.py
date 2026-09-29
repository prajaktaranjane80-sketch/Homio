"""
CORE-005 hardening — deep adversarial boundary regression.

Tests only. No production behavior is introduced here.
"""

from __future__ import annotations

import pytest

from .search_consistency import (
    ConsistencyEvent,
    ConsistencyStatus,
    SearchConsistencyTracker,
)
from .search_domain import (
    SearchPagination,
    SearchRequest,
    SearchTenantContext,
)
from .search_filters import StructuredSearchFilter
from .search_index_contract import (
    EXPECTED_INDEX_FINGERPRINT,
    InventoryIndexDocument,
    SearchIndexOperation,
)
from .search_security import (
    SearchAbuseBoundaryError,
    SearchAuthorizationContext,
    SearchDataLeakageError,
    SearchSecurityBoundary,
    SearchSecurityError,
    SearchSecurityPolicy,
    SearchTenantIsolationError,
    SecurityDecision,
)


def make_document(
    *,
    tenant_id: str = "tenant-a",
    index_key: str = "tenant-a:inv-001",
    version: int = 1,
    payload: dict[str, object] | None = None,
) -> InventoryIndexDocument:
    return InventoryIndexDocument(
        tenant_id=tenant_id,
        project_id="project-001",
        inventory_id=index_key,
        inventory_code="UNIT-001",
        inventory_type="UNIT",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
        name="Premium Apartment",
        inventory_version=version,
        index_key=index_key,
        operation=SearchIndexOperation.UPSERT,
        payload=payload or {},
    )


def test_request_tenant_mismatch_denies_before_authorization() -> None:
    boundary = SearchSecurityBoundary()

    request = SearchRequest(
        tenant=SearchTenantContext(
            tenant_id="tenant-a"
        ),
        filters=StructuredSearchFilter(
            tenant_id="tenant-a"
        ),
        pagination=SearchPagination(
            page=1,
            page_size=20,
        ),
    )

    decision = boundary.validate_request(
        request,
        SearchAuthorizationContext(
            tenant_id="tenant-b"
        ),
    )

    assert decision.decision is SecurityDecision.DENY


def test_cross_tenant_result_fails_closed() -> None:
    boundary = SearchSecurityBoundary()
    context = SearchAuthorizationContext(
        tenant_id="tenant-a"
    )

    with pytest.raises(SearchTenantIsolationError):
        boundary.enforce_tenant_result_boundary(
            context,
            (
                make_document(
                    tenant_id="tenant-b",
                    index_key="tenant-b:inv-001",
                ),
            ),
        )


def test_idor_duplicate_result_identity_is_blocked() -> None:
    boundary = SearchSecurityBoundary()
    context = SearchAuthorizationContext(
        tenant_id="tenant-a"
    )

    duplicate = make_document(
        index_key="tenant-a:inv-001"
    )

    with pytest.raises(SearchSecurityError):
        boundary.enforce_tenant_result_boundary(
            context,
            (duplicate, duplicate),
        )


def test_malformed_result_object_fails_closed() -> None:
    boundary = SearchSecurityBoundary()
    context = SearchAuthorizationContext(
        tenant_id="tenant-a"
    )

    with pytest.raises(SearchDataLeakageError):
        boundary.enforce_tenant_result_boundary(
            context,
            (object(),),  # type: ignore[arg-type]
        )


def test_candidate_count_abuse_boundary_is_enforced() -> None:
    boundary = SearchSecurityBoundary(
        policy=SearchSecurityPolicy(
            max_candidate_count=1
        )
    )

    context = SearchAuthorizationContext(
        tenant_id="tenant-a"
    )

    with pytest.raises(SearchAbuseBoundaryError):
        boundary.enforce_tenant_result_boundary(
            context,
            (
                make_document(
                    index_key="tenant-a:inv-001"
                ),
                make_document(
                    index_key="tenant-a:inv-002"
                ),
            ),
        )


def test_sensitive_payload_sanitization_does_not_mutate_source() -> None:
    original = make_document(
        payload={
            "public_label": "Premium",
            "private_key": "SECRET",
        }
    )

    boundary = SearchSecurityBoundary(
        policy=SearchSecurityPolicy(
            blocked_payload_fields=frozenset(
                {"private_key"}
            )
        )
    )

    result = boundary.enforce_tenant_result_boundary(
        SearchAuthorizationContext(
            tenant_id="tenant-a"
        ),
        (original,),
    )

    assert "private_key" in original.payload
    assert "private_key" not in result[0].payload
    assert result[0].tenant_id == "tenant-a"


def test_search_index_document_is_immutable_at_boundary() -> None:
    document = make_document()

    with pytest.raises(AttributeError):
        document.tenant_id = "tenant-b"  # type: ignore[misc]

    with pytest.raises(TypeError):
        document.payload["x"] = "y"  # type: ignore[index]


def test_consistency_detects_future_then_stale_event_without_reordering_state() -> None:
    tracker = SearchConsistencyTracker()

    first = ConsistencyEvent(
        event_id="event-001",
        tenant_id="tenant-a",
        index_key="inv-001",
        source_version=3,
    )

    older = ConsistencyEvent(
        event_id="event-000",
        tenant_id="tenant-a",
        index_key="inv-001",
        source_version=2,
    )

    assert (
        tracker.observe_event(first)
        is ConsistencyStatus.CURRENT
    )

    assert (
        tracker.observe_event(older)
        is ConsistencyStatus.OUT_OF_ORDER
    )

    state = tracker.state(
        tenant_id="tenant-a",
        index_key="inv-001",
    )

    assert state is not None
    assert state.source_version == 3
    assert state.projection_version == 3


def test_consistency_ordered_application_is_permutation_stable() -> None:
    events = (
        ConsistencyEvent(
            event_id="event-c",
            tenant_id="tenant-a",
            index_key="inv-002",
            source_version=2,
        ),
        ConsistencyEvent(
            event_id="event-a",
            tenant_id="tenant-a",
            index_key="inv-001",
            source_version=1,
        ),
        ConsistencyEvent(
            event_id="event-b",
            tenant_id="tenant-a",
            index_key="inv-001",
            source_version=2,
        ),
    )

    first = SearchConsistencyTracker()
    second = SearchConsistencyTracker()

    first_statuses = first.apply_ordered_events(
        events
    )

    second_statuses = second.apply_ordered_events(
        tuple(reversed(events))
    )

    assert first_statuses == second_statuses
    assert first.snapshot() == second.snapshot()


def test_index_contract_fingerprint_survives_round_trip() -> None:
    document = make_document()

    reconstructed = InventoryIndexDocument(
        tenant_id=document.tenant_id,
        project_id=document.project_id,
        inventory_id=document.inventory_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        lifecycle=document.lifecycle,
        availability=document.availability,
        name=document.name,
        inventory_version=document.inventory_version,
        index_key=document.index_key,
        schema_version=document.schema_version,
        index_version=document.index_version,
        index_fingerprint=document.index_fingerprint,
        operation=document.operation,
        payload=dict(document.payload),
    )

    assert reconstructed.to_dict() == document.to_dict()
    assert (
        reconstructed.index_fingerprint
        == EXPECTED_INDEX_FINGERPRINT
    )
