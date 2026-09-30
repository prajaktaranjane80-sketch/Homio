from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_closeout import CommissionCloseout
from .commission_statement import CommissionStatement


class CommissionStatementTemporalError(
    ValueError
):
    """Invalid statement temporal relationship."""


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
        raise CommissionStatementTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class StatementTemporalWindow:
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
                raise CommissionStatementTemporalError(
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


def assert_closeout_after_statement(
    statement: CommissionStatement,
    closeout: CommissionCloseout,
    *,
    statement_generated_at: datetime | None = None,
) -> None:
    reference_time = (
        statement.generated_at
        if statement_generated_at is None
        else _normalize(
            statement_generated_at,
            "statement_generated_at",
        )
    )

    if closeout.closed_at is not None:
        if closeout.closed_at < reference_time:
            raise CommissionStatementTemporalError(
                "Closeout cannot predate statement generation."
            )


__all__ = [
    "CommissionStatementTemporalError",
    "StatementTemporalWindow",
    "assert_closeout_after_statement",
]
