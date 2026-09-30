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
from .financial_domain import Currency


UTC = timezone.utc

START = datetime(
    2026,
    9,
    1,
    tzinfo=UTC,
)

END = datetime(
    2026,
    10,
    1,
    tzinfo=UTC,
)


def build_entitlement(
    tenant_id: str = "tenant-a",
) -> CommissionEntitlementReference:
    return CommissionEntitlementReference(
        entitlement_id="ent-001",
        tenant_id=tenant_id,
        entitled_party=CommissionPartyReference(
            party_type=CommissionPartyType.BROKER,
            party_id="broker-001",
        ),
        deal_reference="deal-001",
        ownership_reference="ownership-001",
        provenance_reference="provenance-001",
    )


def build_provenance() -> CommissionProvenance:
    return CommissionProvenance(
        source_type="BUILDER_MOU",
        source_reference="mou-001",
        captured_at=(
            START - timedelta(days=2)
        ),
        evidence_reference="evidence-001",
    )


def build_basis() -> CommissionBasis:
    return CommissionBasis(
        basis_type=(
            CommissionBasisType.GROSS_TRANSACTION_VALUE
        ),
        source_reference="deal.gross_value",
    )


def build_rate(
    value: str = "2.5",
) -> CommissionRate:
    return CommissionRate(
        rate_type=CommissionRateType.PERCENTAGE,
        value=value,
    )


def build_contract(
    **overrides,
) -> CommissionContract:
    values = {
        "commission_id": "commission-001",
        "tenant_id": "tenant-a",
        "entitlement": build_entitlement(),
        "basis": build_basis(),
        "rate": build_rate(),
        "eligibility_rules": (
            CommissionEligibilityRule(
                rule_code="DEAL_ELIGIBLE",
                operator=(
                    EligibilityOperator.EQUALS
                ),
                value="ELIGIBLE",
            ),
            CommissionEligibilityRule(
                rule_code="EVIDENCE_PRESENT",
                operator=(
                    EligibilityOperator.EXISTS
                ),
            ),
        ),
        "effective_from": START,
        "effective_to": END,
        "contract_version": 1,
        "provenance": build_provenance(),
        "state": CommissionContractState.ACTIVE,
        "metadata": {
            "source": "CORE-008-T02",
        },
    }

    values.update(overrides)

    return CommissionContract(
        **values
    )


def test_contract_identity_is_tenant_scoped() -> None:
    contract = build_contract()

    assert contract.identity_key == (
        "tenant-a",
        "commission-001",
    )

    with pytest.raises(
        CommissionContractTenantScopeError
    ):
        contract.assert_tenant(
            "tenant-b"
        )


def test_entitlement_tenant_must_match_contract() -> None:
    with pytest.raises(
        CommissionContractTenantScopeError
    ):
        build_contract(
            entitlement=build_entitlement(
                "tenant-b"
            )
        )


def test_percentage_rate_is_declarative() -> None:
    contract = build_contract()

    assert (
        contract.rate.rate_type
        is CommissionRateType.PERCENTAGE
    )

    assert str(
        contract.rate.value
    ) == "2.5"


def test_effective_window_is_half_open() -> None:
    contract = build_contract()

    assert not contract.is_effective_at(
        START - timedelta(seconds=1)
    )

    assert contract.is_effective_at(
        START
    )

    assert contract.is_effective_at(
        END - timedelta(microseconds=1)
    )

    assert not contract.is_effective_at(
        END
    )


def test_inactive_contract_is_not_effective() -> None:
    contract = build_contract(
        state=CommissionContractState.SUSPENDED
    )

    assert not contract.is_effective_at(
        START + timedelta(days=1)
    )


def test_contract_terms_are_immutable() -> None:
    contract = build_contract()

    with pytest.raises(
        FrozenInstanceError
    ):
        contract.rate = build_rate(
            "3.0"
        )  # type: ignore[misc]

    with pytest.raises(
        TypeError
    ):
        contract.metadata[
            "changed"
        ] = True  # type: ignore[index]


def test_same_identity_and_version_with_same_terms_is_compatible() -> None:
    first = build_contract()
    second = build_contract()

    assert (
        first.immutable_terms_fingerprint
        == second.immutable_terms_fingerprint
    )

    first.assert_compatible(
        second
    )


def test_same_identity_and_version_with_changed_terms_fails() -> None:
    first = build_contract()

    second = build_contract(
        rate=build_rate(
            "3.0"
        )
    )

    with pytest.raises(
        CommissionContractConflictError
    ):
        first.assert_compatible(
            second
        )


def test_new_version_preserves_identity() -> None:
    first = build_contract()

    second = first.next_version(
        basis=first.basis,
        rate=build_rate(
            "3.0"
        ),
        eligibility_rules=(
            first.eligibility_rules
        ),
        effective_from=END,
        effective_to=None,
        provenance=CommissionProvenance(
            source_type="BUILDER_MOU",
            source_reference="mou-002",
            captured_at=(
                END - timedelta(days=1)
            ),
            evidence_reference="evidence-002",
        ),
        state=CommissionContractState.DRAFT,
    )

    assert (
        second.commission_id
        == first.commission_id
    )

    assert (
        second.tenant_id
        == first.tenant_id
    )

    assert second.contract_version == 2

    assert (
        second.immutable_terms_fingerprint
        != first.immutable_terms_fingerprint
    )


@pytest.mark.parametrize(
    "rate_type,value,currency",
    [
        (
            CommissionRateType.PERCENTAGE,
            "100.01",
            None,
        ),
        (
            CommissionRateType.PERCENTAGE,
            "-0.1",
            None,
        ),
        (
            CommissionRateType.FIXED_AMOUNT,
            "10.00",
            None,
        ),
    ],
)
def test_invalid_rates_are_rejected(
    rate_type,
    value,
    currency,
) -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionRate(
            rate_type=rate_type,
            value=value,
            currency=currency,
        )


def test_fixed_amount_requires_currency() -> None:
    rate = CommissionRate(
        rate_type=(
            CommissionRateType.FIXED_AMOUNT
        ),
        value="5000.00",
        currency=Currency(
            "INR",
            2,
        ),
    )

    assert rate.currency.code == "INR"


def test_percentage_rate_rejects_currency() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionRate(
            rate_type=(
                CommissionRateType.PERCENTAGE
            ),
            value="2.5",
            currency=Currency(
                "USD",
                2,
            ),
        )


def test_fixed_amount_basis_requires_currency() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionBasis(
            basis_type=(
                CommissionBasisType.FIXED_TRANSACTION_AMOUNT
            ),
            source_reference="transaction.fixed",
        )


def test_fixed_amount_basis_accepts_currency() -> None:
    basis = CommissionBasis(
        basis_type=(
            CommissionBasisType.FIXED_TRANSACTION_AMOUNT
        ),
        source_reference="transaction.fixed",
        currency=Currency(
            "INR",
            2,
        ),
    )

    assert basis.currency.code == "INR"


def test_eligibility_rule_is_declarative() -> None:
    exists_rule = CommissionEligibilityRule(
        rule_code="EVIDENCE_PRESENT",
        operator=EligibilityOperator.EXISTS,
    )

    equals_rule = CommissionEligibilityRule(
        rule_code="DEAL_STATE",
        operator=EligibilityOperator.EQUALS,
        value="CLOSED",
    )

    assert exists_rule.value is None
    assert equals_rule.value == "CLOSED"


def test_exists_rule_cannot_have_value() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionEligibilityRule(
            rule_code="EVIDENCE_PRESENT",
            operator=EligibilityOperator.EXISTS,
            value="TRUE",
        )


def test_non_exists_rule_requires_value() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        CommissionEligibilityRule(
            rule_code="DEAL_STATE",
            operator=EligibilityOperator.EQUALS,
        )


def test_duplicate_eligibility_codes_are_rejected() -> None:
    rule = CommissionEligibilityRule(
        rule_code="DEAL_STATE",
        operator=EligibilityOperator.EQUALS,
        value="CLOSED",
    )

    with pytest.raises(
        CommissionContractValidationError
    ):
        build_contract(
            eligibility_rules=(
                rule,
                rule,
            )
        )


def test_effective_to_must_follow_effective_from() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        build_contract(
            effective_to=START
        )


def test_provenance_cannot_be_after_effective_start() -> None:
    with pytest.raises(
        CommissionContractValidationError
    ):
        build_contract(
            provenance=CommissionProvenance(
                source_type="BUILDER_MOU",
                source_reference="invalid-mou",
                captured_at=(
                    START + timedelta(days=1)
                ),
                evidence_reference="invalid-evidence",
            )
        )


def test_same_terms_have_deterministic_fingerprint() -> None:
    first = build_contract()
    second = build_contract()

    assert (
        first.immutable_terms_fingerprint
        == second.immutable_terms_fingerprint
    )

    assert (
        first.to_dict(
            include_fingerprint=False
        )
        == second.to_dict(
            include_fingerprint=False
        )
    )


def test_contract_does_not_create_duplicate_authorities() -> None:
    payload = build_contract().to_dict()

    assert (
        payload["source_of_truth"]
        == "CORE-008.COMMISSION_CONTRACT"
    )

    assert "control_center_state" not in payload
    assert "ownership_engine" not in payload
    assert "event_bus" not in payload
    assert "fraud_engine" not in payload
    assert "authorization_engine" not in payload
    assert "acrL_engine" not in payload
