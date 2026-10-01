from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from .commission_calculation import calculate_commission
from .commission_calculation_basis import (
    CommissionCalculationBasis,
)
from .commission_contract import (
    CommissionBasis,
    CommissionBasisType,
    CommissionContract,
    CommissionContractState,
    CommissionEligibilityRule,
    CommissionEntitlementReference,
    CommissionPartyReference,
    CommissionPartyType,
    CommissionProvenance,
    CommissionRate,
    CommissionRateType,
    EligibilityOperator,
)
from .commission_entitlement import (
    CommissionEntitlement,
)
from .financial_domain import (
    Currency,
    FinancialCurrencyMismatchError,
    MonetaryAmount,
)


UTC = timezone.utc

START = datetime(
    2026,
    9,
    1,
    tzinfo=UTC,
)


def _contract(
    tenant_id: str = "tenant-a",
) -> CommissionContract:
    return CommissionContract(
        commission_id="commission-001",
        tenant_id=tenant_id,
        entitlement=CommissionEntitlementReference(
            entitlement_id="entitlement-001",
            tenant_id=tenant_id,
            entitled_party=CommissionPartyReference(
                party_type=CommissionPartyType.BROKER,
                party_id="broker-001",
            ),
            deal_reference="deal-001",
            ownership_reference="ownership-001",
            provenance_reference="ownership-proof-001",
        ),
        basis=CommissionBasis(
            basis_type=(
                CommissionBasisType.GROSS_TRANSACTION_VALUE
            ),
            source_reference="deal.gross_value",
        ),
        rate=CommissionRate(
            rate_type=CommissionRateType.PERCENTAGE,
            value="2.5",
        ),
        eligibility_rules=(
            CommissionEligibilityRule(
                rule_code="DEAL_ELIGIBLE",
                operator=EligibilityOperator.EQUALS,
                value="ELIGIBLE",
            ),
        ),
        effective_from=START,
        effective_to=None,
        contract_version=1,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-001",
            captured_at=(
                START - timedelta(days=1)
            ),
            evidence_reference="evidence-001",
        ),
        state=CommissionContractState.ACTIVE,
    )


def _basis(
    amount: str = "1000000.00",
) -> CommissionCalculationBasis:
    return CommissionCalculationBasis(
        basis_reference="basis-001",
        source_reference="deal.gross_value",
        source_version=1,
        captured_at=START,
        amount=MonetaryAmount.create(
            amount,
            Currency("INR", 2),
        ),
        basis_code=(
            CommissionBasisType.GROSS_TRANSACTION_VALUE.value
        ),
    )


def test_money_uses_canonical_decimal_rounding() -> None:
    amount = MonetaryAmount.create(
        "100.005",
        Currency("INR", 2),
    )

    assert amount.amount == amount.amount.quantize(
        Currency("INR", 2).quantum
    )

    assert amount.currency.code == "INR"
    assert amount.currency.minor_unit == 2


def test_currency_semantics_are_part_of_identity() -> None:
    inr = Currency("INR", 2)
    usd = Currency("USD", 2)

    assert inr.identity_key != usd.identity_key

    with pytest.raises(
        FinancialCurrencyMismatchError
    ):
        MonetaryAmount.create(
            "10.00",
            inr,
        ).add(
            MonetaryAmount.create(
                "10.00",
                usd,
            )
        )


def test_calculation_is_reproducible_for_identical_inputs() -> None:
    contract = _contract()
    basis = _basis()

    first = calculate_commission(
        contract,
        basis,
        calculated_at=START + timedelta(hours=1),
        eligibility_confirmed=True,
        eligibility_reference="eligibility-001",
        provenance_reference="proof-001",
        calculation_version=1,
        calculation_id="calc-a",
    )

    second = calculate_commission(
        contract,
        basis,
        calculated_at=START + timedelta(hours=1),
        eligibility_confirmed=True,
        eligibility_reference="eligibility-001",
        provenance_reference="proof-001",
        calculation_version=1,
        calculation_id="calc-b",
    )

    assert first.commission_amount.amount == second.commission_amount.amount
    assert first.commission_amount.currency.identity_key == (
        second.commission_amount.currency.identity_key
    )
    assert first.idempotency_key == second.idempotency_key


def test_calculation_requires_external_eligibility_confirmation() -> None:
    with pytest.raises(Exception):
        calculate_commission(
            _contract(),
            _basis(),
            calculated_at=START + timedelta(hours=1),
            eligibility_confirmed=False,
            eligibility_reference="eligibility-001",
            provenance_reference="proof-001",
        )


def test_entitlement_cannot_exceed_calculated_commission() -> None:
    calculation = calculate_commission(
        _contract(),
        _basis(),
        calculated_at=START + timedelta(hours=1),
        eligibility_confirmed=True,
        eligibility_reference="eligibility-001",
        provenance_reference="proof-001",
    )

    with pytest.raises(Exception):
        CommissionEntitlement.from_calculation(
            calculation,
            entitlement_id="entitlement-002",
            entitled_party=CommissionPartyReference(
                party_type=CommissionPartyType.BROKER,
                party_id="broker-002",
            ),
            eligibility_reference="eligibility-001",
            authorization_reference="auth-001",
            provenance_reference="proof-001",
            established_at=START + timedelta(hours=2),
            entitled_amount=MonetaryAmount.create(
                "999999.99",
                calculation.commission_amount.currency,
            ),
        )


def test_financial_contract_and_amounts_are_immutable() -> None:
    contract = _contract()

    with pytest.raises(FrozenInstanceError):
        contract.rate = CommissionRate(  # type: ignore[misc]
            rate_type=CommissionRateType.PERCENTAGE,
            value="3.0",
        )

    amount = MonetaryAmount.create(
        "100.00",
        Currency("INR", 2),
    )

    with pytest.raises(FrozenInstanceError):
        amount.amount = amount.amount  # type: ignore[misc]


def test_tenant_boundary_is_enforced() -> None:
    contract = _contract()

    with pytest.raises(Exception):
        contract.assert_tenant(
            "tenant-b"
        )

    calculation = calculate_commission(
        contract,
        _basis(),
        calculated_at=START + timedelta(hours=1),
        eligibility_confirmed=True,
        eligibility_reference="eligibility-001",
        provenance_reference="proof-001",
    )

    with pytest.raises(Exception):
        calculation.assert_tenant(
            "tenant-b"
        )
