from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from types import SimpleNamespace

import pytest

from .deal import (
    Deal,
    DealConcurrencyError,
    DealStatus,
    DealTenantError,
)
from .deal_contract import DealHistoryEntry
from .deal_transaction_consistency import (
    validate_deal_consistency,
)


AT = "2026-09-29T06:00:00+00:00"


def make_deal(
    *,
    bound: bool = True,
) -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001" if bound else None,
        project_id="project-001" if bound else None,
        unit_id="unit-001" if bound else None,
        deal_id="deal-001",
        at=AT,
    )


def move_to(
    deal: Deal,
    *states: DealStatus,
) -> Deal:
    current = deal

    for state in states:
        current = current.transition(
            state,
            tenant_id=current.tenant_id,
            expected_version=current.version,
            at=AT,
        )

    return current


def shadow(
    deal: Deal,
    **overrides,
) -> SimpleNamespace:
    values = {
        "deal_id": deal.deal_id,
        "tenant_id": deal.tenant_id,
        "customer_id": deal.customer_id,
        "broker_id": deal.broker_id,
        "status": deal.status,
        "version": deal.version,
        "history": deal.history,
        "participants": deal.participants,
        "offers": deal.offers,
        "negotiation": deal.negotiation,
        "milestones": deal.milestones,
        "ownership_binding": deal.ownership_binding,
        "evidence": deal.evidence,
        "audit_log": deal.audit_log,
    }

    values.update(overrides)
    return SimpleNamespace(**values)


def test_fresh_deal_is_consistent() -> None:
    deal = make_deal()

    result = validate_deal_consistency(
        deal,
        tenant_id="tenant-001",
    )

    assert result.valid
    assert result.violations == ()
    assert "tenant" in result.checked
    assert "version" in result.checked
    assert "history" in result.checked


def test_lifecycle_state_and_history_remain_consistent() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    )

    result = validate_deal_consistency(
        deal,
        tenant_id="tenant-001",
    )

    assert result.valid, result.violations
    assert deal.history[0].version == 1
    assert deal.history[-1].version == deal.version


def test_tenant_scope_mismatch_is_invalid() -> None:
    result = validate_deal_consistency(
        make_deal(),
        tenant_id="tenant-999",
    )

    assert not result.valid
    assert any(
        item.code == "TENANT_SCOPE"
        for item in result.violations
    )


def test_history_must_start_at_version_one() -> None:
    deal = make_deal()

    invalid_history = (
        DealHistoryEntry(
            history_id="history-2",
            from_status=DealStatus.QUALIFIED,
            to_status=DealStatus.MATCHED,
            version=2,
            changed_at=deal.created_at,
            reason="INVALID",
        ),
    )

    result = validate_deal_consistency(
        shadow(
            deal,
            history=invalid_history,
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "HISTORY_ORDER"
        for item in result.violations
    )


def test_duplicate_party_relationship_is_invalid() -> None:
    deal = make_deal()

    result = validate_deal_consistency(
        shadow(
            deal,
            participants=deal.participants + (
                deal.participants[0],
            ),
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "PARTY_DUPLICATE"
        for item in result.violations
    )


def test_cross_deal_offer_is_invalid() -> None:
    deal = make_deal()

    offer = SimpleNamespace(
        offer_id="offer-001",
        deal_id="other-deal",
        tenant_id="tenant-001",
    )

    result = validate_deal_consistency(
        shadow(
            deal,
            offers=(offer,),
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "OFFER_SCOPE"
        for item in result.violations
    )


def test_cross_tenant_offer_is_invalid() -> None:
    deal = make_deal()

    offer = SimpleNamespace(
        offer_id="offer-001",
        deal_id="deal-001",
        tenant_id="tenant-999",
    )

    result = validate_deal_consistency(
        shadow(
            deal,
            offers=(offer,),
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "OFFER_TENANT"
        for item in result.violations
    )


def test_duplicate_offer_identity_is_invalid() -> None:
    deal = make_deal()

    first = SimpleNamespace(
        offer_id="offer-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
    )

    second = SimpleNamespace(
        offer_id="offer-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
    )

    result = validate_deal_consistency(
        shadow(
            deal,
            offers=(first, second),
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "OFFER_DUPLICATE"
        for item in result.violations
    )


def test_negotiation_requires_existing_active_offer() -> None:
    deal = make_deal()

    negotiation = SimpleNamespace(
        deal_id="deal-001",
        tenant_id="tenant-001",
        active_offer_id="missing-offer",
    )

    result = validate_deal_consistency(
        shadow(
            deal,
            offers=(),
            negotiation=negotiation,
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "NEGOTIATION_OFFER"
        for item in result.violations
    )


def test_milestone_sequence_must_be_contiguous() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    )

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        reference_id="booking-001",
        at=AT,
    )

    milestone = updated.milestones[0]

    broken = replace(
        milestone,
        sequence=3,
    )

    result = validate_deal_consistency(
        shadow(
            updated,
            milestones=(broken,),
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "MILESTONE_SEQUENCE"
        for item in result.violations
    )


def test_milestone_versions_must_increase() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    )

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        reference_id="booking-001",
        at=AT,
    )

    first = updated.milestones[0]
    second = replace(
        first,
        milestone_id="milestone-002",
        sequence=2,
        deal_version=first.deal_version,
    )

    result = validate_deal_consistency(
        shadow(
            updated,
            milestones=(first, second),
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "MILESTONE_VERSION"
        for item in result.violations
    )


def test_current_status_must_match_latest_milestone() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    )

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        reference_id="booking-001",
        at=AT,
    )

    result = validate_deal_consistency(
        shadow(
            updated,
            status=DealStatus.OFFERED,
        ),
        tenant_id="tenant-001",
    )

    assert not result.valid
    assert any(
        item.code == "CURRENT_STATUS"
        for item in result.violations
    )


def test_stale_transition_is_rejected() -> None:
    deal = make_deal()

    current = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    with pytest.raises(DealConcurrencyError):
        current.transition(
            DealStatus.VISIT_PENDING,
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )


def test_wrong_tenant_is_rejected_before_mutation() -> None:
    deal = make_deal()

    with pytest.raises(DealTenantError):
        deal.transition(
            DealStatus.MATCHED,
            tenant_id="tenant-999",
            expected_version=deal.version,
            at=AT,
        )

    assert deal.version == 1
    assert deal.status is DealStatus.QUALIFIED


def test_optimistic_concurrency_is_monotonic() -> None:
    deal = make_deal()

    first = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    second = first.transition(
        DealStatus.VISIT_PENDING,
        tenant_id="tenant-001",
        expected_version=2,
        at=AT,
    )

    third = second.transition(
        DealStatus.VISITED,
        tenant_id="tenant-001",
        expected_version=3,
        at=AT,
    )

    assert (deal.version, first.version, second.version, third.version) == (
        1,
        2,
        3,
        4,
    )


def test_failed_concurrent_update_does_not_mutate_snapshot() -> None:
    deal = make_deal()

    updated = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    with pytest.raises(DealConcurrencyError):
        updated.transition(
            DealStatus.VISIT_PENDING,
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )

    assert updated.version == 2
    assert updated.status is DealStatus.MATCHED


def test_immutable_snapshot_survives_parallel_mutations() -> None:
    deal = make_deal()

    def mutate() -> Deal:
        return deal.transition(
            DealStatus.MATCHED,
            tenant_id="tenant-001",
            expected_version=1,
            at=AT,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda _: mutate(),
                range(32),
            )
        )

    assert len(results) == 32
    assert all(item.version == 2 for item in results)
    assert all(
        item.status is DealStatus.MATCHED
        for item in results
    )

    assert deal.version == 1
    assert deal.status is DealStatus.QUALIFIED
    assert len(deal.history) == 1


def test_parallel_mutations_have_independent_results() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
    )

    def mutate() -> Deal:
        return deal.create_offer(
            offer_id="offer-001",
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda _: mutate(),
                range(16),
            )
        )

    assert len(results) == 16
    assert all(item.version == deal.version + 1 for item in results)
    assert all(
        len(item.offers) == 1
        and item.offers[0].offer_id == "offer-001"
        for item in results
    )

    assert deal.offers == ()


@pytest.mark.parametrize(
    "method_name",
    (
        "bind_opportunity",
        "bind_party",
        "transition",
        "create_offer",
        "submit_offer",
        "start_negotiation",
        "transition_negotiation",
        "close_negotiation",
        "advance_transaction_milestone",
        "bind_ownership",
        "attach_evidence",
        "record_audit",
    ),
)
def test_all_mutating_operations_expose_expected_version(
    method_name: str,
) -> None:
    method = getattr(Deal, method_name)
    assert "expected_version" in method.__annotations__ or (
        "expected_version" in str(
            getattr(method, "__doc__", "")
        )
    ) or "expected_version" in str(method)


def test_consistency_result_is_immutable() -> None:
    result = validate_deal_consistency(
        make_deal(),
        tenant_id="tenant-001",
    )

    with pytest.raises(Exception):
        result.valid = False  # type: ignore[misc]


def test_consistency_require_valid_returns_same_result() -> None:
    result = validate_deal_consistency(
        make_deal(),
        tenant_id="tenant-001",
    )

    assert result.require_valid() is result


def test_invalid_consistency_result_cannot_be_required() -> None:
    result = validate_deal_consistency(
        make_deal(),
        tenant_id="tenant-999",
    )

    with pytest.raises(ValueError):
        result.require_valid()


def test_no_mutation_occurs_during_consistency_validation() -> None:
    deal = make_deal()

    before = deal.to_dict()

    result = validate_deal_consistency(
        deal,
        tenant_id="tenant-001",
    )

    after = deal.to_dict()

    assert result.valid
    assert before == after