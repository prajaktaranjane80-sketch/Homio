from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .budget_models import (
    BudgetResult,
)


class BudgetReplayError(RuntimeError):
    pass


class BudgetIdentityConflict(RuntimeError):
    pass


@dataclass
class BudgetStore:
    _items: dict[
        str,
        BudgetResult,
    ] = field(
        default_factory=dict
    )

    _lock: Lock = field(
        default_factory=Lock
    )

    def put(
        self,
        result: BudgetResult,
    ) -> None:
        with self._lock:
            existing = self._items.get(
                result.request_id
            )

            if existing is None:
                self._items[
                    result.request_id
                ] = result
                return

            if (
                existing.result_fingerprint
                == result.result_fingerprint
            ):
                raise BudgetReplayError(
                    "Identical budget result already exists."
                )

            raise BudgetIdentityConflict(
                "Budget request identity collision."
            )

    def get(
        self,
        request_id: str,
    ) -> BudgetResult | None:
        with self._lock:
            return self._items.get(
                request_id
            )

    def contains(
        self,
        request_id: str,
    ) -> bool:
        with self._lock:
            return request_id in self._items
