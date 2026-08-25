"""Security tripwires for AUTONOMY_ENGINE V6.

Tripwires provide deterministic, fail-closed checks for dangerous runtime
conditions. They do not execute tools, mutate controller state, or bypass
existing AUTONOMY_ENGINE approval, integrity, governance, or workspace
controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable


class TripwireSeverity(str, Enum):
    """Severity assigned to a triggered tripwire."""

    WARNING = "WARNING"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class TripwireResult:
    """Immutable result produced by a tripwire evaluation."""

    tripwire_id: str
    triggered: bool
    severity: TripwireSeverity
    reason: str = ""

    @property
    def blocked(self) -> bool:
        """Return whether the result requires execution to stop."""
        return (
            self.triggered
            and self.severity == TripwireSeverity.BLOCK
        )


@dataclass(frozen=True)
class Tripwire:
    """A deterministic security condition."""

    tripwire_id: str
    check: Callable[[], bool]
    severity: TripwireSeverity = TripwireSeverity.BLOCK
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.tripwire_id:
            raise ValueError("tripwire_id is required")

        if not callable(self.check):
            raise TypeError("check must be callable")

        if not self.reason:
            raise ValueError("reason is required")

    def evaluate(self) -> TripwireResult:
        """Evaluate this tripwire and return a normalized result."""
        try:
            triggered = bool(self.check())
        except Exception as exc:
            # Security evaluation failure must fail closed.
            return TripwireResult(
                tripwire_id=self.tripwire_id,
                triggered=True,
                severity=TripwireSeverity.BLOCK,
                reason=(
                    f"tripwire evaluation failed: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        return TripwireResult(
            tripwire_id=self.tripwire_id,
            triggered=triggered,
            severity=self.severity,
            reason=self.reason if triggered else "",
        )


class TripwireRegistry:
    """Registry and evaluator for security tripwires."""

    def __init__(
        self,
        tripwires: Iterable[Tripwire] | None = None,
    ) -> None:
        self._tripwires: dict[str, Tripwire] = {}

        for tripwire in tripwires or ():
            self.register(tripwire)

    def register(self, tripwire: Tripwire) -> None:
        """Register a tripwire without silent replacement."""
        if tripwire.tripwire_id in self._tripwires:
            raise ValueError(
                f"tripwire already registered: "
                f"{tripwire.tripwire_id}"
            )

        self._tripwires[tripwire.tripwire_id] = tripwire

    def get(self, tripwire_id: str) -> Tripwire | None:
        """Return a registered tripwire."""
        return self._tripwires.get(tripwire_id)

    def evaluate(self) -> tuple[TripwireResult, ...]:
        """Evaluate all registered tripwires."""
        return tuple(
            tripwire.evaluate()
            for tripwire in self._tripwires.values()
        )

    def blocking_results(self) -> tuple[TripwireResult, ...]:
        """Return only results that require execution to stop."""
        return tuple(
            result
            for result in self.evaluate()
            if result.blocked
        )

    def is_blocked(self) -> bool:
        """Return whether any tripwire currently blocks execution."""
        return bool(self.blocking_results())

    def snapshot(self) -> tuple[str, ...]:
        """Return registered tripwire IDs in deterministic order."""
        return tuple(sorted(self._tripwires))

    def __len__(self) -> int:
        """Return the number of registered tripwires."""
        return len(self._tripwires)