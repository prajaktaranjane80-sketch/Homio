"""
CORE-005 / Point 07 — Search / Match Consistency.

Owns:
- source-version tracking
- projection-lag detection
- stale-result detection
- duplicate-event handling
- out-of-order update handling
- deterministic consistency evaluation
- eventual-consistency disclosure

Does NOT own:
- event bus
- search backend
- ranking
- matching
- inventory source truth
- Control Center state
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class SearchConsistencyError(ValueError):
    """Base consistency error."""


class SearchConsistencyVersionError(
    SearchConsistencyError
):
    """Raised for invalid versions."""


class SearchConsistencyTenantError(
    SearchConsistencyError
):
    """Raised for tenant mismatch."""


class ConsistencyStatus(str, Enum):
    """
    Explicit consistency state.
    """

    CURRENT = "CURRENT"
    LAGGING = "LAGGING"
    STALE = "STALE"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CONFLICT = "CONFLICT"


def _positive_version(
    value: int,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise SearchConsistencyVersionError(
            f"{field_name} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class ConsistencyVersionState:
    """
    Version state for one tenant/index identity.
    """

    tenant_id: str
    index_key: str
    source_version: int
    projection_version: int

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.tenant_id,
                str,
            )
            or not self.tenant_id.strip()
        ):
            raise SearchConsistencyTenantError(
                "tenant_id must be non-empty."
            )

        if (
            not isinstance(
                self.index_key,
                str,
            )
            or not self.index_key.strip()
        ):
            raise SearchConsistencyError(
                "index_key must be non-empty."
            )

        object.__setattr__(
            self,
            "source_version",
            _positive_version(
                self.source_version,
                "source_version",
            ),
        )

        object.__setattr__(
            self,
            "projection_version",
            _positive_version(
                self.projection_version,
                "projection_version",
            ),
        )

    @property
    def lag(self) -> int:
        return max(
            0,
            self.source_version
            - self.projection_version,
        )

    @property
    def is_current(self) -> bool:
        return self.lag == 0

    @property
    def is_lagging(self) -> bool:
        return self.lag > 0


@dataclass(frozen=True, slots=True)
class ConsistencyEvaluation:
    """
    Explicit consistency disclosure for downstream consumers.
    """

    status: ConsistencyStatus
    tenant_id: str
    index_key: str
    source_version: int
    projection_version: int
    lag: int
    stale: bool
    message: str

    @property
    def result_eligible(self) -> bool:
        """
        Conservative result exposure decision.

        Current data is eligible.
        Stale/conflicting data is not automatically eligible.

        This is not an authorization engine.
        """
        return self.status is ConsistencyStatus.CURRENT


@dataclass(frozen=True, slots=True)
class ConsistencyEvent:
    """
    Lightweight consistency event record.

    It is not an event bus implementation.
    """

    event_id: str
    tenant_id: str
    index_key: str
    source_version: int

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.event_id,
                str,
            )
            or not self.event_id.strip()
        ):
            raise SearchConsistencyError(
                "event_id must be non-empty."
            )

        if (
            not isinstance(
                self.tenant_id,
                str,
            )
            or not self.tenant_id.strip()
        ):
            raise SearchConsistencyTenantError(
                "tenant_id must be non-empty."
            )

        if (
            not isinstance(
                self.index_key,
                str,
            )
            or not self.index_key.strip()
        ):
            raise SearchConsistencyError(
                "index_key must be non-empty."
            )

        object.__setattr__(
            self,
            "source_version",
            _positive_version(
                self.source_version,
                "source_version",
            ),
        )


@dataclass(slots=True)
class SearchConsistencyTracker:
    """
    Tracks only search-projection consistency metadata.

    Source truth remains outside this class.
    """

    _states: dict[
        tuple[str, str],
        ConsistencyVersionState
    ]
    _events: set[str]

    def __init__(self) -> None:
        self._states = {}
        self._events = set()

    def observe_event(
        self,
        event: ConsistencyEvent,
    ) -> ConsistencyStatus:
        if not isinstance(
            event,
            ConsistencyEvent,
        ):
            raise SearchConsistencyError(
                "event must be ConsistencyEvent."
            )

        if event.event_id in self._events:
            return ConsistencyStatus.DUPLICATE

        key = (
            event.tenant_id,
            event.index_key,
        )

        current = self._states.get(key)

        if current is not None:
            if (
                event.source_version
                < current.source_version
            ):
                self._events.add(
                    event.event_id
                )

                return ConsistencyStatus.OUT_OF_ORDER

            if (
                event.source_version
                == current.source_version
            ):
                self._events.add(
                    event.event_id
                )

                return ConsistencyStatus.CONFLICT

        self._events.add(
            event.event_id
        )

        projection_version = (
            current.projection_version
            if current is not None
            else event.source_version
        )

        self._states[key] = (
            ConsistencyVersionState(
                tenant_id=event.tenant_id,
                index_key=event.index_key,
                source_version=event.source_version,
                projection_version=projection_version,
            )
        )

        return ConsistencyStatus.CURRENT

    def mark_projected(
        self,
        *,
        tenant_id: str,
        index_key: str,
        projection_version: int,
    ) -> None:
        projection_version = _positive_version(
            projection_version,
            "projection_version",
        )

        key = (
            tenant_id,
            index_key,
        )

        current = self._states.get(key)

        if current is None:
            self._states[key] = (
                ConsistencyVersionState(
                    tenant_id=tenant_id,
                    index_key=index_key,
                    source_version=projection_version,
                    projection_version=projection_version,
                )
            )

            return

        if (
            tenant_id
            != current.tenant_id
        ):
            raise SearchConsistencyTenantError(
                "Tenant mismatch in projection state."
            )

        if (
            projection_version
            < current.projection_version
        ):
            raise SearchConsistencyVersionError(
                "Projection version cannot move backwards."
            )

        if (
            projection_version
            > current.source_version
        ):
            raise SearchConsistencyVersionError(
                "Projection version cannot exceed known "
                "source version."
            )

        self._states[key] = (
            ConsistencyVersionState(
                tenant_id=current.tenant_id,
                index_key=current.index_key,
                source_version=current.source_version,
                projection_version=projection_version,
            )
        )

    def evaluate(
        self,
        *,
        tenant_id: str,
        index_key: str,
        source_version: int,
    ) -> ConsistencyEvaluation:
        source_version = _positive_version(
            source_version,
            "source_version",
        )

        key = (
            tenant_id,
            index_key,
        )

        current = self._states.get(key)

        if current is None:
            return ConsistencyEvaluation(
                status=ConsistencyStatus.STALE,
                tenant_id=tenant_id,
                index_key=index_key,
                source_version=source_version,
                projection_version=0,
                lag=source_version,
                stale=True,
                message=(
                    "No projection version is known "
                    "for this search identity."
                ),
            )

        if current.tenant_id != tenant_id:
            raise SearchConsistencyTenantError(
                "Tenant mismatch."
            )

        projection_version = (
            current.projection_version
        )

        if projection_version == source_version:
            return ConsistencyEvaluation(
                status=ConsistencyStatus.CURRENT,
                tenant_id=tenant_id,
                index_key=index_key,
                source_version=source_version,
                projection_version=projection_version,
                lag=0,
                stale=False,
                message="Projection is current.",
            )

        if projection_version < source_version:
            lag = (
                source_version
                - projection_version
            )

            return ConsistencyEvaluation(
                status=ConsistencyStatus.LAGGING,
                tenant_id=tenant_id,
                index_key=index_key,
                source_version=source_version,
                projection_version=projection_version,
                lag=lag,
                stale=True,
                message=(
                    "Search projection is behind "
                    "canonical source version."
                ),
            )

        raise SearchConsistencyVersionError(
            "Projection version cannot exceed "
            "requested source version."
        )

    def state(
        self,
        *,
        tenant_id: str,
        index_key: str,
    ) -> ConsistencyVersionState | None:
        return self._states.get(
            (
                tenant_id,
                index_key,
            )
        )

    def snapshot(
        self,
    ) -> tuple[ConsistencyVersionState, ...]:
        return tuple(
            sorted(
                self._states.values(),
                key=lambda state: (
                    state.tenant_id.casefold(),
                    state.index_key.casefold(),
                ),
            )
        )

    def apply_ordered_events(
        self,
        events: Iterable[ConsistencyEvent],
    ) -> tuple[ConsistencyStatus, ...]:
        if isinstance(
            events,
            (str, bytes),
        ):
            raise SearchConsistencyError(
                "events must be iterable."
            )

        materialized = list(events)

        for event in materialized:
            if not isinstance(
                event,
                ConsistencyEvent,
            ):
                raise SearchConsistencyError(
                    "events must contain ConsistencyEvent."
                )

        materialized.sort(
            key=lambda event: (
                event.tenant_id.casefold(),
                event.index_key.casefold(),
                event.source_version,
                event.event_id,
            )
        )

        return tuple(
            self.observe_event(event)
            for event in materialized
        )


__all__ = [
    "SearchConsistencyError",
    "SearchConsistencyVersionError",
    "SearchConsistencyTenantError",
    "ConsistencyStatus",
    "ConsistencyVersionState",
    "ConsistencyEvaluation",
    "ConsistencyEvent",
    "SearchConsistencyTracker",
]
