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
from .commission_contract_conflict import (
    CommissionContractVersionConflictError,
    assert_no_contract_conflict,
    detect_contract_conflict,
)


UTC = timezone.utc


def make_contract(
    *,
    version: int = 1,
    commission_id: str = "commission-conflict",
    tenant_id: str = "tenant-a",
    rate: str = "2.5",
) -> CommissionContract:
    start = datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    )

    return CommissionContract(
        commission_id=commission_id,
        tenant_id=tenant_id,
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-conflict",
            tenant_id=tenant_id,
            entitled_party=CommissionPartyReference(
                CommissionPartyType.BROKER,
                "broker-conflict",
            ),
            deal_reference="deal-conflict",
            ownership_reference="ownership-conflict",
            provenance_reference="proof-conflict",
        ),
        basis=CommissionBasis(
            CommissionBasisType.GROSS_TRANSACTION_VALUE,
            "deal.gross_value",
        ),
        rate=CommissionRate(
            CommissionRateType.PERCENTAGE,
            rate,
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
        contract_version=version,
        provenance=CommissionProvenance(
            "MOU",
            f"mou-{version}",
            start,
            f"proof-{version}",
        ),
        state=CommissionContractState.ACTIVE,
    )


def test_exact_duplicate_is_not_a_conflict() -> None:
    first = make_contract()
    second = make_contract()

    report = detect_contract_conflict(
        first,
        second,
    )

    assert report.conflict is False
    assert report.same_identity is True
    assert report.same_version is True
    assert report.same_terms is True

    assert_no_contract_conflict(
        first,
        second,
    )


def test_same_version_changed_rate_is_conflict() -> None:
    first = make_contract(
        rate="2.5"
    )

    second = make_contract(
        rate="3.5"
    )

    report = detect_contract_conflict(
        first,
        second,
    )

    assert report.conflict is True

    with pytest.raises(
        CommissionContractVersionConflictError
    ):
        assert_no_contract_conflict(
            first,
            second,
        )


def test_new_version_is_not_same_version_conflict() -> None:
    first = make_contract(
        version=1,
        rate="2.5",
    )

    second = make_contract(
        version=2,
        rate="3.5",
    )

    report = detect_contract_conflict(
        first,
        second,
    )

    assert report.conflict is False
    assert report.same_identity is True
    assert report.same_version is False
    assert report.same_terms is False


def test_different_identity_is_not_term_conflict() -> None:
    first = make_contract(
        commission_id="commission-a",
    )

    second = make_contract(
        commission_id="commission-b",
    )

    report = detect_contract_conflict(
        first,
        second,
    )

    assert report.conflict is False
    assert report.same_identity is False


def test_same_identity_and_version_is_never_silently_replaced() -> None:
    first = make_contract(
        rate="2.5"
    )

    incoming = make_contract(
        rate="4.0"
    )

    with pytest.raises(
        CommissionContractVersionConflictError
    ):
        assert_no_contract_conflict(
            first,
            incoming,
        )
