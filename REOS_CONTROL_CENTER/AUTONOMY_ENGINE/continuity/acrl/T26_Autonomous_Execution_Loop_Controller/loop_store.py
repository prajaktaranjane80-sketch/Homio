from __future__ import annotations

from dataclasses import dataclass, field, replace
from threading import RLock

from .loop_models import ExecutionLoop, LoopStatus


class LoopReplayError(RuntimeError):
    """An identical loop operation has already been recorded."""


class LoopIdentityConflict(RuntimeError):
    """An existing loop identity or immutable contract was changed."""


class LoopConcurrentUpdateError(RuntimeError):
    """A stale, branched, or non-monotonic loop update was rejected."""


_IMMUTABLE_FIELDS = (
    "schema_version",
    "loop_version",
    "loop_id",
    "execution_intent",
    "checkpoint_id",
    "checkpoint_fingerprint",
    "continuity_recovery_id",
    "continuity_fingerprint",
    "evidence_resolution_id",
    "evidence_fingerprint",
    "max_iterations",
    "max_retries_per_iteration",
    "total_work_budget",
    "total_token_budget",
    "total_context_budget",
    "no_progress_limit",
)

_TERMINAL_STATUSES = frozenset(
    {
        LoopStatus.STOPPED,
        LoopStatus.COMPLETED,
        LoopStatus.BLOCKED,
        LoopStatus.EXHAUSTED,
        LoopStatus.FAILED,
    }
)

_ADVANCE_STATUSES = frozenset(
    {
        LoopStatus.RUNNING,
        LoopStatus.PAUSED,
        LoopStatus.STOPPED,
        LoopStatus.COMPLETED,
        LoopStatus.FAILED,
    }
)


@dataclass
class LoopStore:
    """
    Thread-safe in-memory store for bounded execution-loop state.

    Guarantees provided by this implementation:
    - loop IDs cannot be reused for different immutable execution inputs;
    - iterations cannot be overwritten by stale snapshots;
    - iteration history must extend the stored history by exactly one item;
    - budgets cannot increase or consumption move backwards;
    - terminal loop states cannot be reopened;
    - the explicitly supported budget-exhaustion transition may update
      status without adding an iteration.

    This is an in-memory store, not a durable database or a distributed
    transaction ledger. Cross-process durability must be provided by an
    approved persistent store implementing equivalent atomic semantics.
    """

    _items: dict[str, ExecutionLoop] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)

    def put(self, loop: ExecutionLoop) -> None:
        if not isinstance(loop, ExecutionLoop):
            raise TypeError("loop must be an ExecutionLoop.")

        with self._lock:
            existing = self._items.get(loop.loop_id)

            if existing is None:
                self._items[loop.loop_id] = loop
                return

            if existing.loop_fingerprint == loop.loop_fingerprint:
                raise LoopReplayError(
                    "Identical loop already exists."
                )

            raise LoopIdentityConflict(
                "Loop identity already exists with different state."
            )

    def get(self, loop_id: str) -> ExecutionLoop | None:
        with self._lock:
            return self._items.get(loop_id)

    @staticmethod
    def _validate_immutable_identity(
        existing: ExecutionLoop,
        candidate: ExecutionLoop,
    ) -> None:
        changed = [
            name
            for name in _IMMUTABLE_FIELDS
            if getattr(existing, name) != getattr(candidate, name)
        ]

        if changed:
            # Do not include potentially sensitive execution-intent values.
            raise LoopIdentityConflict(
                "Immutable loop contract changed: "
                + ", ".join(changed)
                + "."
            )

    @staticmethod
    def _is_budget_exhaustion_transition(
        existing: ExecutionLoop,
        candidate: ExecutionLoop,
    ) -> bool:
        """
        Allow only the controller's explicit same-iteration exhaustion
        transition, with every other state field remaining unchanged.
        """
        if existing.status not in {
            LoopStatus.RUNNING,
            LoopStatus.PAUSED,
        }:
            return False

        if candidate.status is not LoopStatus.EXHAUSTED:
            return False

        if candidate.terminal_reason != "BUDGET_EXHAUSTED":
            return False

        if candidate.current_iteration != existing.current_iteration:
            return False

        restored = replace(
            candidate,
            status=existing.status,
            terminal_reason=existing.terminal_reason,
            loop_fingerprint=existing.loop_fingerprint,
        )

        return restored == existing

    @staticmethod
    def _validate_consumption(
        existing: ExecutionLoop,
        candidate: ExecutionLoop,
    ) -> None:
        budget_pairs = (
            ("work_consumed", "total_work_budget"),
            ("token_consumed", "total_token_budget"),
            ("context_consumed", "total_context_budget"),
        )

        for consumed_name, budget_name in budget_pairs:
            previous = getattr(existing, consumed_name)
            current = getattr(candidate, consumed_name)
            budget = getattr(candidate, budget_name)

            for value, label in (
                (previous, consumed_name),
                (current, consumed_name),
                (budget, budget_name),
            ):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or value < 0
                ):
                    raise LoopConcurrentUpdateError(
                        f"{label} must be a non-negative integer."
                    )

            if current < previous:
                raise LoopConcurrentUpdateError(
                    f"{consumed_name} cannot move backwards."
                )

            if current > budget:
                raise LoopConcurrentUpdateError(
                    f"{consumed_name} exceeds its immutable budget."
                )

    def update(self, loop: ExecutionLoop) -> None:
        """
        Atomically validate and store one legal state transition.

        The current revision is checked while holding the same lock used
        for the write. A competing update derived from a stale snapshot
        cannot silently replace the winning iteration.
        """
        if not isinstance(loop, ExecutionLoop):
            raise TypeError("loop must be an ExecutionLoop.")

        if not isinstance(loop.status, LoopStatus):
            raise TypeError("loop.status must be a LoopStatus.")

        with self._lock:
            existing = self._items.get(loop.loop_id)

            if existing is None:
                raise KeyError("Unknown loop.")

            if existing.loop_fingerprint == loop.loop_fingerprint:
                raise LoopReplayError(
                    "Identical loop state cannot be written twice."
                )

            self._validate_immutable_identity(existing, loop)

            if existing.status in _TERMINAL_STATUSES:
                raise LoopConcurrentUpdateError(
                    "A terminal execution loop cannot be reopened."
                )

            if self._is_budget_exhaustion_transition(existing, loop):
                self._items[loop.loop_id] = loop
                return

            if loop.current_iteration <= existing.current_iteration:
                raise LoopConcurrentUpdateError(
                    "Stale loop revision: iteration did not advance."
                )

            if loop.current_iteration != existing.current_iteration + 1:
                raise LoopConcurrentUpdateError(
                    "An update must advance exactly one iteration."
                )

            if (
                len(existing.iterations) != existing.current_iteration
                or len(loop.iterations) != loop.current_iteration
            ):
                raise LoopConcurrentUpdateError(
                    "Loop iteration count does not match its history."
                )

            if (
                loop.iterations[: len(existing.iterations)]
                != existing.iterations
            ):
                raise LoopConcurrentUpdateError(
                    "An update cannot rewrite prior iteration history."
                )

            if len(loop.iterations) != len(existing.iterations) + 1:
                raise LoopConcurrentUpdateError(
                    "An update must append exactly one iteration."
                )

            if loop.iterations[-1].iteration != loop.current_iteration:
                raise LoopConcurrentUpdateError(
                    "The appended iteration identity is inconsistent."
                )

            if existing.status not in {
                LoopStatus.RUNNING,
                LoopStatus.PAUSED,
            }:
                raise LoopConcurrentUpdateError(
                    "The current loop status does not allow advancement."
                )

            if loop.status not in _ADVANCE_STATUSES:
                raise LoopConcurrentUpdateError(
                    "The requested loop status is not valid for advancement."
                )

            if loop.current_iteration > loop.max_iterations:
                raise LoopConcurrentUpdateError(
                    "The iteration limit cannot be exceeded."
                )

            self._validate_consumption(existing, loop)

            self._items[loop.loop_id] = loop
