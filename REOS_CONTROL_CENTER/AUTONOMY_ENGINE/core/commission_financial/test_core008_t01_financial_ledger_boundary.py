
"""CORE-008 T01 — Financial ledger boundary regression tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import pytest

from . import compare_ledger_entries as public_compare_ledger_entries
from .financial_domain import Currency, MonetaryAmount
from .financial_ledger_boundary import (
    FinancialLedgerBoundary,
    FinancialLedgerBoundaryError,
    FinancialLedgerEntry,
    FinancialLedgerValidationError,
    LedgerAccountReference,
    compare_ledger_entries,
)


def make_entry(
    *,
    entry_id: str = "entry-001",
    tenant_id: str = "tenant-001",
    amount: str = "125.50",
    debit_account_id: str = "cash-account",
    credit_account_id: str = "commission-payable",
    metadata: Mapping[str, Any] | None = None,
) -> FinancialLedgerEntry:
    return FinancialLedgerBoundary.create_entry(
        entry_id=entry_id,
        tenant_id=tenant_id,
        commission_id="commission-001",
        entry_version=1,
        transaction_reference="txn-001",
        debit=LedgerAccountReference(
            account_id=debit_account_id,
            account_type="ASSET",
        ),
        credit=LedgerAccountReference(
            account_id=credit_account_id,
            account_type="LIABILITY",
        ),
        amount=MonetaryAmount.create(
            amount,
            Currency("USD", 2),
        ),
        entry_timestamp=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        source_reference="test-source",
        provenance_reference="test-provenance",
        metadata={} if metadata is None else metadata,
    )


def test_nested_metadata_is_deeply_immutable() -> None:
    source = {
        "evidence": {
            "ids": [
                "evidence-001",
                {"origin": "verified-source"},
            ],
        },
    }

    entry = make_entry(metadata=source)
    original_fingerprint = entry.immutable_fingerprint

    source["evidence"]["ids"][0] = "changed-outside"
    source["evidence"]["ids"][1]["origin"] = "changed-outside"

    assert entry.metadata["evidence"]["ids"][0] == "evidence-001"
    assert (
        entry.metadata["evidence"]["ids"][1]["origin"]
        == "verified-source"
    )

    with pytest.raises(TypeError):
        entry.metadata["evidence"]["ids"][0] = "changed-inside"

    with pytest.raises(TypeError):
        entry.metadata["evidence"]["ids"][1]["origin"] = "changed-inside"

    assert entry.immutable_fingerprint == original_fingerprint
    assert entry.verify_integrity() is True


def test_serialization_returns_detached_metadata() -> None:
    entry = make_entry(
        metadata={
            "evidence": {
                "ids": ["evidence-001"],
            },
        }
    )
    original_fingerprint = entry.immutable_fingerprint

    exported = entry.to_dict()
    exported["metadata"]["evidence"]["ids"][0] = "modified-export"

    assert entry.metadata["evidence"]["ids"][0] == "evidence-001"
    assert entry.immutable_fingerprint == original_fingerprint
    assert entry.verify_integrity() is True


def test_metadata_rejects_non_json_compatible_values() -> None:
    with pytest.raises(
        FinancialLedgerValidationError,
        match="JSON-compatible",
    ):
        make_entry(
            metadata={
                "unsupported": object(),
            }
        )


def test_metadata_rejects_non_string_nested_keys() -> None:
    with pytest.raises(FinancialLedgerValidationError):
        make_entry(
            metadata={
                "nested": {
                    123: "not-a-string-key",
                },
            }
        )


def test_same_debit_and_credit_account_is_rejected() -> None:
    with pytest.raises(
        FinancialLedgerValidationError,
        match="accounts must differ",
    ):
        make_entry(
            debit_account_id="same-account",
            credit_account_id="same-account",
        )


def test_zero_or_negative_ledger_amount_is_rejected() -> None:
    for amount in ("0", "-1.00"):
        with pytest.raises(
            FinancialLedgerValidationError,
            match="greater than zero",
        ):
            make_entry(amount=amount)


def test_entry_structural_balance_check_succeeds() -> None:
    entry = make_entry()

    assert entry.assert_balanced() is None
    assert entry.verify_integrity() is True


def test_integrity_verification_detects_post_construction_tampering() -> None:
    entry = make_entry()
    original_fingerprint = entry.immutable_fingerprint

    assert entry.verify_integrity() is True

    # Adversarially simulate a field change that bypasses ordinary
    # frozen-dataclass assignment. Integrity verification must detect it.
    object.__setattr__(
        entry,
        "source_reference",
        "tampered-source",
    )

    assert entry.immutable_fingerprint != original_fingerprint
    assert entry.verify_integrity() is False


def test_tenant_boundary_fails_closed() -> None:
    entry = make_entry(tenant_id="tenant-a")

    entry.assert_tenant("tenant-a")

    with pytest.raises(
        FinancialLedgerBoundaryError,
        match="tenant boundary",
    ):
        entry.assert_tenant("tenant-b")


def test_entry_comparison_separates_identity_and_content() -> None:
    first = make_entry(
        entry_id="entry-same",
        metadata={"source": "approved"},
    )
    same = make_entry(
        entry_id="entry-same",
        metadata={"source": "approved"},
    )
    changed = make_entry(
        entry_id="entry-same",
        metadata={"source": "changed"},
    )

    assert compare_ledger_entries(first, same) == (True, True)
    assert compare_ledger_entries(first, changed) == (True, False)


def test_ledger_comparison_is_available_from_package_public_api() -> None:
    first = make_entry(entry_id="public-entry")
    second = make_entry(entry_id="public-entry")

    assert public_compare_ledger_entries(first, second) == (True, True)


def test_invalid_comparison_operand_is_rejected() -> None:
    entry = make_entry()

    with pytest.raises(TypeError, match="left must be FinancialLedgerEntry"):
        compare_ledger_entries(object(), entry)  # type: ignore[arg-type]
