"""Context and execution budget controls for AUTONOMY_ENGINE V6.

This module provides deterministic budget accounting only.
It does not execute actions and does not replace the existing
AUTONOMY_ENGINE runtime or execution gateway.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BudgetSnapshot:
    """Immutable snapshot of current budget consumption."""

    limit: int
    used: int
    remaining: int
    exhausted: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "exhausted": self.exhausted,
        }


class ContextBudget:
    """Track a bounded integer execution/context budget.

    The counter is monotonic: consumption cannot become negative and
    releasing more capacity than has been consumed is rejected.
    """

    def __init__(self, limit: int) -> None:
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise TypeError("Budget limit must be an integer.")

        if limit < 0:
            raise ValueError("Budget limit cannot be negative.")

        self._limit = limit
        self._used = 0

    @property
    def limit(self) -> int:
        """Configured budget limit."""
        return self._limit

    @property
    def used(self) -> int:
        """Currently consumed budget."""
        return self._used

    @property
    def remaining(self) -> int:
        """Remaining budget capacity."""
        return max(0, self._limit - self._used)

    @property
    def exhausted(self) -> bool:
        """Whether the budget has been fully consumed."""
        return self._used >= self._limit

    def can_consume(self, amount: int) -> bool:
        """Return whether the requested amount fits within the budget."""
        self._validate_amount(amount)
        return self._used + amount <= self._limit

    def consume(self, amount: int) -> BudgetSnapshot:
        """Consume budget or fail closed when insufficient capacity exists."""
        self._validate_amount(amount)

        if not self.can_consume(amount):
            raise RuntimeError(
                f"Context budget exceeded: requested={amount}, "
                f"remaining={self.remaining}"
            )

        self._used += amount
        return self.snapshot()

    def release(self, amount: int) -> BudgetSnapshot:
        """Release previously consumed budget."""
        self._validate_amount(amount)

        if amount > self._used:
            raise ValueError(
                f"Cannot release {amount}; only {self._used} is used."
            )

        self._used -= amount
        return self.snapshot()

    def reset(self) -> BudgetSnapshot:
        """Reset consumed budget to zero."""
        self._used = 0
        return self.snapshot()

    def snapshot(self) -> BudgetSnapshot:
        """Return an immutable budget snapshot."""
        return BudgetSnapshot(
            limit=self._limit,
            used=self._used,
            remaining=self.remaining,
            exhausted=self.exhausted,
        )

    @staticmethod
    def _validate_amount(amount: int) -> None:
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError("Budget amount must be an integer.")

        if amount < 0:
            raise ValueError("Budget amount cannot be negative.")