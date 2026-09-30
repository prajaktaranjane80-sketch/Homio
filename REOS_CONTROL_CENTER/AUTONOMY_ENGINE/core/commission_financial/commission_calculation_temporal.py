from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_calculation import (
    CommissionCalculation,
)
from .commission_calculation_basis import (
    CommissionCalculationBasis,
)


class CommissionCalculationTemporalError(
    ValueError
):
    """Invalid temporal relationship."""


def _aware(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionCalculationTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def assert_temporal_consistency(
    basis: CommissionCalculationBasis,
    calculation: CommissionCalculation,
) -> None:
    """Ensure calculation never predates its consumed basis snapshot."""

    basis_time = _aware(
        basis.captured_at,
        "basis.captured_at",
    )

    calculation_time = _aware(
        calculation.calculated_at,
        "calculation.calculated_at",
    )

    if basis_time > calculation_time:
        raise CommissionCalculationTemporalError(
            "Calculation cannot precede the captured "
            "basis snapshot."
        )


@dataclass(frozen=True, slots=True)
class CalculationTemporalWindow:
    """Explicit half-open validity interval [valid_from, valid_to)."""

    valid_from: datetime
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        start = _aware(
            self.valid_from,
            "valid_from",
        )

        object.__setattr__(
            self,
            "valid_from",
            start,
        )

        if self.valid_to is not None:
            end = _aware(
                self.valid_to,
                "valid_to",
            )

            if end <= start:
                raise CommissionCalculationTemporalError(
                    "valid_to must be later than valid_from."
                )

            object.__setattr__(
                self,
                "valid_to",
                end,
            )

    def contains(
        self,
        at: datetime,
    ) -> bool:
        instant = _aware(
            at,
            "at",
        )

        if instant < self.valid_from:
            return False

        return (
            self.valid_to is None
            or instant < self.valid_to
        )


__all__ = [
    "CommissionCalculationTemporalError",
    "CalculationTemporalWindow",
    "assert_temporal_consistency",
]
