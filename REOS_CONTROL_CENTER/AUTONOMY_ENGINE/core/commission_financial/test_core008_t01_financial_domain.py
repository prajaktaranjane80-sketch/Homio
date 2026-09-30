"""CORE-008 T01 — Financial Domain adversarial regression."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from .financial_domain import (
    Currency,
    FinancialCurrencyMismatchError,
    FinancialDomainRecord,
    FinancialIdentity,
    FinancialPrecisionError,
    FinancialState,
    FinancialSubject,
    FinancialSubjectType,
    FinancialTenantScopeError,
    FinancialValidationError,
    MonetaryAmount,
    RoundingMode,
    new_financial_identity,
)


def usd() -> Currency:
    return Currency("USD", 2)


def inr() -> Currency:
    return Currency("INR", 2)


def test_currency_is_immutable_and_explicitly_scoped() -> None:
    value = usd()

    assert value.code == "USD"
    assert value.minor_unit == 2
    assert value.rounding_mode is RoundingMode.HALF_EVEN
    assert value.quantum == Decimal("0.01")

    with pytest.raises(FrozenInstanceError):
        value.code = "EUR"  # type: ignore[misc]


@pytest.mark.parametrize(
    "code",
    ["US", "USDT", "", "usd1", "12A"],
)
def test_currency_rejects_invalid_identity(code: str) -> None:
    with pytest.raises(FinancialValidationError):
        Currency(code, 2)


@pytest.mark.parametrize(
    "minor_unit",
    [-1, 7, True, "2"],
)
def test_currency_rejects_invalid_precision(minor_unit) -> None:
    with pytest.raises(FinancialValidationError):
        Currency("USD", minor_unit)


def test_monetary_amount_uses_decimal_and_deterministic_rounding() -> None:
    value = MonetaryAmount.create(
        "10.005",
        usd(),
    )

    assert value.amount == Decimal("10.00")
    assert value.to_dict()["amount"] == "10.00"
    assert value.as_minor_units == 1000

    upward = MonetaryAmount.create(
        "10.005",
        Currency(
            "USD",
            2,
            RoundingMode.HALF_UP,
        ),
    )

    assert upward.amount == Decimal("10.01")


def test_binary_float_is_rejected_at_financial_boundary() -> None:
    with pytest.raises(FinancialValidationError):
        MonetaryAmount.create(
            10.25,
            usd(),
        )  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    ["NaN", "Infinity", "-Infinity"],
)
def test_non_finite_amount_is_rejected(
    value: str,
) -> None:
    with pytest.raises(FinancialValidationError):
        MonetaryAmount.create(
            value,
            usd(),
        )


def test_currency_mismatch_is_fail_closed() -> None:
    usd_value = MonetaryAmount.create(
        "100.00",
        usd(),
    )
    inr_value = MonetaryAmount.create(
        "100.00",
        inr(),
    )

    with pytest.raises(FinancialCurrencyMismatchError):
        usd_value.add(inr_value)

    with pytest.raises(FinancialCurrencyMismatchError):
        usd_value.subtract(inr_value)


def test_money_arithmetic_is_immutable() -> None:
    base = MonetaryAmount.create(
        "100.00",
        usd(),
    )
    fee = MonetaryAmount.create(
        "10.25",
        usd(),
    )

    result = base.subtract(fee)

    assert base.amount == Decimal("100.00")
    assert fee.amount == Decimal("10.25")
    assert result.amount == Decimal("89.75")


def test_financial_subject_is_typed_and_versioned() -> None:
    subject = FinancialSubject(
        subject_type=FinancialSubjectType.COMMISSION,
        subject_id="commission-001",
        subject_version=3,
    )

    assert subject.identity_key == (
        "COMMISSION",
        "commission-001",
    )
    assert subject.subject_version == 3

    with pytest.raises(FinancialValidationError):
        FinancialSubject(
            subject_type=FinancialSubjectType.COMMISSION,
            subject_id="",
        )


def test_financial_identity_is_tenant_scoped_and_immutable() -> None:
    identity = new_financial_identity(
        tenant_id="tenant-a",
        subject_type=FinancialSubjectType.COMMISSION,
        subject_id="commission-001",
    )

    assert identity.identity_key[0] == "tenant-a"
    assert len(identity.immutable_fingerprint) == 64

    with pytest.raises(FinancialTenantScopeError):
        identity.assert_tenant("tenant-b")

    with pytest.raises(FrozenInstanceError):
        identity.financial_id = "replacement"  # type: ignore[misc]


def test_same_identity_produces_stable_fingerprint_and_identity_key() -> None:
    subject = FinancialSubject(
        FinancialSubjectType.COMMISSION,
        "commission-001",
        1,
    )

    first = FinancialIdentity(
        financial_id="fin-001",
        tenant_id="tenant-a",
        subject=subject,
    )
    second = FinancialIdentity(
        financial_id="fin-001",
        tenant_id="tenant-a",
        subject=subject,
    )

    assert first.identity_key == second.identity_key
    assert (
        first.immutable_fingerprint
        == second.immutable_fingerprint
    )


def test_financial_record_is_immutable_and_tenant_scoped() -> None:
    identity = FinancialIdentity(
        financial_id="fin-001",
        tenant_id="tenant-a",
        subject=FinancialSubject(
            FinancialSubjectType.COMMISSION,
            "commission-001",
        ),
    )

    record = FinancialDomainRecord(
        identity=identity,
        state=FinancialState.ACTIVE,
        amount=MonetaryAmount.create(
            "100.00",
            usd(),
        ),
        metadata={
            "source": "T01",
            "approved": False,
        },
    )

    assert record.state is FinancialState.ACTIVE
    assert record.tenant_id == "tenant-a"
    assert record.financial_id == "fin-001"
    assert len(record.immutable_fingerprint) == 64

    with pytest.raises(FinancialTenantScopeError):
        record.assert_tenant("tenant-b")

    with pytest.raises(FrozenInstanceError):
        record.state = FinancialState.SETTLED  # type: ignore[misc]


def test_financial_record_metadata_is_immutable() -> None:
    identity = FinancialIdentity(
        financial_id="fin-001",
        tenant_id="tenant-a",
        subject=FinancialSubject(
            FinancialSubjectType.COMMISSION,
            "commission-001",
        ),
    )

    record = FinancialDomainRecord(
        identity=identity,
        metadata={
            "origin": "lead-001",
            "attempt": 1,
            "approved": False,
        },
    )

    assert dict(record.metadata) == {
        "origin": "lead-001",
        "attempt": 1,
        "approved": False,
    }

    with pytest.raises(TypeError):
        record.metadata["origin"] = "changed"  # type: ignore[index]


def test_financial_record_does_not_accept_nested_state() -> None:
    identity = FinancialIdentity(
        financial_id="fin-001",
        tenant_id="tenant-a",
        subject=FinancialSubject(
            FinancialSubjectType.COMMISSION,
            "commission-001",
        ),
    )

    with pytest.raises(FinancialValidationError):
        FinancialDomainRecord(
            identity=identity,
            metadata={
                "nested": {
                    "forbidden": True,
                },
            },
        )


def test_new_identity_generates_unique_financial_ids() -> None:
    first = new_financial_identity(
        tenant_id="tenant-a",
        subject_type=FinancialSubjectType.COMMISSION,
        subject_id="commission-001",
    )
    second = new_financial_identity(
        tenant_id="tenant-a",
        subject_type=FinancialSubjectType.COMMISSION,
        subject_id="commission-001",
    )

    assert first.financial_id != second.financial_id
    assert first.identity_key != second.identity_key


def test_precision_guard_has_distinct_error_boundary() -> None:
    with pytest.raises(FinancialPrecisionError):
        MonetaryAmount.create(
            "9" * 10000,
            usd(),
        )