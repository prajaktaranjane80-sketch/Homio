from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .financial_domain import MonetaryAmount


class CommissionCalculationBasisError(ValueError):
    """Invalid calculation-basis input."""


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionCalculationBasisError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionCalculationBasisError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionCalculationBasisError(
            f"{field} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class CommissionCalculationBasis:
    """Immutable source snapshot consumed by commission calculation.

    CORE-006 owns transaction/deal values.
    CORE-003 owns lead/customer ownership.
    CORE-008 records the exact financial input consumed.
    """

    basis_reference: str
    source_reference: str
    source_version: int
    captured_at: datetime
    amount: MonetaryAmount
    basis_code: str
    attributes: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "basis_reference",
            _text(
                self.basis_reference,
                "basis_reference",
            ),
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        object.__setattr__(
            self,
            "source_version",
            _positive(
                self.source_version,
                "source_version",
            ),
        )

        object.__setattr__(
            self,
            "captured_at",
            _aware(
                self.captured_at,
                "captured_at",
            ),
        )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise CommissionCalculationBasisError(
                "amount must be MonetaryAmount."
            )

        object.__setattr__(
            self,
            "basis_code",
            _text(
                self.basis_code,
                "basis_code",
            ),
        )

        attributes = (
            {}
            if self.attributes == ()
            else self.attributes
        )

        if not isinstance(
            attributes,
            Mapping,
        ):
            raise CommissionCalculationBasisError(
                "attributes must be a mapping."
            )

        object.__setattr__(
            self,
            "attributes",
            dict(attributes),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis_reference": self.basis_reference,
            "source_reference": self.source_reference,
            "source_version": self.source_version,
            "captured_at": self.captured_at.isoformat(),
            "amount": self.amount.to_dict(),
            "basis_code": self.basis_code,
            "attributes": dict(self.attributes),
        }


__all__ = [
    "CommissionCalculationBasis",
    "CommissionCalculationBasisError",
]
