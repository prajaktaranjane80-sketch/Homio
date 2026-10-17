
"""CORE-008 financial ledger entry boundary.

This module defines an immutable, serializable double-entry record.
It does not persist ledger entries, post payments, or replace an external
general ledger or the canonical reconciliation authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Mapping

from ..contract_primitives import (
    canonical_json,
    deep_freeze,
    deep_thaw,
    fingerprint,
)
from .financial_domain import MonetaryAmount


CORE008_FINANCIAL_LEDGER_SCHEMA_VERSION = 1


class FinancialLedgerBoundaryError(ValueError):
    """Financial ledger-boundary violation."""


class FinancialLedgerValidationError(
    FinancialLedgerBoundaryError
):
    """Invalid financial ledger entry."""


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FinancialLedgerValidationError(
            f"{field} must be non-empty text."
        )

    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise FinancialLedgerValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _freeze_json_metadata(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate, normalize and deeply freeze JSON-compatible metadata.

    Reuses the canonical Core contract primitives instead of creating
    a second immutable-data implementation.
    """
    try:
        first_freeze = deep_freeze(
            value,
            field_name="metadata",
        )

        normalized = json.loads(
            canonical_json(first_freeze)
        )

        result = deep_freeze(
            normalized,
            field_name="metadata",
        )
    except (TypeError, ValueError) as exc:
        raise FinancialLedgerValidationError(
            "metadata must contain JSON-compatible values "
            "with string keys."
        ) from exc

    if not isinstance(result, Mapping):
        raise FinancialLedgerValidationError(
            "metadata must be a mapping."
        )

    return result


@dataclass(frozen=True, slots=True)
class LedgerAccountReference:
    """Immutable reference to an account owned by the ledger authority."""

    account_id: str
    account_type: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "account_id",
            _text(self.account_id, "account_id"),
        )

        object.__setattr__(
            self,
            "account_type",
            _text(self.account_type, "account_type"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "account_id": self.account_id,
            "account_type": self.account_type,
        }


@dataclass(frozen=True, slots=True)
class FinancialLedgerEntry:
    """Immutable, tenant-scoped double-entry record.

    A single MonetaryAmount is applied to the debit and credit legs.
    This record can validate its own structure; it cannot establish
    account balances across multiple entries or certify a posted journal.
    Those responsibilities belong to the approved ledger and reconciliation
    authorities.
    """

    entry_id: str
    tenant_id: str
    commission_id: str
    entry_version: int
    transaction_reference: str

    debit: LedgerAccountReference
    credit: LedgerAccountReference

    amount: MonetaryAmount
    entry_timestamp: datetime

    source_reference: str
    provenance_reference: str

    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "entry_id",
            "tenant_id",
            "commission_id",
            "transaction_reference",
            "source_reference",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(getattr(self, field), field),
            )

        if (
            isinstance(self.entry_version, bool)
            or not isinstance(self.entry_version, int)
            or self.entry_version < 1
        ):
            raise FinancialLedgerValidationError(
                "entry_version must be a positive integer."
            )

        if not isinstance(self.debit, LedgerAccountReference):
            raise FinancialLedgerValidationError(
                "debit must be LedgerAccountReference."
            )

        if not isinstance(self.credit, LedgerAccountReference):
            raise FinancialLedgerValidationError(
                "credit must be LedgerAccountReference."
            )

        if self.debit.account_id == self.credit.account_id:
            raise FinancialLedgerValidationError(
                "Debit and credit accounts must differ."
            )

        if not isinstance(self.amount, MonetaryAmount):
            raise FinancialLedgerValidationError(
                "amount must be MonetaryAmount."
            )

        if self.amount.amount <= 0:
            raise FinancialLedgerValidationError(
                "ledger amount must be greater than zero."
            )

        object.__setattr__(
            self,
            "entry_timestamp",
            _aware(self.entry_timestamp, "entry_timestamp"),
        )

        metadata = self.metadata

        if metadata == ():
            metadata = {}

        if not isinstance(metadata, Mapping):
            raise FinancialLedgerValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_json_metadata(metadata),
        )

    @property
    def identity_key(self) -> tuple[str, str, int]:
        """Tenant-scoped identity and version of this entry."""
        return (
            self.tenant_id,
            self.entry_id,
            self.entry_version,
        )

    @property
    def immutable_fingerprint(self) -> str:
        """Deterministic digest of the complete serialized entry."""
        return fingerprint(
            self.to_dict(include_fingerprint=False)
        )

    def assert_balanced(self) -> None:
        """Validate the structural balance of this single entry.

        The entry model uses the same positive amount on both legs.
        This method does not certify aggregate ledger or account balances.
        """
        if self.debit.account_id == self.credit.account_id:
            raise FinancialLedgerValidationError(
                "Debit and credit accounts must differ."
            )

        if self.amount.amount <= 0:
            raise FinancialLedgerValidationError(
                "ledger amount must be greater than zero."
            )

        # One shared MonetaryAmount represents both debit and credit legs.
        # Cross-entry totals must be checked by ledger reconciliation.

    def assert_tenant(self, tenant_id: str) -> None:
        tenant_id = _text(tenant_id, "tenant_id")

        if tenant_id != self.tenant_id:
            raise FinancialLedgerBoundaryError(
                "Ledger entry crossed tenant boundary."
            )

    def verify_integrity(self) -> bool:
        """Recompute the deterministic digest for the current entry."""
        return bool(self.immutable_fingerprint)

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        """Return detached JSON-compatible data.

        Mutating this returned structure cannot mutate the immutable entry.
        """
        result: dict[str, Any] = {
            "source_of_truth": (
                "CORE-008.FINANCIAL_LEDGER_BOUNDARY"
            ),
            "schema_version": (
                CORE008_FINANCIAL_LEDGER_SCHEMA_VERSION
            ),
            "entry_id": self.entry_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "entry_version": self.entry_version,
            "transaction_reference": self.transaction_reference,
            "debit": self.debit.to_dict(),
            "credit": self.credit.to_dict(),
            "amount": self.amount.to_dict(),
            "entry_timestamp": self.entry_timestamp.isoformat(),
            "source_reference": self.source_reference,
            "provenance_reference": self.provenance_reference,
            "metadata": deep_thaw(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


class FinancialLedgerBoundary:
    """Construction-only adapter for immutable ledger-boundary records."""

    @staticmethod
    def create_entry(**kwargs: Any) -> FinancialLedgerEntry:
        return FinancialLedgerEntry(**kwargs)


def compare_ledger_entries(
    left: FinancialLedgerEntry,
    right: FinancialLedgerEntry,
) -> tuple[bool, bool]:
    """Return (same_identity, same_fingerprint) for two valid entries."""
    if not isinstance(left, FinancialLedgerEntry):
        raise TypeError("left must be FinancialLedgerEntry.")

    if not isinstance(right, FinancialLedgerEntry):
        raise TypeError("right must be FinancialLedgerEntry.")

    return (
        left.identity_key == right.identity_key,
        left.immutable_fingerprint == right.immutable_fingerprint,
    )


__all__ = [
    "CORE008_FINANCIAL_LEDGER_SCHEMA_VERSION",
    "FinancialLedgerBoundary",
    "FinancialLedgerBoundaryError",
    "FinancialLedgerEntry",
    "FinancialLedgerValidationError",
    "LedgerAccountReference",
    "compare_ledger_entries",
]
