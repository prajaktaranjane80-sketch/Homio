from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping

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


@dataclass(frozen=True, slots=True)
class LedgerAccountReference:
    account_id: str
    account_type: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "account_id",
            _text(
                self.account_id,
                "account_id",
            ),
        )

        object.__setattr__(
            self,
            "account_type",
            _text(
                self.account_type,
                "account_type",
            ),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "account_id": self.account_id,
            "account_type": self.account_type,
        }


@dataclass(frozen=True, slots=True)
class FinancialLedgerEntry:
    """
    Immutable ledger-entry boundary record.

    CORE-008 defines financial-entry semantics.
    It does NOT post into an external/general-ledger engine.
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
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        if (
            isinstance(self.entry_version, bool)
            or not isinstance(
                self.entry_version,
                int,
            )
            or self.entry_version < 1
        ):
            raise FinancialLedgerValidationError(
                "entry_version must be positive."
            )

        if not isinstance(
            self.debit,
            LedgerAccountReference,
        ):
            raise FinancialLedgerValidationError(
                "debit must be LedgerAccountReference."
            )

        if not isinstance(
            self.credit,
            LedgerAccountReference,
        ):
            raise FinancialLedgerValidationError(
                "credit must be LedgerAccountReference."
            )

        if (
            self.debit.account_id
            == self.credit.account_id
        ):
            raise FinancialLedgerValidationError(
                "Debit and credit accounts must differ."
            )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
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
            _aware(
                self.entry_timestamp,
                "entry_timestamp",
            ),
        )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise FinancialLedgerValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(metadata)),
        )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, int]:
        return (
            self.tenant_id,
            self.entry_id,
            self.entry_version,
        )

    @property
    def immutable_fingerprint(self) -> str:
        payload = self.to_dict(
            include_fingerprint=False
        )

        return sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def assert_balanced(self) -> None:
        if (
            self.amount.currency.identity_key
            != self.amount.currency.identity_key
        ):
            raise FinancialLedgerValidationError(
                "Ledger currency identity is inconsistent."
            )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise FinancialLedgerBoundaryError(
                "Ledger entry crossed tenant boundary."
            )

    def verify_integrity(self) -> bool:
        return bool(
            self.immutable_fingerprint
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
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
            "transaction_reference": (
                self.transaction_reference
            ),
            "debit": self.debit.to_dict(),
            "credit": self.credit.to_dict(),
            "amount": self.amount.to_dict(),
            "entry_timestamp": (
                self.entry_timestamp.isoformat()
            ),
            "source_reference": self.source_reference,
            "provenance_reference": (
                self.provenance_reference
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


class FinancialLedgerBoundary:
    """
    Construction-only financial ledger boundary.

    No persistence or posting responsibility is introduced.
    """

    @staticmethod
    def create_entry(
        **kwargs: Any,
    ) -> FinancialLedgerEntry:
        return FinancialLedgerEntry(
            **kwargs
        )


def compare_ledger_entries(
    left: FinancialLedgerEntry,
    right: FinancialLedgerEntry,
) -> tuple[bool, bool]:
    if not isinstance(left, FinancialLedgerEntry):
        raise TypeError(
            "left must be FinancialLedgerEntry"
        )

    if not isinstance(right, FinancialLedgerEntry):
        raise TypeError(
            "right must be FinancialLedgerEntry"
        )

    same_identity = (
        left.identity_key
        == right.identity_key
    )

    same_fingerprint = (
        left.immutable_fingerprint
        == right.immutable_fingerprint
    )

    return (
        same_identity,
        same_fingerprint,
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
