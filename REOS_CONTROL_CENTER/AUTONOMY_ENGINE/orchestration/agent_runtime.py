"""Agent runtime primitives for AUTONOMY_ENGINE V6.

This module provides the isolated runtime boundary for autonomous agents.
It does not execute tools directly and does not bypass the existing
AUTONOMY_ENGINE safety, approval, integrity, or workspace controls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AgentRuntimeContext:
    """Immutable execution context supplied to an agent runtime."""

    run_id: str
    agent_id: str
    task_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentRuntimeResult:
    """Deterministic result returned by an agent runtime."""

    run_id: str
    agent_id: str
    task_id: str
    status: str
    output: Mapping[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


class AgentRuntime:
    """Safe orchestration boundary for one autonomous agent execution."""

    VALID_STATUSES = frozenset(
        {
            "PLANNED",
            "RUNNING",
            "COMPLETED",
            "BLOCKED",
            "FAILED",
        }
    )

    def __init__(self, context: AgentRuntimeContext) -> None:
        if not context.run_id:
            raise ValueError("run_id is required")
        if not context.agent_id:
            raise ValueError("agent_id is required")
        if not context.task_id:
            raise ValueError("task_id is required")

        self._context = context
        self._status = "PLANNED"

    @property
    def context(self) -> AgentRuntimeContext:
        """Return the immutable runtime context."""
        return self._context

    @property
    def status(self) -> str:
        """Return the current runtime status."""
        return self._status

    def start(self) -> AgentRuntimeResult:
        """Transition the runtime from PLANNED to RUNNING."""
        if self._status != "PLANNED":
            raise RuntimeError(
                f"runtime cannot start from status {self._status}"
            )

        self._status = "RUNNING"
        return self.result()

    def complete(
        self,
        output: Mapping[str, Any] | None = None,
    ) -> AgentRuntimeResult:
        """Mark the runtime as successfully completed."""
        if self._status != "RUNNING":
            raise RuntimeError(
                f"runtime cannot complete from status {self._status}"
            )

        self._status = "COMPLETED"
        return self.result(output=output)

    def block(
        self,
        reason: str,
    ) -> AgentRuntimeResult:
        """Block execution without performing autonomous side effects."""
        if self._status != "RUNNING":
            raise RuntimeError(
                f"runtime cannot block from status {self._status}"
            )
        if not reason:
            raise ValueError("block reason is required")

        self._status = "BLOCKED"
        return self.result(errors=(reason,))

    def fail(
        self,
        reason: str,
    ) -> AgentRuntimeResult:
        """Record a runtime failure."""
        if self._status != "RUNNING":
            raise RuntimeError(
                f"runtime cannot fail from status {self._status}"
            )
        if not reason:
            raise ValueError("failure reason is required")

        self._status = "FAILED"
        return self.result(errors=(reason,))

    def result(
        self,
        output: Mapping[str, Any] | None = None,
        errors: tuple[str, ...] = (),
    ) -> AgentRuntimeResult:
        """Build a deterministic runtime result."""
        if self._status not in self.VALID_STATUSES:
            raise RuntimeError(f"invalid runtime status: {self._status}")

        return AgentRuntimeResult(
            run_id=self._context.run_id,
            agent_id=self._context.agent_id,
            task_id=self._context.task_id,
            status=self._status,
            output=dict(output or {}),
            errors=tuple(errors),
        )