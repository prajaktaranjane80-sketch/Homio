from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock

from .loop_models import ExecutionLoop


class LoopReplayError(RuntimeError):
    pass


class LoopIdentityConflict(RuntimeError):
    pass


@dataclass
class LoopStore:
    _items: dict[
        str,
        ExecutionLoop,
    ] = field(
        default_factory=dict
    )

    _lock: RLock = field(
        default_factory=RLock
    )

    def put(
        self,
        loop: ExecutionLoop,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                loop.loop_id
            )

            if existing is None:
                self._items[
                    loop.loop_id
                ] = loop
                return

            if (
                existing.loop_fingerprint
                == loop.loop_fingerprint
            ):
                raise LoopReplayError(
                    "Identical loop already exists."
                )

            raise LoopIdentityConflict(
                "Loop identity collision."
            )

    def get(
        self,
        loop_id: str,
    ) -> ExecutionLoop | None:
        with self._lock:
            return self._items.get(
                loop_id
            )

    def update(
        self,
        loop: ExecutionLoop,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                loop.loop_id
            )

            if existing is None:
                raise KeyError(
                    "Unknown loop."
                )

            self._items[
                loop.loop_id
            ] = loop
