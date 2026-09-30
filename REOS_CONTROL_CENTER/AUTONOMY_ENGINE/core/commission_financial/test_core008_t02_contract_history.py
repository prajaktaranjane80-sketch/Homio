from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
from .commission_contract_history import (
    CommissionContractHistory,
    CommissionContractHistoryIdentityError,
    CommissionContractHistoryOrderError,
)


UTC = timezone.utc

T1 = datetime(
    2026,
    9,
    1,
    tzinfo=UTC,
)

T2 = datetime(
    2026,
    10,
    1,
    tzinfo=UTC,
)

T3 = datetime(
    2026,
    11,
    1,
    tzinfo=UTC,
)


def build_contract(
    version: int,
    start: datetime,
    end: datetime | None,
    rate: str,
) -> CommissionContract:
    return CommissionContract(
        commission_id="commission-001",
        tenant_id="tenant-a",
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-001",
            tenant_id="tenant-a",
            entitled_party=CommissionPartyReference(
                party_type=CommissionPartyType.BROKER,
                party_id="broker-001",
            ),
            deal_reference="deal-001",
            ownership_reference="ownership-001",
            provenance_reference="prov-001",
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
                rule_code="DEAL_ELIGIBLE",
                operator=EligibilityOperator.EQUALS,
                value="YES",
            ),
        ),
        effective_from=start,
        effective_to=end,
        contract_version=version,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference=f"mou-{version}",
            captured_at=start - timedelta(days=1),
            evidence_reference=f"evidence-{version}",
        ),
        state=CommissionContractState.ACTIVE,
    )


def test_history_requires_at_least_one_contract() -> None:
    with pytest.raises(
        Exception
    ):
        CommissionContractHistory(
            contracts=()
        )


def test_single_contract_is_valid_history() -> None:
    contract = build_contract(
        1,
        T1,
        None,
        "2.5",
    )

    history = CommissionContractHistory(
        contracts=(contract,)
    )

    assert history.identity_key == (
        "tenant-a",
        "commission-001",
    )

    assert history.version_numbers == (
        1,
    )

    assert history.latest is contract


def test_append_requires_next_version() -> None:
    first = build_contract(
        1,
        T1,
        T2,
        "2.5",
    )

    second = build_contract(
        2,
        T2,
        None,
        "3.0",
    )

    history = CommissionContractHistory(
        contracts=(first,)
    )

    updated = history.append(
        second
    )

    assert updated.version_numbers == (
        1,
        2,
    )


def test_append_rejects_version_gap() -> None:
    first = build_contract(
        1,
        T1,
        T2,
        "2.5",
    )

    invalid = build_contract(
        3,
        T2,
        None,
        "3.0",
    )

    history = CommissionContractHistory(
        contracts=(first,)
    )

    with pytest.raises(
        CommissionContractHistoryOrderError
    ):
        history.append(
            invalid
        )


def test_history_rejects_duplicate_versions() -> None:
    first = build_contract(
        1,
        T1,
        T2,
        "2.5",
    )

    duplicate = build_contract(
        1,
        T2,
        None,
        "3.0",
    )

    with pytest.raises(
        CommissionContractHistoryOrderError
    ):
        CommissionContractHistory(
            contracts=(
                first,
                duplicate,
            )
        )


def test_history_rejects_identity_mixing() -> None:
    first = build_contract(
        1,
        T1,
        T2,
        "2.5",
    )

    second = CommissionContract(
        commission_id="commission-002",
        tenant_id="tenant-a",
        entitlement=first.entitlement,
        basis=first.basis,
        rate=first.rate,
        eligibility_rules=(
            first.eligibility_rules
        ),
        effective_from=T2,
        effective_to=None,
        contract_version=2,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-2",
            captured_at=T2 - timedelta(days=1),
            evidence_reference="evidence-2",
        ),
        state=CommissionContractState.ACTIVE,
    )

    with pytest.raises(
        CommissionContractHistoryIdentityError
    ):
        CommissionContractHistory(
            contracts=(
                first,
                second,
            )
        )


def test_effective_lookup_is_deterministic() -> None:
    first = build_contract(
        1,
        T1,
        T2,
        "2.5",
    )

    second = build_contract(
        2,
        T2,
        T3,
        "3.0",
    )

    history = CommissionContractHistory(
        contracts=(
            first,
            second,
        )
    )

    assert history.effective_at(
        T1 + timedelta(days=10)
    ) is first

    assert history.effective_at(
        T2 + timedelta(days=10)
    ) is second


def test_history_rejects_overlapping_effective_windows() -> None:
    first = build_contract(
        1,
        T1,
        T3,
        "2.5",
    )

    second = build_contract(
        2,
        T2,
        None,
        "3.0",
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


def test_historical_terms_remain_distinct() -> None:
    first = build_contract(
        1,
        T1,
        T2,
        "2.5",
    )

    second = build_contract(
        2,
        T2,
        None,
        "3.0",
    )

    history = CommissionContractHistory(
        contracts=(
            first,
            second,
        )
    )

    assert (
        first.immutable_terms_fingerprint
        != second.immutable_terms_fingerprint
    )

    assert history.find_version(
        1
    ) is first

    assert history.find_version(
        2
    ) is second
