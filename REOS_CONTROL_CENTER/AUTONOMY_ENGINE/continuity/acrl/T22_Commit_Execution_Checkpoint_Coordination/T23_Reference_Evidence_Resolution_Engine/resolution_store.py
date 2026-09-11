from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .evidence_models import ResolutionResult


class ResolutionReplayError(RuntimeError):
    pass


class ResolutionIdentityConflict(RuntimeError):
    pass


@dataclass
class ResolutionStore:
    _items: dict[
        str,
        ResolutionResult,
    ] = field(
        default_factory=dict
    )

    _lock: Lock = field(
        default_factory=Lock
    )

    def put(
        self,
        result: ResolutionResult,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                result.resolution_id
            )

            if existing is None:
                self._items[
                    result.resolution_id
                ] = result
                return

            if (
                existing.resolution_fingerprint
                == result.resolution_fingerprint
            ):
                raise ResolutionReplayError(
                    "Resolution already exists."
                )

            raise ResolutionIdentityConflict(
                "Resolution identity collision."
            )

    def get(
        self,
        resolution_id: str,
    ) -> ResolutionResult | None:
        with self._lock:
            return self._items.get(
                resolution_id
            )

    def contains(
        self,
        resolution_id: str,
    ) -> bool:
        with self._lock:
            return (
                resolution_id
                in self._items
            )
