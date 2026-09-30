from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from .commission_contract import (
    CommissionBasis,
    CommissionBasisType,
    CommissionContract,
    CommissionContractConflictError,
    CommissionContractState,
    CommissionContractTenantScopeError,
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
from .commission_contract_history import (
    CommissionContractHistory,
    CommissionContractHistoryOrderError,
)


UTC = timezone.utc


def contract(
    *,
    version: int = 1,
    tenant_id: str = "tenant-a",
    commission_id: str = "commission-a",
    start: datetime | None = None,
    end: datetime | None = None,
    rate: str = "2.5",
) -> CommissionContract:
    if start is None:
        start = datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        )

    if end is None:
        end = datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        )

    return CommissionContract(
        commission_id=commission_id,
        tenant_id=tenant_id,
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-a",
            tenant_id=tenant_id,
            entitled_party=CommissionPartyReference(
                party_type=CommissionPartyType.BROKER,
                party_id="broker-a",
            ),
            deal_reference="deal-a",
            ownership_reference="ownership-a",
            provenance_reference="proof-a",
        ),
        basis=CommissionBasis(
            basis_type=(
                CommissionBasisType.GROSS_TRANSACTION_VALUE
            ),
            source_reference="deal.gross_value",
        ),
        rate=CommissionRate(
            rate_type=CommissionRateType.PERCENTAGE,
            value=rate,
        ),
        eligibility_rules=(
            CommissionEligibilityRule(
                rule_code="ELIGIBLE",
                operator=EligibilityOperator.EQUALS,
                value="YES",
            ),
        ),
        effective_from=start,
        effective_to=end,
        contract_version=version,
        provenance=CommissionProvenance(
            source_type="MOU",
            source_reference=f"mou-{version}",
            captured_at=(
                start - timedelta(days=1)
            ),
            evidence_reference=f"proof-{version}",
        ),
        state=CommissionContractState.ACTIVE,
    )


def test_same_identity_same_version_cannot_hide_term_conflict() -> None:
    left = contract(
        rate="2.5"
    )

    right = contract(
        rate="4.0"
    )

    assert (
        left.identity_key
        == right.identity_key
    )

    with pytest.raises(
        CommissionContractConflictError
    ):
        left.assert_compatible(
            right
        )


def test_tenant_cannot_cross_boundary() -> None:
    value = contract()

    with pytest.raises(
        CommissionContractTenantScopeError
    ):
        value.assert_tenant(
            "tenant-b"
        )


def test_commission_contract_is_immutable() -> None:
    value = contract()

    with pytest.raises(
        FrozenInstanceError
    ):
        value.commission_id = (
            "replacement"
        )  # type: ignore[misc]


def test_history_cannot_skip_versions() -> None:
    first = contract(
        version=1,
        end=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
    )

    third = contract(
        version=3,
        start=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
        end=None,
        rate="3.0",
    )

    history = CommissionContractHistory(
        contracts=(first,)
    )

    with pytest.raises(
        CommissionContractHistoryOrderError
    ):
        history.append(
            third
        )


def test_timezone_naive_effective_date_is_rejected() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        contract(
            start=datetime(
                2026,
                9,
                1,
            )
        )


def test_percentage_above_100_is_rejected() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionRate(
            rate_type=(
                CommissionRateType.PERCENTAGE
            ),
            value="100.01",
        )


def test_percentage_negative_is_rejected() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionRate(
            rate_type=(
                CommissionRateType.PERCENTAGE
            ),
            value="-1",
        )


def test_fixed_rate_requires_currency() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionRate(
            rate_type=(
                CommissionRateType.FIXED_AMOUNT
            ),
            value="1000",
        )


def test_exists_rule_cannot_have_value() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionEligibilityRule(
            rule_code="EVIDENCE",
            operator=EligibilityOperator.EXISTS,
            value="YES",
        )


def test_history_cannot_overlap_effective_dates() -> None:
    first = contract(
        version=1,
        start=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
        end=datetime(
            2026,
            11,
            1,
            tzinfo=UTC,
        ),
    )

    second = contract(
        version=2,
        start=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
        end=None,
        rate="3.0",
    )

    with pytest.raises(
        CommissionContractHistoryOrderError
    ):
        CommissionContractHistory(
            contracts=(
                first,
                second,
            )
        )
