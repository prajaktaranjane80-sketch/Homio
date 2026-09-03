"""ACRL T03 — Atomic authoritative state observation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


class StateObservationError(RuntimeError):
    """Base observation failure."""


class StateObservationSourceError(StateObservationError):
    """State source is unavailable."""


class StateObservationConflictError(StateObservationError):
    """State changed during observation."""


@dataclass(frozen=True)
class ObservedState:
    """Immutable byte-level observation of authoritative state."""

    path: str
    size: int
    modified_ns: int
    sha256: str
    raw_bytes: bytes

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "size": self.size,
            "modified_ns": self.modified_ns,
            "sha256": self.sha256,
        }


def observe_authoritative_state(
    path: Path | str,
) -> ObservedState:
    """Read state bytes and detect a concurrent mutation."""

    target = Path(path)

    if not target.exists():
        raise StateObservationSourceError(
            f"Authoritative state not found: {target}"
        )

    if not target.is_file():
        raise StateObservationSourceError(
            f"Authoritative state is not a file: {target}"
        )

    try:
        before = target.stat()
        raw = target.read_bytes()
        after = target.stat()
    except OSError as exc:
        raise StateObservationSourceError(
            f"Unable to observe authoritative state: {target}"
        ) from exc

    if (
        before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise StateObservationConflictError(
            "Authoritative state changed during observation."
        )

    digest = hashlib.sha256(raw).hexdigest()

    return ObservedState(
        path=str(target.resolve()),
        size=len(raw),
        modified_ns=after.st_mtime_ns,
        sha256=digest,
        raw_bytes=raw,
    )


__all__ = [
    "ObservedState",
    "StateObservationConflictError",
    "StateObservationError",
    "StateObservationSourceError",
    "observe_authoritative_state",
]
