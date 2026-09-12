from __future__ import annotations

from threading import RLock

from .scheduler_models import ScheduleSnapshot


class SchedulerReplayError(Exception):
    pass


class SchedulerIdentityConflict(Exception):
    pass


class SchedulerStore:
    def __init__(self) -> None:
        self._items: dict[
            str,
            ScheduleSnapshot,
        ] = {}
        self._lock = RLock()

    def get(
        self,
        scheduler_id: str,
    ) -> ScheduleSnapshot | None:
        with self._lock:
            return self._items.get(
                scheduler_id
            )

    def put(
        self,
        snapshot: ScheduleSnapshot,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                snapshot.scheduler_id
            )

            if existing is None:
                self._items[
                    snapshot.scheduler_id
                ] = snapshot
                return

            if (
                existing.schedule_fingerprint
                == snapshot.schedule_fingerprint
            ):
                raise SchedulerReplayError(
                    "Identical scheduler already exists."
                )

            raise SchedulerIdentityConflict(
                "Scheduler identity collision."
            )

    def update(
        self,
        snapshot: ScheduleSnapshot,
    ) -> None:
        with self._lock:
            self._items[
                snapshot.scheduler_id
            ] = snapshot
