"""Loop detection primitives for AUTONOMY_ENGINE V6.

This module detects repeated execution patterns before autonomous execution
can continue indefinitely.

It is intentionally isolated from the existing AUTONOMY_ENGINE foundation.
It does not execute tools, mutate controller state, or bypass existing
approval, integrity, workspace, or governance controls.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable


@dataclass(frozen=True)
class LoopDetectionResult:
    """Deterministic result of a loop detection check."""

    repeated: bool
    fingerprint: str
    occurrences: int
    threshold: int


class LoopDetector:
    """Bounded detector for repeated autonomous execution patterns."""

    def __init__(
        self,
        *,
        threshold: int = 3,
        history_limit: int = 256,
    ) -> None:
        if threshold < 2:
            raise ValueError("threshold must be at least 2")

        if history_limit < threshold:
            raise ValueError(
                "history_limit must be greater than or equal to threshold"
            )

        self._threshold = threshold
        self._history: deque[str] = deque(maxlen=history_limit)
        self._counts: dict[str, int] = {}

    @staticmethod
    def fingerprint(
        action: str,
        *,
        context: str = "",
    ) -> str:
        """Create a stable fingerprint for an execution pattern."""
        if not action:
            raise ValueError("action is required")

        payload = f"{context}\x00{action}".encode("utf-8")
        return sha256(payload).hexdigest()

    def observe(
        self,
        action: str,
        *,
        context: str = "",
    ) -> LoopDetectionResult:
        """Record an action and determine whether it has entered a loop."""
        fingerprint = self.fingerprint(action, context=context)

        self._history.append(fingerprint)
        self._counts[fingerprint] = (
            self._counts.get(fingerprint, 0) + 1
        )

        occurrences = self._counts[fingerprint]

        return LoopDetectionResult(
            repeated=occurrences >= self._threshold,
            fingerprint=fingerprint,
            occurrences=occurrences,
            threshold=self._threshold,
        )

    def has_loop(
        self,
        action: str,
        *,
        context: str = "",
    ) -> bool:
        """Observe an action and return only the loop state."""
        return self.observe(action, context=context).repeated

    def count(
        self,
        action: str,
        *,
        context: str = "",
    ) -> int:
        """Return the current occurrence count without observing a new action."""
        fingerprint = self.fingerprint(action, context=context)
        return self._counts.get(fingerprint, 0)

    def history(self) -> tuple[str, ...]:
        """Return the bounded fingerprint history."""
        return tuple(self._history)

    def reset(self) -> None:
        """Clear all observed execution history."""
        self._history.clear()
        self._counts.clear()

    def inspect(
        self,
        fingerprints: Iterable[str],
    ) -> tuple[LoopDetectionResult, ...]:
        """Inspect known fingerprints without changing detector state."""
        results: list[LoopDetectionResult] = []

        for fingerprint in fingerprints:
            occurrences = self._counts.get(fingerprint, 0)

            results.append(
                LoopDetectionResult(
                    repeated=occurrences >= self._threshold,
                    fingerprint=fingerprint,
                    occurrences=occurrences,
                    threshold=self._threshold,
                )
            )

        return tuple(results)