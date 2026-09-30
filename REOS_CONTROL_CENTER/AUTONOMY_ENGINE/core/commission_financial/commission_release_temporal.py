from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_closeout import CommissionCloseout
from .commission_release import CommissionRelease
from .commission_statement import CommissionStatement


class CommissionReleaseTemporalError(
    ValueError
):
    """Invalid release temporal relationship."""


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
        raise CommissionReleaseTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ReleaseTemporalWindow:
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
                raise CommissionReleaseTemporalError(
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


def assert_release_temporal_order(
    statement: CommissionStatement,
    closeout: CommissionCloseout | None,
    release: CommissionRelease,
) -> None:
    if release.evaluated_at < statement.generated_at:
        raise CommissionReleaseTemporalError(
            "Release evaluation cannot precede statement generation."
        )

    if (
        closeout is not None
        and closeout.closed_at is not None
        and release.evaluated_at < closeout.closed_at
    ):
        raise CommissionReleaseTemporalError(
            "Release evaluation cannot precede closeout."
        )

    if release.released_at is not None:
        if release.released_at < release.evaluated_at:
            raise CommissionReleaseTemporalError(
                "Release time cannot precede evaluation."
            )


__all__ = [
    "CommissionReleaseTemporalError",
    "ReleaseTemporalWindow",
    "assert_release_temporal_order",
]
