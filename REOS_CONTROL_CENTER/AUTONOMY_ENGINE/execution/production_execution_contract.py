"""
Production Execution Contract for AUTONOMY_ENGINE R3.

Authority model
---------------
REOS_CONTROL_CENTER remains the sole authoritative controller.

This module defines the contract between:
    AUTONOMY_ENGINE
        -> production executor
        -> REOS_CONTROL_CENTER authoritative mutation mechanism

This module DOES NOT:
- execute controller commands,
- discover executors,
- create authorization,
- mutate controller state,
- mutate state.json,
- approve actions,
- bypass policy,
- bypass risk controls,
- bypass tripwires,
- retry failed mutations.

This module ONLY defines and validates the immutable contract used by the
production execution boundary.

Design goals
------------
- deterministic
- immutable
- fail-closed
- explicit authority provenance
- explicit executor provenance
- explicit action identity
- explicit execution attempt identity
- explicit result provenance
- replay-resistant contract shape
- no implicit defaults that grant authority
- JSON-safe serialization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ProductionExecutionStatus(str, Enum):
    """Terminal/status values for one production execution contract."""

    PROPOSED = "PROPOSED"
    READY = "READY"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class ProductionExecutionBlockReason(str, Enum):
    """Machine-readable fail-closed refusal reasons."""

    INVALID_CONTRACT = "INVALID_CONTRACT"
    AUTHORITY_MISSING = "AUTHORITY_MISSING"
    AUTHORITY_INVALID = "AUTHORITY_INVALID"
    EXECUTOR_MISSING = "EXECUTOR_MISSING"
    EXECUTOR_INVALID = "EXECUTOR_INVALID"
    ACTION_ID_MISSING = "ACTION_ID_MISSING"
    ATTEMPT_ID_MISSING = "ATTEMPT_ID_MISSING"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"
    CONTRACT_REPLAY = "CONTRACT_REPLAY"
    RESULT_INVALID = "RESULT_INVALID"


@dataclass(frozen=True)
class ProductionAuthority:
    """
    Explicit description of the authoritative controller boundary.

    The contract records authority provenance; it does not grant authority.
    """

    controller_name: str = ""
    controller_root: str = ""
    authority_token: str = ""
    authority_version: str = ""

    def validate(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []

        if not isinstance(self.controller_name, str) or not self.controller_name.strip():
            errors.append("controller_name is required.")

        if not isinstance(self.controller_root, str) or not self.controller_root.strip():
            errors.append("controller_root is required.")

        if not isinstance(self.authority_token, str) or not self.authority_token.strip():
            errors.append("authority_token is required.")

        if not isinstance(self.authority_version, str) or not self.authority_version.strip():
            errors.append("authority_version is required.")

        return not errors, tuple(errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "controller_name": self.controller_name,
            "controller_root": self.controller_root,
            "authority_token": self.authority_token,
            "authority_version": self.authority_version,
        }


@dataclass(frozen=True)
class ProductionExecutorIdentity:
    """
    Explicit identity of the executor crossing the production boundary.

    Identity is descriptive. It is never interpreted as authorization.
    """

    executor_name: str = ""
    executor_version: str = ""
    executor_type: str = ""
    executor_fingerprint: str = ""

    def validate(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []

        if not isinstance(self.executor_name, str) or not self.executor_name.strip():
            errors.append("executor_name is required.")

        if not isinstance(self.executor_version, str) or not self.executor_version.strip():
            errors.append("executor_version is required.")

        if not isinstance(self.executor_type, str) or not self.executor_type.strip():
            errors.append("executor_type is required.")

        if not isinstance(self.executor_fingerprint, str) or not self.executor_fingerprint.strip():
            errors.append("executor_fingerprint is required.")

        return not errors, tuple(errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_name": self.executor_name,
            "executor_version": self.executor_version,
            "executor_type": self.executor_type,
            "executor_fingerprint": self.executor_fingerprint,
        }


@dataclass(frozen=True)
class ProductionExecutionRequest:
    """
    Immutable production execution request.

    This object is a contract, not an execution primitive.

    No field in this object independently grants permission to execute.
    """

    action_id: str
    attempt_id: str
    action: str
    target: str

    authority: ProductionAuthority | None = None
    executor: ProductionExecutorIdentity | None = None

    parameters: Mapping[str, Any] = field(default_factory=dict)
    evidence: Mapping[str, Any] = field(default_factory=dict)

    status: ProductionExecutionStatus = ProductionExecutionStatus.PROPOSED

    def validate(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []

        if not isinstance(self.action_id, str) or not self.action_id.strip():
            errors.append(
                ProductionExecutionBlockReason.ACTION_ID_MISSING.value
            )

        if not isinstance(self.attempt_id, str) or not self.attempt_id.strip():
            errors.append(
                ProductionExecutionBlockReason.ATTEMPT_ID_MISSING.value
            )

        if not isinstance(self.action, str) or not self.action.strip():
            errors.append("action is required.")

        if not isinstance(self.target, str) or not self.target.strip():
            errors.append("target is required.")

        if self.authority is None:
            errors.append(
                ProductionExecutionBlockReason.AUTHORITY_MISSING.value
            )
        elif not isinstance(self.authority, ProductionAuthority):
            errors.append(
                ProductionExecutionBlockReason.AUTHORITY_INVALID.value
            )
        else:
            valid, authority_errors = self.authority.validate()
            if not valid:
                errors.extend(authority_errors)

        if self.executor is None:
            errors.append(
                ProductionExecutionBlockReason.EXECUTOR_MISSING.value
            )
        elif not isinstance(self.executor, ProductionExecutorIdentity):
            errors.append(
                ProductionExecutionBlockReason.EXECUTOR_INVALID.value
            )
        else:
            valid, executor_errors = self.executor.validate()
            if not valid:
                errors.extend(executor_errors)

        if not isinstance(self.parameters, Mapping):
            errors.append("parameters must be a mapping.")

        if not isinstance(self.evidence, Mapping):
            errors.append("evidence must be a mapping.")

        if not isinstance(self.status, ProductionExecutionStatus):
            errors.append("status must be a ProductionExecutionStatus.")

        return not errors, tuple(errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "attempt_id": self.attempt_id,
            "action": self.action,
            "target": self.target,
            "authority": (
                self.authority.to_dict()
                if self.authority is not None
                else None
            ),
            "executor": (
                self.executor.to_dict()
                if self.executor is not None
                else None
            ),
            "parameters": dict(self.parameters),
            "evidence": dict(self.evidence),
            "status": self.status.value,
        }


@dataclass(frozen=True)
class ProductionExecutionResult:
    """
    Immutable result returned by the production execution boundary.

    This result records what happened. It does not modify authority state.
    """

    action_id: str
    attempt_id: str
    status: ProductionExecutionStatus

    executed: bool
    allowed: bool

    reason: str = ""
    block_reason: ProductionExecutionBlockReason | None = None

    executor_name: str = ""
    authority_version: str = ""

    result: Any = None
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []

        if not isinstance(self.action_id, str) or not self.action_id.strip():
            errors.append(
                ProductionExecutionBlockReason.ACTION_ID_MISSING.value
            )

        if not isinstance(self.attempt_id, str) or not self.attempt_id.strip():
            errors.append(
                ProductionExecutionBlockReason.ATTEMPT_ID_MISSING.value
            )

        if not isinstance(self.status, ProductionExecutionStatus):
            errors.append("status must be a ProductionExecutionStatus.")

        if not isinstance(self.executed, bool):
            errors.append("executed must be boolean.")

        if not isinstance(self.allowed, bool):
            errors.append("allowed must be boolean.")

        if self.executed and not self.allowed:
            errors.append("executed cannot be true when allowed is false.")

        if not isinstance(self.evidence, Mapping):
            errors.append("evidence must be a mapping.")

        return not errors, tuple(errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "attempt_id": self.attempt_id,
            "status": self.status.value,
            "executed": self.executed,
            "allowed": self.allowed,
            "reason": self.reason,
            "block_reason": (
                self.block_reason.value
                if self.block_reason is not None
                else None
            ),
            "executor_name": self.executor_name,
            "authority_version": self.authority_version,
            "result": self.result,
            "evidence": dict(self.evidence),
        }


def validate_production_request(
    request: ProductionExecutionRequest,
) -> tuple[bool, tuple[str, ...]]:
    """
    Validate a production request without executing anything.

    Fail-closed behavior:
    malformed objects are invalid and never become executable.
    """

    if not isinstance(request, ProductionExecutionRequest):
        return (
            False,
            (ProductionExecutionBlockReason.INVALID_CONTRACT.value,),
        )

    return request.validate()


def validate_production_result(
    result: ProductionExecutionResult,
) -> tuple[bool, tuple[str, ...]]:
    """
    Validate a production result without changing execution state.
    """

    if not isinstance(result, ProductionExecutionResult):
        return (
            False,
            (ProductionExecutionBlockReason.RESULT_INVALID.value,),
        )

    return result.validate()


__all__ = [
    "ProductionExecutionStatus",
    "ProductionExecutionBlockReason",
    "ProductionAuthority",
    "ProductionExecutorIdentity",
    "ProductionExecutionRequest",
    "ProductionExecutionResult",
    "validate_production_request",
    "validate_production_result",
]
