from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .checkpoint_models import ExecutionCheckpoint


class CheckpointReplayError(RuntimeError):
    pass


class CheckpointConcurrencyError(RuntimeError):
    pass


@dataclass
class CheckpointStore:
    _items: dict[str, ExecutionCheckpoint] = field(
        default_factory=dict
    )
    _lock: Lock = field(
        default_factory=Lock
    )

    def get(
        self,
        checkpoint_id: str,
    ) -> ExecutionCheckpoint | None:
        with self._lock:
            return self._items.get(
                checkpoint_id
            )

    def put(
        self,
        checkpoint: ExecutionCheckpoint,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                checkpoint.checkpoint_id
            )

            if existing is not None:
                if (
                    existing.checkpoint_fingerprint
                    == checkpoint.checkpoint_fingerprint
                ):
                    raise CheckpointReplayError(
                        "Checkpoint already exists."
                    )

                raise CheckpointConcurrencyError(
                    "Checkpoint identity collision detected."
                )

            self._items[
                checkpoint.checkpoint_id
            ] = checkpoint

    def contains(
        self,
        checkpoint_id: str,
    ) -> bool:
        with self._lock:
            return checkpoint_id in self._items

    def size(self) -> int:
        with self._lock:
            return len(self._items)
