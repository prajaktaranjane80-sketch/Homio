from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from ..deal_transaction.deal import Deal
from ..deal_transaction.deal_parties import DealPartyLifecycle, DealPartyRole
from .commission_allocation import (
    CommissionAllocation,
    CommissionAllocationValidationError,
)
from .commission_allocation_validation import validate_allocation
from .commission_attribution import CommissionAttributionBinding
from .commission_calculation import (
    CommissionCalculationState,
    calculate_commission,
)
from .commission_calculation_basis import CommissionCalculationBasis
from .commission_contract import (
    CommissionBasisType,
    CommissionPartyReference,
    CommissionPartyType,
)
from .commission_entitlement import (
    CommissionEntitlement,
    CommissionEntitlementState,
)
from .commission_participant_split import (
    CommissionParticipantSplit,
    CommissionParticipantSplitValidationError,
)
from .financial_domain import Currency, MonetaryAmount
from .test_core008_t02_attribution_binding import (
    NOW,
    OTHER_TENANT_ID,
    TENANT_ID,
    build_sources,
)


DEFAULT_PARTIES = (
    (CommissionPartyType.BROKER, "broker-001"),
    (CommissionPartyType.PARTNER, "builder-001"),
    (CommissionPartyType.REFERRAL_PARTY, "referrer-001"),
)


def _make_allocation(
    calculation,
    entitlements,
) -> CommissionAllocation:
    return CommissionAllocation.from_entitlements(
        calculation,
        tuple(entitlements),
        allocation_set_id="allocation-set-001",
        eligibility_reference="eligibility-001",
        authorization_reference="auth-001",
        provenance_reference="deal-proof-001",
    )


def _build_fixture(
    *,
    base_amount: str = "1.20",
    amounts: tuple[str, ...] | None = None,
    parties=DEFAULT_PARTIES,
):
    contract, lead, deal = build_sources()
    parties = tuple(parties)

    if any(
        party_type in (CommissionPartyType.AGENT, CommissionPartyType.REFERRAL_PARTY)
        for party_type, _ in parties
    ):
        if not any(p.role is DealPartyRole.REPRESENTATIVE for p in deal.participants):
            deal = deal.bind_party(
                role=DealPartyRole.REPRESENTATIVE,
                party_id="referrer-001",
                tenant_id=deal.tenant_id,
                expected_version=deal.version,
            )

    attribution = CommissionAttributionBinding.from_authoritative_sources(
        contract, lead, deal
    )

    basis = CommissionCalculationBasis(
        basis_reference="basis-001",
        source_reference="deal.gross_value",
        source_version=1,
        captured_at=NOW,
        amount=MonetaryAmount.create(base_amount, Currency("INR", 2)),
        basis_code=CommissionBasisType.GROSS_TRANSACTION_VALUE.value,
    )
    calculation = calculate_commission(
        contract,
        basis,
        calculated_at=NOW + timedelta(hours=1),
        eligibility_confirmed=True,
        eligibility_reference="eligibility-001",
        provenance_reference="deal-proof-001",
        calculation_version=1,
        calculation_id="calc-001",
    )

    if amounts is None:
        amounts = (
            tuple("0.00" for _ in parties)
            if Decimal(base_amount) == 0
            else tuple("0.01" for _ in parties)
        )

    if len(amounts) != len(parties):
        raise ValueError("Test helper requires one amount per party.")

    entitlements = tuple(
        CommissionEntitlement.from_calculation(
            calculation,
            entitlement_id=f"entitlement-{index}",
            entitled_party=CommissionPartyReference(
                party_type=party_type,
                party_id=party_id,
            ),
            eligibility_reference="eligibility-001",
            authorization_reference="auth-001",
            provenance_reference="deal-proof-001",
            established_at=NOW + timedelta(hours=2),
            entitled_amount=MonetaryAmount.create(
                amount,
                calculation.commission_amount.currency,
            ),
            state=CommissionEntitlementState.CONFIRMED,
        )
        for index, ((party_type, party_id), amount)
        in enumerate(zip(parties, amounts), start=1)
    )

    allocation = _make_allocation(calculation, entitlements)
    return contract, lead, deal, attribution, calculation, entitlements, allocation


def test_three_minor_unit_shares_have_deterministic_ratios_totaling_100() -> None:
    _, _, _, _, calculation, entitlements, allocation = _build_fixture()
    assert calculation.commission_amount.amount == Decimal("0.03")
    assert sum((x.entitled_amount.amount for x in entitlements), Decimal("0")) == Decimal("0.03")
    assert sum((x.allocation_ratio for x in allocation.lines), Decimal("0")) == Decimal("100")
    assert allocation.lines[0].allocation_ratio == Decimal("33.33333334")
    assert allocation.lines[1].allocation_ratio == Decimal("33.33333333")
    assert allocation.lines[2].allocation_ratio == Decimal("33.33333333")


def test_zero_value_allocation_has_zero_ratios_and_validates() -> None:
    _, _, _, _, calculation, _, allocation = _build_fixture(base_amount="0.00")
    assert allocation.total_amount.amount == Decimal("0.00")
    assert all(line.allocation_ratio == Decimal("0") for line in allocation.lines)
    assert validate_allocation(allocation, calculation) == ()


@pytest.mark.parametrize(
    "state",
    (
        CommissionEntitlementState.PENDING,
        CommissionEntitlementState.SUPERSEDED,
        CommissionEntitlementState.VOID,
    ),
)
def test_unconfirmed_or_inactive_entitlement_cannot_be_allocated(state) -> None:
    _, _, _, _, _, entitlements, allocation = _build_fixture()
    updated = (replace(entitlements[0], state=state),) + entitlements[1:]
    with pytest.raises(CommissionAllocationValidationError, match="confirmed or frozen"):
        _make_allocation(
            # The helper fixture's allocation was generated from its canonical calculation.
            # Entitlement state is checked before any financial split is generated.
            _build_fixture()[4],
            updated,
        )


def test_frozen_entitlement_can_be_allocated() -> None:
    _, _, _, _, calculation, entitlements, _ = _build_fixture()
    updated = (replace(entitlements[0], state=CommissionEntitlementState.FROZEN),) + entitlements[1:]
    assert _make_allocation(calculation, updated).total_amount.amount == Decimal("0.03")


@pytest.mark.parametrize(
    "state",
    (CommissionCalculationState.VOID, CommissionCalculationState.SUPERSEDED),
)
def test_invalid_calculation_lifecycle_cannot_be_allocated(state) -> None:
    _, _, _, _, calculation, entitlements, _ = _build_fixture()
    with pytest.raises(CommissionAllocationValidationError, match="Only CALCULATED"):
        _make_allocation(replace(calculation, state=state), entitlements)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("contract_version", 2, "contract_version"),
        ("calculation_version", 2, "calculation_version"),
    ),
)
def test_entitlement_versions_must_match_the_calculation(field, value, message) -> None:
    _, _, _, _, calculation, entitlements, _ = _build_fixture()
    invalid = replace(entitlements[0], **{field: value})
    with pytest.raises(CommissionAllocationValidationError, match=message):
        _make_allocation(calculation, (invalid,) + entitlements[1:])


def test_non_entitlement_input_fails_with_domain_error() -> None:
    _, _, _, _, calculation, _, _ = _build_fixture()
    with pytest.raises(CommissionAllocationValidationError, match="Invalid entitlement"):
        _make_allocation(calculation, ("not-an-entitlement",))


def test_split_resolves_all_recipients_to_compatible_deal_roles() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture()
    split = CommissionParticipantSplit.from_authoritative_sources(
        allocation, deal, attribution
    )
    assert [line.deal_role for line in split.lines] == [
        "BROKER", "BUILDER", "REPRESENTATIVE"
    ]
    assert split.immutable_fingerprint == CommissionParticipantSplit.from_authoritative_sources(
        allocation, deal, attribution
    ).immutable_fingerprint
    assert split.to_dict()["authorities"]["deal"] == "CORE-006"
    assert split.to_dict()["authorities"]["ownership"] == "ARCH-011"
    assert deal.ownership_binding is not None
    assert split.to_dict()["ownership_binding"]["binding_id"] == deal.ownership_binding.binding_id


def test_split_rejects_recipient_not_in_the_deal() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture(
        parties=(
            (CommissionPartyType.BROKER, "broker-001"),
            (CommissionPartyType.PARTNER, "partner-not-on-deal"),
            (CommissionPartyType.REFERRAL_PARTY, "referrer-001"),
        )
    )
    with pytest.raises(CommissionParticipantSplitValidationError, match="compatible Deal participant"):
        CommissionParticipantSplit.from_authoritative_sources(allocation, deal, attribution)


def test_split_rejects_party_type_that_does_not_match_deal_role() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture(
        parties=(
            (CommissionPartyType.BROKER, "broker-001"),
            (CommissionPartyType.AGENT, "broker-001"),
            (CommissionPartyType.PARTNER, "builder-001"),
        )
    )
    with pytest.raises(CommissionParticipantSplitValidationError, match="compatible Deal participant"):
        CommissionParticipantSplit.from_authoritative_sources(allocation, deal, attribution)


def test_split_rejects_suspended_participant() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture()
    updated_participants = tuple(
        replace(p, lifecycle=DealPartyLifecycle.SUSPENDED)
        if p.party_id == "builder-001"
        else p
        for p in deal.participants
    )
    suspended_deal = replace(deal, participants=updated_participants)
    with pytest.raises(CommissionParticipantSplitValidationError, match="active Deal participant"):
        CommissionParticipantSplit.from_authoritative_sources(
            allocation, suspended_deal, attribution
        )


def test_split_rejects_a_stale_deal_version() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture()
    updated_deal = deal.bind_party(
        role=DealPartyRole.SELLER,
        party_id="seller-001",
        tenant_id=deal.tenant_id,
        expected_version=deal.version,
    )
    with pytest.raises(CommissionParticipantSplitValidationError, match="Deal version"):
        CommissionParticipantSplit.from_authoritative_sources(
            allocation, updated_deal, attribution
        )


def test_split_rejects_cross_tenant_deal() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture()
    other_tenant_deal = Deal.create(
        tenant_id=str(OTHER_TENANT_ID),
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        deal_id=deal.deal_id,
        at=NOW,
    )
    with pytest.raises(CommissionParticipantSplitValidationError, match="tenant scopes"):
        CommissionParticipantSplit.from_authoritative_sources(
            allocation, other_tenant_deal, attribution
        )


def test_split_rejects_ownership_binding_substitution() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture()
    assert deal.ownership_binding is not None
    substituted_binding = replace(
        deal.ownership_binding,
        binding_id="binding-other",
        ownership_record_id="ownership-other",
        owner_id="owner-other",
    )
    tampered_deal = replace(
        deal,
        ownership_binding=substituted_binding,
    )
    with pytest.raises(CommissionParticipantSplitValidationError, match="ownership binding"):
        CommissionParticipantSplit.from_authoritative_sources(
            allocation, tampered_deal, attribution
        )

def test_allocation_must_include_the_contract_entitled_party() -> None:
    _, _, deal, attribution, _, _, allocation = _build_fixture(
        parties=(
            (CommissionPartyType.PARTNER, "builder-001"),
            (CommissionPartyType.REFERRAL_PARTY, "referrer-001"),
        ),
        amounts=("0.02", "0.01"),
    )
    with pytest.raises(CommissionParticipantSplitValidationError, match="entitled party must be present"):
        CommissionParticipantSplit.from_authoritative_sources(
            allocation, deal, attribution
        )


def test_split_is_exported_by_the_commission_financial_package() -> None:
    from . import CommissionParticipantSplit as PublicSplit
    assert PublicSplit is CommissionParticipantSplit