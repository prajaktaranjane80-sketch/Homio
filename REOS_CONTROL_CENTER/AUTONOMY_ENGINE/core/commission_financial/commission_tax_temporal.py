from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_invoice import CommissionInvoice
from .commission_tax import (
    CommissionTaxAssessment,
    CommissionTaxRuleReference,
)


class CommissionTaxTemporalError(
    ValueError
):
    """Invalid tax temporal relationship."""


def _normalize(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(
            value,
            datetime,
        )
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionTaxTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class TaxTemporalWindow:
    valid_from: datetime
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        start = _normalize(
            self.valid_from,
            "valid_from",
        )

        object.__setattr__(
            self,
            "valid_from",
            start,
        )

        if self.valid_to is not None:
            end = _normalize(
                self.valid_to,
                "valid_to",
            )

            if end <= start:
                raise CommissionTaxTemporalError(
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
        instant = _normalize(
            at,
            "at",
        )

        if instant < self.valid_from:
            return False

        return (
            self.valid_to is None
            or instant < self.valid_to
        )


def assert_tax_temporal_order(
    invoice: CommissionInvoice,
    assessment: CommissionTaxAssessment,
) -> None:
    if assessment.assessed_at < invoice.issued_at:
        raise CommissionTaxTemporalError(
            "Tax assessment cannot precede invoice issue."
        )

    for component in (
        assessment.tax_components
        + assessment.withholding_components
    ):
        if not component.rule.applies_at(
            assessment.assessed_at
        ):
            raise CommissionTaxTemporalError(
                "A tax rule is not effective at "
                "assessment time."
            )


def assert_rule_effective(
    rule: CommissionTaxRuleReference,
    at: datetime,
) -> None:
    if not rule.applies_at(at):
        raise CommissionTaxTemporalError(
            "Tax rule is not effective at supplied time."
        )


__all__ = [
    "CommissionTaxTemporalError",
    "TaxTemporalWindow",
    "assert_tax_temporal_order",
    "assert_rule_effective",
]
