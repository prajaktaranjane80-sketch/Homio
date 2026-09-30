from __future__ import annotations

from datetime import datetime, timezone

import pytest

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
from .commission_contract_integrity import (
    inspect_commission_contract_integrity,
)
from .commission_contract_snapshot import (
    CommissionContractSnapshot,
    CommissionContractSnapshotIntegrityError,
)


UTC = timezone.utc


def build_contract() -> CommissionContract:
    start = datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    )

    return CommissionContract(
        commission_id="commission-snapshot",
        tenant_id="tenant-a",
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-snapshot",
            tenant_id="tenant-a",
            entitled_party=CommissionPartyReference(
                CommissionPartyType.BROKER,
                "broker-a",
            ),
            deal_reference="deal-a",
            ownership_reference="ownership-a",
            provenance_reference="ownership-proof-a",
        ),
        basis=CommissionBasis(
            CommissionBasisType.GROSS_TRANSACTION_VALUE,
            "deal.gross_value",
        ),
        rate=CommissionRate(
            CommissionRateType.PERCENTAGE,
            "2.5",
        ),
        eligibility_rules=(
            CommissionEligibilityRule(
                "ELIGIBLE",
                EligibilityOperator.EQUALS,
                "YES",
            ),
        ),
        effective_from=start,
        effective_to=None,
        contract_version=1,
        provenance=CommissionProvenance(
            source_type="MOU",
            source_reference="mou-snapshot",
            captured_at=start,
            evidence_reference="evidence-snapshot",
        ),
        state=CommissionContractState.ACTIVE,
    )


def test_snapshot_is_derived_from_contract() -> None:
    contract = build_contract()

    snapshot = CommissionContractSnapshot.from_contract(
        contract
    )

    assert snapshot.identity_key == (
        "tenant-a",
        "commission-snapshot",
        1,
    )

    snapshot.assert_matches_contract(
        contract
    )


def test_snapshot_cannot_accept_tampered_fingerprint() -> None:
    contract = build_contract()

    original = CommissionContractSnapshot.from_contract(
        contract
    )

    with pytest.raises(
        CommissionContractSnapshotIntegrityError
    ):
        CommissionContractSnapshot(
            tenant_id=original.tenant_id,
            commission_id=original.commission_id,
            contract_version=original.contract_version,
            terms=original.terms,
            terms_fingerprint="tampered",
        )


def test_snapshot_detects_contract_identity_change() -> None:
    contract = build_contract()
    snapshot = CommissionContractSnapshot.from_contract(
        contract
    )

    changed = CommissionContract(
        commission_id="commission-other",
        tenant_id=contract.tenant_id,
        entitlement=contract.entitlement,
        basis=contract.basis,
        rate=contract.rate,
        eligibility_rules=contract.eligibility_rules,
        effective_from=contract.effective_from,
        effective_to=contract.effective_to,
        contract_version=contract.contract_version,
        provenance=contract.provenance,
        state=contract.state,
    )

    with pytest.raises(
        CommissionContractSnapshotIntegrityError
    ):
        snapshot.assert_matches_contract(
            changed
        )


def test_integrity_report_passes_valid_contract() -> None:
    result = inspect_commission_contract_integrity(
        build_contract()
    )

    assert result.valid is True
    assert result.errors == ()


def test_snapshot_does_not_become_a_second_state_store() -> None:
    snapshot = CommissionContractSnapshot.from_contract(
        build_contract()
    )

    payload = snapshot.to_dict()

    assert (
        payload["snapshot_type"]
        == "CORE-008.COMMISSION_CONTRACT_SNAPSHOT"
    )

    assert (
        "state_store"
        not in payload
    )

    assert (
        "calculation_engine"
        not in payload
    )

    assert (
        "ledger"
        not in payload
    )

    assert (
        "settlement_engine"
        not in payload
    )
