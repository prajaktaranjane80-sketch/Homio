from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
from .commission_contract_validation import (
    assert_valid_commission_contract,
    validate_commission_contract,
)


UTC = timezone.utc

START = datetime(
    2026,
    9,
    1,
    tzinfo=UTC,
)


def build_contract(
    state: CommissionContractState = (
        CommissionContractState.ACTIVE
    ),
) -> CommissionContract:
    return CommissionContract(
        commission_id="commission-validation",
        tenant_id="tenant-a",
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-validation",
            tenant_id="tenant-a",
            entitled_party=CommissionPartyReference(
                party_type=CommissionPartyType.BROKER,
                party_id="broker-a",
            ),
            deal_reference="deal-a",
            ownership_reference="ownership-a",
            provenance_reference="ownership-proof-a",
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
                rule_code="ELIGIBLE",
                operator=EligibilityOperator.EQUALS,
                value="YES",
            ),
        ),
        effective_from=START,
        effective_to=None,
        contract_version=1,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-validation",
            captured_at=(
                START - timedelta(days=1)
            ),
            evidence_reference="evidence-validation",
        ),
        state=state,
    )


def test_valid_contract_passes_validation() -> None:
    result = validate_commission_contract(
        build_contract(),
        expected_tenant_id="tenant-a",
    )

    assert result.valid is True
    assert result.errors == ()


def test_wrong_tenant_fails_validation() -> None:
    result = validate_commission_contract(
        build_contract(),
        expected_tenant_id="tenant-b",
    )

    assert result.valid is False
    assert any(
        "tenant" in error.lower()
        for error in result.errors
    )


def test_active_contract_without_rules_generates_warning() -> None:
    contract = build_contract()

    contract = CommissionContract(
        commission_id=contract.commission_id,
        tenant_id=contract.tenant_id,
        entitlement=contract.entitlement,
        basis=contract.basis,
        rate=contract.rate,
        eligibility_rules=(),
        effective_from=contract.effective_from,
        effective_to=contract.effective_to,
        contract_version=contract.contract_version,
        provenance=contract.provenance,
        state=contract.state,
    )

    result = validate_commission_contract(
        contract
    )

    assert result.valid is True
    assert any(
        "eligibility" in warning.lower()
        for warning in result.warnings
    )


def test_assert_valid_accepts_valid_contract() -> None:
    assert_valid_commission_contract(
        build_contract()
    )
