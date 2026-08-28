"""
Production execution boundary for AUTONOMY_ENGINE R3.

This module defines the final local executor binding boundary used by the
production execution layer.

Authority model
---------------
- REOS_CONTROL_CENTER remains the sole controller authority.
- ProductionExecutor is NOT a controller.
- ProductionExecutor does not discover executors.
- ProductionExecutor does not invent controller commands.
- ProductionExecutor does not mutate state.json directly.
- ProductionExecutor executes only through an explicitly bound callable.
- An unbound executor is always default-deny.

Security model
--------------
ActionProposal
    |
    v
ProductionExecutor
    |
    +--> protocol validation
    +--> executor identity validation
    +--> capability validation
    +--> binding validation
    +--> timeout validation
    +--> single-attempt protection
    |
    v
Explicitly bound authoritative callable
    |
    v
ProductionExecutionResult

Design guarantees
-----------------
- Default deny.
- Fail closed.
- No implicit executor discovery.
- No implicit authorization.
- No implicit capability grant.
- No command invention.
- No retry loop.
- No silent fallback.
- No mutation before binding and validation.
- Executor exceptions never become successful execution.
- Timeout configuration is validated before execution.
- Each action_id is single-shot per executor instance.
- Evidence is deterministic and preserved.
- Identity is explicit and stable for the executor instance.
- Existing AUTONOMY_ENGINE architecture remains additive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from enum import Enum
from typing import Any, Callable, Mapping
from uuid import uuid4

from protocols.action_protocol import (
    ActionProposal,
    ProtocolDecision,
    validate_proposal,
)


ProductionCallable = Callable[[ActionProposal], Any]


class ProductionExecutorStatus(str, Enum):
    """Deterministic lifecycle states of production execution."""

    BLOCKED = "BLOCKED"
    READY = "READY"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ProductionExecutorBlockReason(str, Enum):
    """Machine-readable reasons for refusing production execution."""

    INVALID_PROPOSAL = "INVALID_PROPOSAL"
    IDENTITY_INVALID = "IDENTITY_INVALID"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    EXECUTOR_MISSING = "EXECUTOR_MISSING"
    EXECUTOR_UNBOUND = "EXECUTOR_UNBOUND"
    EXECUTOR_INVALID = "EXECUTOR_INVALID"
    TIMEOUT_INVALID = "TIMEOUT_INVALID"
    ALREADY_ATTEMPTED = "ALREADY_ATTEMPTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


@dataclass(frozen=True)
class ProductionExecutorFailure(Exception):
    """Structured representation of an executor failure."""

    error_type: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible representation."""

        return {
            "error_type": self.error_type,
            "message": self.message,
        }


@dataclass(frozen=True)
class ExecutorIdentity:
    """
    Immutable identity of one production executor instance.

    instance_id is generated automatically when omitted. This keeps the
    identity primitive safe to construct while preserving explicit identity
    in the resulting object.
    """

    name: str
    version: str
    instance_id: str = field(default_factory=lambda: str(uuid4()))

    def valid(self) -> bool:
        """Return whether the executor identity is structurally valid."""

        return all(
            isinstance(value, str) and bool(value.strip())
            for value in (
                self.name,
                self.version,
                self.instance_id,
            )
        )

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible identity representation."""

        return {
            "name": self.name,
            "version": self.version,
            "instance_id": self.instance_id,
        }


@dataclass(frozen=True)
class ExecutorCapability:
    """
    Explicit capability declaration for a production executor.

    Capabilities are descriptive. This class does not grant authorization.
    """

    name: str
    version: str = "1.0"
    enabled: bool = False

    def allows(self, required: str) -> bool:
        """
        Return whether this capability explicitly satisfies a requirement.

        Disabled capabilities never satisfy a requirement.
        """

        if not self.enabled:
            return False

        if not isinstance(required, str) or not required.strip():
            return False

        return self.name == required

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible capability representation."""

        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class ExecutionEnvelope:
    """
    Immutable envelope describing the production execution boundary.

    The proposal is descriptive execution data. It does not grant authority.
    """

    executor: ExecutorIdentity | None = None
    capability: ExecutorCapability | None = None
    timeout_seconds: float | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    proposal: ActionProposal | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible envelope representation."""

        return {
            "executor": (
                self.executor.to_dict()
                if self.executor is not None
                else None
            ),
            "capability": (
                self.capability.to_dict()
                if self.capability is not None
                else None
            ),
            "timeout_seconds": self.timeout_seconds,
            "evidence": dict(self.evidence),
            "proposal": (
                self.proposal.to_dict()
                if self.proposal is not None
                else None
            ),
        }


@dataclass(frozen=True)
class ProductionExecutionResult:
    """Immutable deterministic result of one production execution attempt."""

    status: ProductionExecutorStatus
    action_id: str
    allowed: bool
    reason: str
    protocol: ProtocolDecision
    envelope: ExecutionEnvelope | None = None
    result: Any = None
    failure: ProductionExecutorFailure | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    block_reason: ProductionExecutorBlockReason | None = None

    @property
    def error(self) -> ProductionExecutorFailure | None:
        """Compatibility accessor for machine-readable execution failure."""

        return self.failure

    @property
    def executed(self) -> bool:
        """Return whether the authoritative callable completed successfully."""

        return self.status is ProductionExecutorStatus.EXECUTED

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible result representation."""

        return {
            "status": self.status.value,
            "action_id": self.action_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "protocol": self.protocol.to_dict(),
            "envelope": (
                self.envelope.to_dict()
                if self.envelope is not None
                else None
            ),
            "result": self.result,
            "failure": (
                self.failure.to_dict()
                if self.failure is not None
                else None
            ),
            "evidence": dict(self.evidence),
            "block_reason": (
                self.block_reason.value
                if self.block_reason is not None
                else None
            ),
            "executed": self.executed,
        }


class ProductionExecutor:
    """
    Explicit production executor binding boundary.

    The object starts unbound.

    Nothing is executed until:
    1. the proposal validates,
    2. executor identity is valid,
    3. capability is explicitly enabled,
    4. an explicit callable has been bound,
    5. timeout configuration is valid,
    6. the action has not already been attempted.

    The class never discovers or creates an executor.
    """

    def __init__(
        self,
        *,
        identity: ExecutorIdentity | None = None,
        capability: ExecutorCapability | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._identity = identity or ExecutorIdentity(
            name="REOS_PRODUCTION_EXECUTOR",
            version="3.0",
        )

        self._capability = capability or ExecutorCapability(
            name="controller_mutation",
            version="1.0",
            enabled=False,
        )

        self._timeout_seconds = timeout_seconds
        self._executor: ProductionCallable | None = None
        self._attempted_action_ids: set[str] = set()

    @property
    def identity(self) -> ExecutorIdentity:
        """Return immutable executor identity."""

        return self._identity

    @property
    def capability(self) -> ExecutorCapability:
        """Return the executor capability declaration."""

        return self._capability

    @property
    def bound(self) -> bool:
        """Return whether an explicit callable is currently bound."""

        return self._executor is not None

    def bind(self, executor: ProductionCallable) -> None:
        """
        Bind one explicit authoritative production callable.

        Binding never executes the callable.

        A second binding is rejected rather than silently replacing the
        existing production boundary.
        """

        if self._executor is not None:
            raise RuntimeError(
                "Production executor is already bound."
            )

        if not callable(executor):
            raise TypeError(
                "Production executor must be callable."
            )

        self._executor = executor

    def preflight(
        self,
        proposal: ActionProposal,
    ) -> ProductionExecutionResult:
        """
        Validate production execution without invoking the executor.
        """

        action_id = self._safe_action_id(proposal)

        protocol = self._validate_safely(proposal)

        if not protocol.valid:
            return self._blocked(
                action_id=action_id,
                protocol=protocol,
                reason="Action proposal failed protocol validation.",
                block_reason=ProductionExecutorBlockReason.INVALID_PROPOSAL,
                evidence={
                    "execution_attempted": False,
                    "preflight_passed": False,
                },
            )

        if not self._identity.valid():
            return self._blocked(
                action_id=action_id,
                protocol=protocol,
                reason="Production executor identity is invalid.",
                block_reason=ProductionExecutorBlockReason.IDENTITY_INVALID,
                evidence={
                    "execution_attempted": False,
                    "preflight_passed": False,
                },
            )

        if self._executor is None:
            return self._blocked(
                action_id=action_id,
                protocol=protocol,
                reason="No production executor has been explicitly bound.",
                block_reason=ProductionExecutorBlockReason.EXECUTOR_MISSING,
                evidence={
                    "execution_attempted": False,
                    "preflight_passed": False,
                    "executor_bound": False,
                },
            )

        if not callable(self._executor):
            return self._blocked(
                action_id=action_id,
                protocol=protocol,
                reason="Bound production executor is not callable.",
                block_reason=ProductionExecutorBlockReason.EXECUTOR_INVALID,
                evidence={
                    "execution_attempted": False,
                    "preflight_passed": False,
                },
            )

        try:
            self._validate_timeout(self._timeout_seconds)
        except (TypeError, ValueError):
            return self._blocked(
                action_id=action_id,
                protocol=protocol,
                reason="Production executor timeout configuration is invalid.",
                block_reason=ProductionExecutorBlockReason.TIMEOUT_INVALID,
                evidence={
                    "execution_attempted": False,
                    "preflight_passed": False,
                },
            )

        if action_id in self._attempted_action_ids:
            return self._blocked(
                action_id=action_id,
                protocol=protocol,
                reason="Action has already been attempted by this executor.",
                block_reason=ProductionExecutorBlockReason.ALREADY_ATTEMPTED,
                evidence={
                    "execution_attempted": False,
                    "preflight_passed": False,
                    "replay_blocked": True,
                },
            )

        return ProductionExecutionResult(
            status=ProductionExecutorStatus.READY,
            action_id=action_id,
            allowed=True,
            reason="Production execution preflight passed.",
            protocol=protocol,
            envelope=ExecutionEnvelope(
                executor=self._identity,
                capability=self._capability,
                timeout_seconds=self._timeout_seconds,
                proposal=proposal,
            ),
            evidence={
                "execution_attempted": False,
                "preflight_passed": True,
                "executor_bound": True,
            },
        )

    def execute(
        self,
        proposal: ActionProposal,
    ) -> ProductionExecutionResult:
        """
        Execute exactly one explicitly bound production action.

        There is intentionally no retry behavior.
        """

        preflight = self.preflight(proposal)

        if not preflight.allowed:
            return preflight

        action_id = preflight.action_id

        self._attempted_action_ids.add(action_id)

        executor = self._executor

        if executor is None:
            # Defensive race/integrity boundary. The preflight should already
            # have blocked this case.
            return self._blocked(
                action_id=action_id,
                protocol=preflight.protocol,
                reason="Production executor became unbound before execution.",
                block_reason=ProductionExecutorBlockReason.EXECUTOR_MISSING,
                evidence={
                    **dict(preflight.evidence),
                    "execution_attempted": False,
                },
            )

        try:
            result = executor(proposal)

        except Exception as exc:
            failure = ProductionExecutorFailure(
                error_type=type(exc).__name__,
                message=str(exc),
            )

            return ProductionExecutionResult(
                status=ProductionExecutorStatus.FAILED,
                action_id=action_id,
                allowed=False,
                reason="Bound production executor failed.",
                protocol=preflight.protocol,
                envelope=preflight.envelope,
                failure=failure,
                evidence={
                    **dict(preflight.evidence),
                    "execution_attempted": True,
                    "execution_succeeded": False,
                    "failure_type": type(exc).__name__,
                },
                block_reason=ProductionExecutorBlockReason.EXECUTION_FAILED,
            )

        return ProductionExecutionResult(
            status=ProductionExecutorStatus.EXECUTED,
            action_id=action_id,
            allowed=True,
            reason="Bound production executor completed successfully.",
            protocol=preflight.protocol,
            envelope=preflight.envelope,
            result=result,
            evidence={
                **dict(preflight.evidence),
                "execution_attempted": True,
                "execution_succeeded": True,
            },
        )

    def attempted(self, action_id: str) -> bool:
        """Return whether an action has already crossed this boundary."""

        return action_id in self._attempted_action_ids

    def reset(self) -> None:
        """
        Clear local attempt memory only.

        This does not reset controller state, persistent idempotency records,
        governance decisions, or external execution history.
        """

        self._attempted_action_ids.clear()

    def describe(self) -> dict[str, Any]:
        """Return a deterministic diagnostic description."""

        return {
            "identity": self._identity.to_dict(),
            "capability": self._capability.to_dict(),
            "bound": self.bound,
            "timeout_seconds": self._timeout_seconds,
            "attempted_action_count": len(self._attempted_action_ids),
        }

    @staticmethod
    def _safe_action_id(proposal: Any) -> str:
        """Extract an action identifier without trusting external shape."""

        try:
            action_id = proposal.action_id
        except Exception:
            return "<invalid-action-id>"

        if isinstance(action_id, str) and action_id:
            return action_id

        return "<invalid-action-id>"

    @staticmethod
    def _validate_safely(proposal: Any) -> ProtocolDecision:
        """Validate a proposal without allowing validator exceptions out."""

        try:
            return validate_proposal(proposal)
        except Exception:
            return ProtocolDecision(
                valid=False,
                action_id="",
                errors=("proposal_validation_exception",),
            )

    @staticmethod
    def _validate_timeout(
        timeout_seconds: float | None,
    ) -> float | None:
        """
        Validate optional timeout configuration.

        None means explicitly unset. Invalid values fail closed by raising.
        """

        if timeout_seconds is None:
            return None

        if isinstance(timeout_seconds, bool):
            raise TypeError(
                "timeout_seconds must be a finite positive number or None"
            )

        if not isinstance(timeout_seconds, (int, float)):
            raise TypeError(
                "timeout_seconds must be a finite positive number or None"
            )

        value = float(timeout_seconds)

        if not math.isfinite(value):
            raise ValueError(
                "timeout_seconds must be finite"
            )

        if value <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero"
            )

        return timeout_seconds

    def _blocked(
        self,
        *,
        action_id: str,
        protocol: ProtocolDecision,
        reason: str,
        block_reason: ProductionExecutorBlockReason,
        evidence: Mapping[str, Any] | None = None,
    ) -> ProductionExecutionResult:
        """Construct a deterministic blocked result."""

        return ProductionExecutionResult(
            status=ProductionExecutorStatus.BLOCKED,
            action_id=action_id,
            allowed=False,
            reason=reason,
            protocol=protocol,
            envelope=ExecutionEnvelope(
                executor=self._identity,
                capability=self._capability,
                timeout_seconds=self._timeout_seconds,
            ),
            block_reason=block_reason,
            evidence=dict(evidence or {}),
        )

    @staticmethod
    def _merge_evidence(
        result: ProductionExecutionResult,
        additional: Mapping[str, Any] | None,
    ) -> ProductionExecutionResult:
        """Return a result with additional immutable evidence merged in."""

        if not additional:
            return result

        return ProductionExecutionResult(
            status=result.status,
            action_id=result.action_id,
            allowed=result.allowed,
            reason=result.reason,
            protocol=result.protocol,
            envelope=result.envelope,
            result=result.result,
            failure=result.failure,
            evidence={
                **dict(result.evidence),
                **dict(additional),
            },
            block_reason=result.block_reason,
        )


__all__ = [
    "ProductionCallable",
    "ProductionExecutorStatus",
    "ProductionExecutorBlockReason",
    "ProductionExecutorFailure",
    "ExecutorIdentity",
    "ExecutorCapability",
    "ExecutionEnvelope",
    "ProductionExecutionResult",
    "ProductionExecutor",
]


