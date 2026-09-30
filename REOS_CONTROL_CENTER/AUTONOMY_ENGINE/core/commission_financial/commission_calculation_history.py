from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_calculation import (
    CommissionCalculation,
)


class CommissionCalculationHistoryError(
    ValueError
):
    """Invalid calculation history transition."""


@dataclass(frozen=True, slots=True)
class CommissionCalculationHistoryEntry:
    """Immutable historical reference to one calculation version."""

    calculation_id: str
    tenant_id: str
    commission_id: str
    calculation_version: int
    calculation_fingerprint: str

    def __post_init__(self) -> None:
        if not self.calculation_id.strip():
            raise CommissionCalculationHistoryError(
                "calculation_id is required."
            )

        if not self.tenant_id.strip():
            raise CommissionCalculationHistoryError(
                "tenant_id is required."
            )

        if not self.commission_id.strip():
            raise CommissionCalculationHistoryError(
                "commission_id is required."
            )

        if self.calculation_version < 1:
            raise CommissionCalculationHistoryError(
                "calculation_version must be positive."
            )

        if not self.calculation_fingerprint.strip():
            raise CommissionCalculationHistoryError(
                "calculation_fingerprint is required."
            )

    @classmethod
    def from_calculation(
        cls,
        calculation: CommissionCalculation,
    ) -> "CommissionCalculationHistoryEntry":
        if not isinstance(
            calculation,
            CommissionCalculation,
        ):
            raise CommissionCalculationHistoryError(
                "calculation must be CommissionCalculation."
            )

        return cls(
            calculation_id=(
                calculation.calculation_id
            ),
            tenant_id=calculation.tenant_id,
            commission_id=(
                calculation.commission_id
            ),
            calculation_version=(
                calculation.calculation_version
            ),
            calculation_fingerprint=(
                calculation.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "calculation_id": (
                self.calculation_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "calculation_version": (
                self.calculation_version
            ),
            "calculation_fingerprint": (
                self.calculation_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionCalculationHistory:
    """Immutable ordered calculation history.

    This is a domain value container, not a database or event store.
    """

    entries: tuple[
        CommissionCalculationHistoryEntry,
        ...,
    ] = ()

    def append(
        self,
        calculation: CommissionCalculation,
    ) -> "CommissionCalculationHistory":
        entry = (
            CommissionCalculationHistoryEntry
            .from_calculation(calculation)
        )

        if self.entries:
            previous = self.entries[-1]

            if (
                previous.tenant_id
                != entry.tenant_id
                or previous.commission_id
                != entry.commission_id
            ):
                raise CommissionCalculationHistoryError(
                    "History identity mismatch."
                )

            if (
                entry.calculation_version
                != previous.calculation_version + 1
            ):
                raise CommissionCalculationHistoryError(
                    "Calculation history versions "
                    "must increase sequentially."
                )

        elif entry.calculation_version != 1:
            raise CommissionCalculationHistoryError(
                "First calculation history entry "
                "must have version 1."
            )

        return CommissionCalculationHistory(
            entries=(
                self.entries
                + (entry,)
            )
        )

    @property
    def latest(
        self,
    ) -> CommissionCalculationHistoryEntry | None:
        if not self.entries:
            return None

        return self.entries[-1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }


__all__ = [
    "CommissionCalculationHistoryError",
    "CommissionCalculationHistoryEntry",
    "CommissionCalculationHistory",
]
