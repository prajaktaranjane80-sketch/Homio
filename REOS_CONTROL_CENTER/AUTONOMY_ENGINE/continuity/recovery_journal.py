"""Recovery journal primitives for AUTONOMY_ENGINE V6.

Provides an append-oriented, deterministic journal for recording recovery
events and execution continuity information.

This module does not modify the existing AUTONOMY_ENGINE controller state,
state store, integrity ledger, or recovery mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class RecoveryEntry:
    """Immutable recovery journal entry."""

    sequence: int
    event_type: str
    run_id: str
    timestamp: str
    payload: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "payload": dict(self.payload),
        }


class RecoveryJournal:
    """Bounded in-memory recovery journal."""

    def __init__(
        self,
        entries: Iterable[RecoveryEntry] | None = None,
    ) -> None:
        self._entries: list[RecoveryEntry] = []
        self._next_sequence = 1

        for entry in entries or ():
            self.append_existing(entry)

    @staticmethod
    def _timestamp() -> str:
        """Return a UTC timestamp in ISO-8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def append(
        self,
        *,
        event_type: str,
        run_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> RecoveryEntry:
        """Append a new recovery event."""
        if not event_type:
            raise ValueError("event_type is required")

        if not run_id:
            raise ValueError("run_id is required")

        entry = RecoveryEntry(
            sequence=self._next_sequence,
            event_type=event_type,
            run_id=run_id,
            timestamp=self._timestamp(),
            payload=dict(payload or {}),
        )

        self._entries.append(entry)
        self._next_sequence += 1

        return entry

    def append_existing(self, entry: RecoveryEntry) -> None:
        """Restore an existing entry while preserving its sequence."""
        if entry.sequence != self._next_sequence:
            raise ValueError(
                "recovery entries must be restored in sequence order"
            )

        if not entry.event_type:
            raise ValueError("event_type is required")

        if not entry.run_id:
            raise ValueError("run_id is required")

        self._entries.append(entry)
        self._next_sequence += 1

    def latest(self) -> RecoveryEntry | None:
        """Return the latest recovery entry."""
        if not self._entries:
            return None

        return self._entries[-1]

    def get(self, sequence: int) -> RecoveryEntry | None:
        """Return an entry by sequence number."""
        if sequence < 1:
            raise ValueError("sequence must be positive")

        for entry in self._entries:
            if entry.sequence == sequence:
                return entry

        return None

    def for_run(self, run_id: str) -> tuple[RecoveryEntry, ...]:
        """Return all entries belonging to a run."""
        if not run_id:
            raise ValueError("run_id is required")

        return tuple(
            entry
            for entry in self._entries
            if entry.run_id == run_id
        )

    def events(
        self,
        event_type: str,
    ) -> tuple[RecoveryEntry, ...]:
        """Return entries matching an event type."""
        if not event_type:
            raise ValueError("event_type is required")

        return tuple(
            entry
            for entry in self._entries
            if entry.event_type == event_type
        )

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        """Return a deterministic journal snapshot."""
        return tuple(
            entry.as_dict()
            for entry in self._entries
        )

    def clear(self) -> None:
        """Clear the local journal."""
        self._entries.clear()
        self._next_sequence = 1

    def __len__(self) -> int:
        """Return the number of journal entries."""
        return len(self._entries)