"""ACRL T01 — Atomic authoritative-state observation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any


OBSERVATION_SCHEMA_VERSION = "1.0"


class ObservationError(RuntimeError):
    """Base observation error."""


class ObservationChangedDuringReadError(ObservationError):
    """Raised when authoritative state changes during one observation."""


@dataclass(frozen=True)
class StateObservation:
    """Immutable observation of one authoritative state version."""

    path: str
    source_sha256: str
    content: bytes
    schema_size: int
    schema_mtime_ns: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "path": self.path,
            "source_sha256": self.source_sha256,
            "content_size": len(self.content),
            "schema_size": self.schema_size,
            "schema_mtime_ns": self.schema_mtime_ns,
        }


def observe_state_atomically(path: Path | str) -> StateObservation:
    """Read state bytes only when metadata is stable across the read."""

    target = Path(path).resolve()

    try:
        before = target.stat()
        content = target.read_bytes()
        after = target.stat()
    except OSError as exc:
        raise ObservationError(
            f"Unable to observe authoritative state: {target}"
        ) from exc

    before_sha = hashlib.sha256(content).hexdigest()

    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise ObservationChangedDuringReadError(
            f"Authoritative state changed during observation: {target}"
        )

    return StateObservation(
        path=str(target),
        source_sha256=before_sha,
        content=content,
        schema_size=after.st_size,
        schema_mtime_ns=after.st_mtime_ns,
    )


__all__ = [
    "OBSERVATION_SCHEMA_VERSION",
    "ObservationChangedDuringReadError",
    "ObservationError",
    "StateObservation",
    "observe_state_atomically",
]