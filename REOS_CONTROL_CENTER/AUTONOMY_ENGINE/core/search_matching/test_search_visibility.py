from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.core.search_matching.hybrid_retrieval import HybridSearchResult
from AUTONOMY_ENGINE.core.search_matching.search_visibility import (
    SearchVisibilityPolicy,
    TenantScopeError,
    TenantVisibilityFilter,
    VisibilityPolicyError,
)


def make_result(
    *,
    tenant_id: str,
    lifecycle: str,
    availability: str,
    index_key: str = "idx-001",
) -> HybridSearchResult:
    document = SimpleNamespace(
        index_key=index_key,
        inventory_code="UNIT-001",
        tenant_id=tenant_id,
        lifecycle=lifecycle,
        availability=availability,
        name="Test Unit",
    )

    return HybridSearchResult(
        document=document,
        rrf_score=0.5,
        lexical_rank=1,
        vector_rank=1,
    )


def test_same_tenant_active_available_is_visible():
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    assert boundary.is_visible(result)


def test_cross_tenant_result_is_blocked():
    result = make_result(
        tenant_id="tenant-999",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    decision = boundary.decide(result)

    assert not decision.allowed
    assert not decision.tenant_allowed


@pytest.mark.parametrize(
    "lifecycle",
    ["DRAFT", "ONBOARDING", "SUSPENDED", "ARCHIVED"],
)
def test_non_active_lifecycle_is_blocked(lifecycle):
    result = make_result(
        tenant_id="tenant-001",
        lifecycle=lifecycle,
        availability="AVAILABLE",
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    assert not boundary.is_visible(result)


def test_unavailable_inventory_is_blocked():
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="ACTIVE",
        availability="UNAVAILABLE",
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    decision = boundary.decide(result)

    assert not decision.allowed
    assert decision.tenant_allowed
    assert decision.lifecycle_allowed
    assert not decision.availability_allowed


@pytest.mark.parametrize(
    "availability",
    ["AVAILABLE", "RESERVED", "SOLD"],
)
def test_non_blocked_availability_remains_visible(availability):
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="ACTIVE",
        availability=availability,
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    assert boundary.is_visible(result)


def test_apply_filters_without_reordering():
    results = (
        make_result(
            tenant_id="tenant-001",
            lifecycle="ACTIVE",
            availability="AVAILABLE",
            index_key="idx-003",
        ),
        make_result(
            tenant_id="tenant-999",
            lifecycle="ACTIVE",
            availability="AVAILABLE",
            index_key="idx-001",
        ),
        make_result(
            tenant_id="tenant-001",
            lifecycle="ACTIVE",
            availability="RESERVED",
            index_key="idx-002",
        ),
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    filtered = boundary.apply(results)

    assert [item.document.index_key for item in filtered] == [
        "idx-003",
        "idx-002",
    ]


def test_empty_result_is_safe():
    boundary = TenantVisibilityFilter(tenant_id="tenant-001")

    assert boundary.apply(()) == ()


def test_result_input_is_not_mutated():
    results = (
        make_result(
            tenant_id="tenant-001",
            lifecycle="ACTIVE",
            availability="AVAILABLE",
        ),
    )

    before = results

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")
    boundary.apply(results)

    assert results == before


def test_tenant_id_is_trimmed():
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
    )

    boundary = TenantVisibilityFilter(tenant_id="  tenant-001  ")

    assert boundary.is_visible(result)


def test_empty_tenant_is_rejected():
    with pytest.raises(TenantScopeError):
        TenantVisibilityFilter(tenant_id="   ")


def test_non_string_tenant_is_rejected():
    with pytest.raises(TenantScopeError):
        TenantVisibilityFilter(tenant_id=123)


def test_custom_policy_can_allow_multiple_lifecycles():
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="SUSPENDED",
        availability="AVAILABLE",
    )

    policy = SearchVisibilityPolicy(
        visible_lifecycles=frozenset({"ACTIVE", "SUSPENDED"}),
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-001",
        policy=policy,
    )

    assert boundary.is_visible(result)


def test_custom_policy_can_block_reserved():
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="ACTIVE",
        availability="RESERVED",
    )

    policy = SearchVisibilityPolicy(
        blocked_availability=frozenset({"UNAVAILABLE", "RESERVED"}),
    )

    boundary = TenantVisibilityFilter(
        tenant_id="tenant-001",
        policy=policy,
    )

    assert not boundary.is_visible(result)


def test_policy_normalizes_values():
    policy = SearchVisibilityPolicy(
        visible_lifecycles=frozenset({" active "}),
        blocked_availability=frozenset({" unavailable "}),
    )

    assert policy.visible_lifecycles == frozenset({"ACTIVE"})
    assert policy.blocked_availability == frozenset({"UNAVAILABLE"})


def test_empty_visibility_policy_is_rejected():
    with pytest.raises(VisibilityPolicyError):
        SearchVisibilityPolicy(visible_lifecycles=frozenset())


def test_decision_exposes_all_boundary_dimensions():
    result = make_result(
        tenant_id="tenant-001",
        lifecycle="ACTIVE",
        availability="AVAILABLE",
    )

    boundary = TenantVisibilityFilter(tenant_id="tenant-001")
    decision = boundary.decide(result)

    assert decision.allowed
    assert decision.tenant_allowed
    assert decision.lifecycle_allowed
    assert decision.availability_allowed
