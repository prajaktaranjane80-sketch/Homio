"""Execution trace primitives for AUTONOMY_ENGINE V6.

Provides lightweight, deterministic tracing for autonomous runs without
replacing the existing AUTONOMY_ENGINE observability foundation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Mapping
import hashlib
import json


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TraceEvent:
    """Immutable event recorded during an autonomous run."""

    run_id: str
    sequence: int
    event_type: str
    timestamp: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RunTrace:
    """In-memory deterministic execution trace.

    The trace is observational only. It does not authorize, execute, or
    mutate engine actions.
    """

    def __init__(self, run_id: str) -> None:
        if not run_id.strip():
            raise ValueError("run_id is required.")

        self.run_id = run_id
        self._events: list[TraceEvent] = []

    def append(
        self,
        event_type: str,
        payload: Mapping[str, Any] | None = None,
    ) -> TraceEvent:
        """Append one ordered trace event."""
        event_type = event_type.strip()

        if not event_type:
            raise ValueError("event_type is required.")

        event = TraceEvent(
            run_id=self.run_id,
            sequence=len(self._events) + 1,
            event_type=event_type,
            timestamp=_utc_now(),
            payload=dict(payload or {}),
        )

        self._events.append(event)
        return event

    def events(self) -> tuple[TraceEvent, ...]:
        """Return an immutable view of recorded events."""
        return tuple(self._events)

    def export(self) -> list[dict[str, Any]]:
        """Return events in execution order."""
        return [event.to_dict() for event in self._events]

    def digest(self) -> str:
        """Return a deterministic digest of the complete trace."""
        return _stable_hash(self.export())

    def count(self) -> int:
        """Return the number of recorded events."""
        return len(self._events)

    def clear(self) -> None:
        """Clear the in-memory trace."""
        self._events.clear()