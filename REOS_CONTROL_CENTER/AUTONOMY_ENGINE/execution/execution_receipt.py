"""
Deterministic execution receipt boundary for AUTONOMY_ENGINE.

This module is additive and intentionally does not modify or bypass the
existing REOS_CONTROL_CENTER authority.

Design guarantees
-----------------
- No controller-state mutation.
- No executor discovery.
- No execution or retry behavior.
- No authorization inference.
- No success inference from incomplete evidence.
- Receipt creation is deterministic and fail-closed.
- Execution evidence is preserved without modification.
- Receipt objects are immutable.
- Receipt validation requires explicit completion evidence.
- Existing AUTONOMY_ENGINE modules remain unchanged.

Purpose
-------
This module creates a machine-readable receipt describing the outcome of an
execution coordination attempt.

The receipt is evidence, not authority.

REOS_CONTROL_CENTER remains the authoritative source for controller state,
approval, governance, and persistent execution state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ReceiptStatus(str, Enum):
    """Deterministic lifecycle status represented by an execution receipt."""

    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    EXECUTED = "EXECUTED"
    INVALID = "INVALID"


class ReceiptValidationReason(str, Enum):
    """Machine-readable receipt validation outcomes."""

    VALID = "VALID"
    INVALID_ACTION_ID = "INVALID_ACTION_ID"
    INVALID_STATUS = "INVALID_STATUS"
    EXECUTION_NOT_ATTEMPTED = "EXECUTION_NOT_ATTEMPTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    PROVENANCE_INVALID = "PROVENANCE_INVALID"
    STATE_INCONSISTENT = "STATE_INCONSISTENT"


@dataclass(frozen=True)
class ReceiptValidation:
    """Immutable result of validating an execution receipt."""

    valid: bool
    reason: ReceiptValidationReason
    failures: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "valid": self.valid,
            "reason": self.reason.value,
            "failures": list(self.failures),
        }


@dataclass(frozen=True)
class ExecutionReceipt:
    """
    Immutable evidence record for one execution coordination attempt.

    A receipt does not authorize execution and does not represent controller
    state. It only records supplied execution facts.
    """

    action_id: str
    status: ReceiptStatus
    execution_attempted: bool
    execution_succeeded: bool
    evidence_complete: bool
    provenance_valid: bool
    state_consistent: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)

    @property
    def successful(self) -> bool:
        """Return True only when every completion condition is explicitly true."""
        return (
            self.status is ReceiptStatus.EXECUTED
            and self.execution_attempted is True
            and self.execution_succeeded is True
            and self.evidence_complete is True
            and self.provenance_valid is True
            and self.state_consistent is True
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "action_id": self.action_id,
            "status": self.status.value,
            "execution_attempted": self.execution_attempted,
            "execution_succeeded": self.execution_succeeded,
            "evidence_complete": self.evidence_complete,
            "provenance_valid": self.provenance_valid,
            "state_consistent": self.state_consistent,
            "successful": self.successful,
            "evidence": dict(self.evidence),
        }


class ExecutionReceiptFactory:
    """
    Deterministic factory for execution receipts.

    This class creates evidence only. It does not execute actions, mutate
    controller state, authorize actions, or discover executors.
    """

    def create(
        self,
        *,
        action_id: str,
        status: ReceiptStatus,
        execution_attempted: bool,
        execution_succeeded: bool,
        evidence_complete: bool,
        provenance_valid: bool,
        state_consistent: bool,
        evidence: Mapping[str, Any] | None = None,
    ) -> ExecutionReceipt:
        """
        Create an immutable execution receipt.

        Inputs are recorded as supplied. No missing safety condition is
        silently converted into success.
        """

        normalized_action_id = (
            action_id if isinstance(action_id, str) else ""
        )

        normalized_status = (
            status
            if isinstance(status, ReceiptStatus)
            else ReceiptStatus.INVALID
        )

        return ExecutionReceipt(
            action_id=normalized_action_id,
            status=normalized_status,
            execution_attempted=execution_attempted is True,
            execution_succeeded=execution_succeeded is True,
            evidence_complete=evidence_complete is True,
            provenance_valid=provenance_valid is True,
            state_consistent=state_consistent is True,
            evidence=dict(evidence or {}),
        )

    def validate(
        self,
        receipt: ExecutionReceipt,
    ) -> ReceiptValidation:
        """
        Validate an execution receipt fail-closed.

        Validation never changes the receipt and never triggers execution.
        """

        failures: list[str] = []

        if not isinstance(receipt, ExecutionReceipt):
            return ReceiptValidation(
                valid=False,
                reason=ReceiptValidationReason.INVALID_STATUS,
                failures=("receipt_type",),
            )

        if not isinstance(receipt.action_id, str) or not receipt.action_id:
            failures.append(
                ReceiptValidationReason.INVALID_ACTION_ID.value
            )

        if not isinstance(receipt.status, ReceiptStatus):
            failures.append(
                ReceiptValidationReason.INVALID_STATUS.value
            )

        if receipt.status is ReceiptStatus.EXECUTED:
            if receipt.execution_attempted is not True:
                failures.append(
                    ReceiptValidationReason.EXECUTION_NOT_ATTEMPTED.value
                )

            if receipt.execution_succeeded is not True:
                failures.append(
                    ReceiptValidationReason.EXECUTION_FAILED.value
                )

            if receipt.evidence_complete is not True:
                failures.append(
                    ReceiptValidationReason.EVIDENCE_INCOMPLETE.value
                )

            if receipt.provenance_valid is not True:
                failures.append(
                    ReceiptValidationReason.PROVENANCE_INVALID.value
                )

            if receipt.state_consistent is not True:
                failures.append(
                    ReceiptValidationReason.STATE_INCONSISTENT.value
                )

        elif receipt.status is ReceiptStatus.FAILED:
            if receipt.execution_succeeded is True:
                failures.append(
                    ReceiptValidationReason.EXECUTION_FAILED.value
                )

        elif receipt.status is ReceiptStatus.BLOCKED:
            if receipt.execution_attempted is True:
                failures.append(
                    ReceiptValidationReason.EXECUTION_NOT_ATTEMPTED.value
                )

        else:
            failures.append(
                ReceiptValidationReason.INVALID_STATUS.value
            )

        if failures:
            return ReceiptValidation(
                valid=False,
                reason=self._primary_failure(failures),
                failures=tuple(failures),
            )

        return ReceiptValidation(
            valid=True,
            reason=ReceiptValidationReason.VALID,
        )

    @staticmethod
    def _primary_failure(
        failures: list[str],
    ) -> ReceiptValidationReason:
        """Map the first deterministic failure to its validation reason."""

        priority = (
            ReceiptValidationReason.INVALID_ACTION_ID,
            ReceiptValidationReason.INVALID_STATUS,
            ReceiptValidationReason.EXECUTION_NOT_ATTEMPTED,
            ReceiptValidationReason.EXECUTION_FAILED,
            ReceiptValidationReason.EVIDENCE_INCOMPLETE,
            ReceiptValidationReason.PROVENANCE_INVALID,
            ReceiptValidationReason.STATE_INCONSISTENT,
        )

        failure_set = set(failures)

        for reason in priority:
            if reason.value in failure_set:
                return reason

        return ReceiptValidationReason.INVALID_STATUS


def create_execution_receipt(
    *,
    action_id: str,
    status: ReceiptStatus,
    execution_attempted: bool,
    execution_succeeded: bool,
    evidence_complete: bool,
    provenance_valid: bool,
    state_consistent: bool,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionReceipt:
    """
    Convenience constructor for one deterministic execution receipt.

    This function has no execution side effects.
    """

    return ExecutionReceiptFactory().create(
        action_id=action_id,
        status=status,
        execution_attempted=execution_attempted,
        execution_succeeded=execution_succeeded,
        evidence_complete=evidence_complete,
        provenance_valid=provenance_valid,
        state_consistent=state_consistent,
        evidence=evidence,
    )


def validate_execution_receipt(
    receipt: ExecutionReceipt,
) -> ReceiptValidation:
    """
    Convenience validator for an execution receipt.

    Validation is deterministic and side-effect free.
    """

    return ExecutionReceiptFactory().validate(receipt)
