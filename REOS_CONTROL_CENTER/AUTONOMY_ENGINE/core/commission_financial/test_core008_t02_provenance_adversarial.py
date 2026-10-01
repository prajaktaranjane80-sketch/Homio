from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from .commission_contract import (
    CommissionBasis,
    CommissionBasisType,
    CommissionContract,
    CommissionContractState,
    CommissionContractValidationError,
    CommissionEligibilityRule,
    CommissionEntitlementReference,
    CommissionPartyReference,
    CommissionPartyType,
    CommissionProvenance,
    CommissionRate,
    CommissionRateType,
    EligibilityOperator,
)
from .commission_contract_provenance import (
    CommissionProvenanceRecord,
    provenance_is_before_effective_start,
)


UTC = timezone.utc


def build_contract() -> CommissionContract:
    start = datetime(
        2026,
        9,
        10,
        tzinfo=UTC,
    )

    return CommissionContract(
        commission_id="commission-proof",
        tenant_id="tenant-a",
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-proof",
            tenant_id="tenant-a",
            entitled_party=CommissionPartyReference(
                CommissionPartyType.BROKER,
                "broker-proof",
            ),
            deal_reference="deal-proof",
            ownership_reference="ownership-proof",
            provenance_reference="ownership-evidence",
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
        effective_from=start,
        effective_to=None,
        contract_version=1,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-proof",
            captured_at=(
                start - timedelta(days=1)
            ),
            evidence_reference="evidence-proof",
        ),
        state=CommissionContractState.ACTIVE,
    )


def test_provenance_record_preserves_contract_identity() -> None:
    contract = build_contract()

    record = CommissionProvenanceRecord.from_contract(
        contract
    )

    assert record.identity_key == (
        "tenant-a",
        "commission-proof",
        1,
    )

    record.assert_scope(
        tenant_id="tenant-a",
        commission_id="commission-proof",
    )


def test_provenance_cross_scope_is_rejected() -> None:
    record = CommissionProvenanceRecord.from_contract(
        build_contract()
    )

    with pytest.raises(ValueError):
        record.assert_scope(
            tenant_id="tenant-b",
            commission_id="commission-proof",
        )


def test_provenance_must_precede_effective_start() -> None:
    contract = build_contract()

    assert (
        provenance_is_before_effective_start(
            contract
        )
        is True
    )


def test_late_provenance_is_rejected_at_contract_boundary() -> None:
    original = build_contract()

    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionContract(
        commission_id=original.commission_id,
        tenant_id=original.tenant_id,
        entitlement=original.entitlement,
        basis=original.basis,
        rate=original.rate,
        eligibility_rules=original.eligibility_rules,
        effective_from=original.effective_from,
        effective_to=original.effective_to,
        contract_version=original.contract_version,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="late-mou",
            captured_at=(
                original.effective_from
                + timedelta(seconds=1)
            ),
            evidence_reference="late-evidence",
        ),
            state=original.state,
        )


def test_provenance_is_version_specific() -> None:
    first = build_contract()

    second = CommissionContract(
        commission_id=first.commission_id,
        tenant_id=first.tenant_id,
        entitlement=first.entitlement,
        basis=first.basis,
        rate=CommissionRate(
            rate_type=CommissionRateType.PERCENTAGE,
            value="3.0",
        ),
        eligibility_rules=first.eligibility_rules,
        effective_from=(
            first.effective_from
            + timedelta(days=30)
        ),
        effective_to=None,
        contract_version=2,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-v2",
            captured_at=(
                first.effective_from
                + timedelta(days=29)
            ),
            evidence_reference="evidence-v2",
        ),
        state=CommissionContractState.DRAFT,
    )

    first_record = CommissionProvenanceRecord.from_contract(
        first
    )

    second_record = CommissionProvenanceRecord.from_contract(
        second
    )

    assert first_record.identity_key != (
        second_record.identity_key
    )

    assert (
        first_record.provenance.source_reference
        != second_record.provenance.source_reference
    )
