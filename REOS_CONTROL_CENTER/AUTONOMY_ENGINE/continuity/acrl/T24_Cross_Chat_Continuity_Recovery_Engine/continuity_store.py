from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .continuity_models import (
    ContinuityResult,
)


class ContinuityReplayError(RuntimeError):
    pass


class ContinuityIdentityConflict(RuntimeError):
    pass


@dataclass
class ContinuityStore:
    _items: dict[
        str,
        ContinuityResult,
    ] = field(
        default_factory=dict
    )

    _lock: Lock = field(
        default_factory=Lock
    )

    def put(
        self,
        result: ContinuityResult,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                result.recovery_id
            )

            if existing is None:
                self._items[
                    result.recovery_id
                ] = result
                return

            if (
                existing.recovery_fingerprint
                == result.recovery_fingerprint
            ):
                raise ContinuityReplayError(
                    "Identical recovery already exists."
                )

            raise ContinuityIdentityConflict(
                "Recovery identity collision."
            )

    def get(
        self,
        recovery_id: str,
    ) -> ContinuityResult | None:
        with self._lock:
            return self._items.get(
                recovery_id
            )

    def contains(
        self,
        recovery_id: str,
    ) -> bool:
        with self._lock:
            return recovery_id in self._items

    def size(self) -> int:
        with self._lock:
            return len(self._items)
