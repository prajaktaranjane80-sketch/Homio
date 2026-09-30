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
from .commission_contract_temporal import (
    CommissionContractTemporalConflictError,
    EffectiveCommissionContract,
    resolve_effective_contract,
    validate_non_overlapping_terms,
)


UTC = timezone.utc


def make_contract(
    *,
    version: int,
    start: datetime,
    end: datetime | None,
    rate: str,
) -> CommissionContract:
    return CommissionContract(
        commission_id="commission-temporal",
        tenant_id="tenant-a",
        entitlement=CommissionEntitlementReference(
            entitlement_id="ent-temporal",
            tenant_id="tenant-a",
            entitled_party=CommissionPartyReference(
                CommissionPartyType.BROKER,
                "broker-temporal",
            ),
            deal_reference="deal-temporal",
            ownership_reference="ownership-temporal",
            provenance_reference="proof-temporal",
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
        effective_to=end,
        contract_version=version,
        provenance=CommissionProvenance(
            "MOU",
            f"mou-{version}",
            start - timedelta(days=1),
            f"evidence-{version}",
        ),
        state=CommissionContractState.ACTIVE,
    )


def test_temporal_resolution_returns_one_contract() -> None:
    first = make_contract(
        version=1,
        start=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
        end=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
        rate="2.5",
    )

    second = make_contract(
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

    result = resolve_effective_contract(
        (first, second),
        at=datetime(
            2026,
            9,
            20,
            tzinfo=UTC,
        ),
    )

    assert isinstance(
        result,
        EffectiveCommissionContract,
    )

    assert (
        result.contract.contract_version
        == 1
    )


def test_temporal_resolution_uses_second_version_after_boundary() -> None:
    first = make_contract(
        version=1,
        start=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
        end=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
        rate="2.5",
    )

    second = make_contract(
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

    result = resolve_effective_contract(
        (first, second),
        at=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
    )

    assert (
        result.contract.contract_version
        == 2
    )


def test_resolution_fails_when_no_contract_is_effective() -> None:
    contract = make_contract(
        version=1,
        start=datetime(
            2026,
            10,
            1,
            tzinfo=UTC,
        ),
        end=None,
        rate="2.5",
    )

    with pytest.raises(
        CommissionContractTemporalConflictError
    ):
        resolve_effective_contract(
            (contract,),
            at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )


def test_overlapping_terms_are_rejected() -> None:
    first = make_contract(
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
        rate="2.5",
    )

    second = make_contract(
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
        CommissionContractTemporalConflictError
    ):
        validate_non_overlapping_terms(
            (first, second)
        )


def test_different_commission_identities_can_have_same_window() -> None:
    first = make_contract(
        version=1,
        start=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
        end=None,
        rate="2.5",
    )

    second = CommissionContract(
        commission_id="different-commission",
        tenant_id=first.tenant_id,
        entitlement=first.entitlement,
        basis=first.basis,
        rate=first.rate,
        eligibility_rules=first.eligibility_rules,
        effective_from=first.effective_from,
        effective_to=first.effective_to,
        contract_version=1,
        provenance=first.provenance,
        state=first.state,
    )

    validate_non_overlapping_terms(
        (first, second)
    )
