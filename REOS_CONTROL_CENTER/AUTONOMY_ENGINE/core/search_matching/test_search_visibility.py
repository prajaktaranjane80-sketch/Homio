from __future__ import annotations

from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import (
    HybridSearchResult,
)
from AUTONOMY_ENGINE.core.search_matching.search_visibility import (
    SearchVisibilityPolicy,
    TenantScopeError,
    TenantVisibilityFilter,
    VisibilityPolicyError,
    VisibilityReason,
)


def make_result(
    *,
    tenant_id: str,
    lifecycle: str = "ACTIVE",
    availability: str = "AVAILABLE",
    inventory_type: str = "UNIT",
    index_key: str = "tenant-a:inventory-a",
) -> HybridSearchResult:
    document = SimpleNamespace(
        tenant_id=tenant_id,
        lifecycle=lifecycle,
        availability=availability,
        inventory_type=inventory_type,
        index_key=index_key,
        inventory_id="inventory-a",
        inventory_code="UNIT-001",
        name="Test Unit",
    )

    return HybridSearchResult(
        document=document,
        rrf_score=0.5,
        lexical_rank=1,
        vector_rank=1,
        lexical_score=1.0,
        vector_score=1.0,
    )


def test_same_tenant_active_available_is_visible() -> None:
    result = make_result(
        tenant_id="tenant-a"
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        result
    )

    assert decision.allowed
    assert decision.reason == (
        VisibilityReason.ALLOWED
    )


def test_cross_tenant_result_is_blocked() -> None:
    result = make_result(
        tenant_id="tenant-b"
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        result
    )

    assert not decision.allowed
    assert not decision.tenant_allowed
    assert decision.reason == (
        VisibilityReason.TENANT_MISMATCH
    )


@pytest.mark.parametrize(
    "lifecycle",
    [
        "DRAFT",
        "SUSPENDED",
        "ARCHIVED",
    ],
)
def test_non_visible_lifecycle_is_blocked(
    lifecycle: str,
) -> None:
    result = make_result(
        tenant_id="tenant-a",
        lifecycle=lifecycle,
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        result
    )

    assert not decision.allowed
    assert decision.reason == (
        VisibilityReason.LIFECYCLE_BLOCKED
    )


@pytest.mark.parametrize(
    "availability",
    [
        "BLOCKED",
        "ALLOCATED",
        "SOLD",
        "UNAVAILABLE",
    ],
)
def test_blocked_availability_is_not_exposed(
    availability: str,
) -> None:
    result = make_result(
        tenant_id="tenant-a",
        availability=availability,
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        result
    )

    assert not decision.allowed
    assert decision.reason == (
        VisibilityReason.AVAILABILITY_BLOCKED
    )


def test_reserved_remains_visible_by_default() -> None:
    result = make_result(
        tenant_id="tenant-a",
        availability="RESERVED",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    assert boundary.is_visible(
        result
    )


def test_apply_preserves_existing_order() -> None:
    results = (
        make_result(
            tenant_id="tenant-a",
            index_key="a",
        ),
        make_result(
            tenant_id="tenant-b",
            index_key="b",
        ),
        make_result(
            tenant_id="tenant-a",
            index_key="c",
            availability="RESERVED",
        ),
        make_result(
            tenant_id="tenant-a",
            index_key="d",
            availability="SOLD",
        ),
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    visible = boundary.apply(
        results
    )

    assert [
        item.document.index_key
        for item in visible
    ] == [
        "a",
        "c",
    ]


def test_visibility_does_not_rank() -> None:
    results = (
        make_result(
            tenant_id="tenant-a",
            index_key="z",
        ),
        make_result(
            tenant_id="tenant-a",
            index_key="a",
        ),
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    visible = boundary.apply(
        results
    )

    assert [
        item.document.index_key
        for item in visible
    ] == [
        "z",
        "a",
    ]


def test_empty_results_are_safe() -> None:
    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    assert boundary.apply(
        ()
    ) == ()


def test_empty_tenant_is_rejected() -> None:
    with pytest.raises(
        TenantScopeError
    ):
        TenantVisibilityFilter(
            tenant_id="   "
        )


def test_non_string_tenant_is_rejected() -> None:
    with pytest.raises(
        TenantScopeError
    ):
        TenantVisibilityFilter(
            tenant_id=123  # type: ignore[arg-type]
        )


def test_custom_lifecycle_policy() -> None:
    policy = SearchVisibilityPolicy(
        visible_lifecycles=frozenset(
            {
                "ACTIVE",
                "SUSPENDED",
            }
        )
    )

    result = make_result(
        tenant_id="tenant-a",
        lifecycle="SUSPENDED",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a",
        policy=policy,
    )

    assert boundary.is_visible(
        result
    )


def test_custom_availability_policy() -> None:
    policy = SearchVisibilityPolicy(
        blocked_availability=frozenset(
            {
                "UNAVAILABLE",
                "RESERVED",
            }
        )
    )

    result = make_result(
        tenant_id="tenant-a",
        availability="RESERVED",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a",
        policy=policy,
    )

    assert not boundary.is_visible(
        result
    )


def test_custom_inventory_type_policy() -> None:
    policy = SearchVisibilityPolicy(
        blocked_inventory_types=frozenset(
            {
                "LAND",
            }
        )
    )

    result = make_result(
        tenant_id="tenant-a",
        inventory_type="LAND",
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a",
        policy=policy,
    )

    assert not boundary.is_visible(
        result
    )


def test_policy_normalizes_values() -> None:
    policy = SearchVisibilityPolicy(
        visible_lifecycles=frozenset(
            {" active "}
        ),
        blocked_availability=frozenset(
            {" unavailable "}
        ),
    )

    assert policy.visible_lifecycles == {
        "ACTIVE"
    }

    assert policy.blocked_availability == {
        "UNAVAILABLE"
    }


def test_empty_lifecycle_policy_is_rejected() -> None:
    with pytest.raises(
        VisibilityPolicyError
    ):
        SearchVisibilityPolicy(
            visible_lifecycles=frozenset()
        )


def test_decision_exposes_all_dimensions() -> None:
    result = make_result(
        tenant_id="tenant-a"
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        result
    )

    assert decision.allowed
    assert decision.tenant_allowed
    assert decision.lifecycle_allowed
    assert decision.availability_allowed
    assert decision.inventory_type_allowed


def test_malformed_result_fails_closed() -> None:
    malformed = SimpleNamespace(
        document=SimpleNamespace(
            tenant_id="tenant-a",
            lifecycle="",
            availability="AVAILABLE",
            inventory_type="UNIT",
            index_key="bad",
        )
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    decision = boundary.decide(
        malformed
    )

    assert not decision.allowed
    assert decision.reason == (
        VisibilityReason.MALFORMED_DOCUMENT
    )


def test_boundary_is_immutable() -> None:
    boundary = TenantVisibilityFilter(
        tenant_id="tenant-a"
    )

    with pytest.raises(
        AttributeError
    ):
        boundary.tenant_id = "tenant-b"  # type: ignore[misc]
