"""
Adversarial tests for the deterministic execution receipt boundary.

These tests verify that execution receipts:
- remain immutable,
- never execute anything,
- never authorize anything,
- fail closed on incomplete evidence,
- cannot report incomplete execution as successful,
- preserve supplied evidence,
- distinguish BLOCKED / FAILED / EXECUTED states,
- remain deterministic.

This test module is additive. It does not modify controller state,
architecture files, or existing AUTONOMY_ENGINE modules.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import sys

import pytest

# Allow direct execution from the AUTONOMY_ENGINE root while remaining
# compatible with normal pytest package discovery.
ENGINE_ROOT = Path(__file__).resolve().parents[1]

if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from execution.execution_receipt import (  # noqa: E402
    ExecutionReceipt,
    ExecutionReceiptFactory,
    ReceiptStatus,
    ReceiptValidationReason,
    create_execution_receipt,
    validate_execution_receipt,
)


def make_successful_receipt(
    action_id: str = "receipt-001",
    *,
    evidence: dict | None = None,
) -> ExecutionReceipt:
    """Create a fully valid successful execution receipt."""

    return create_execution_receipt(
        action_id=action_id,
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
        evidence=evidence
        or {
            "trace_id": "trace-001",
            "source": "test_execution_receipt_adversarial",
        },
    )


def test_successful_receipt_validates() -> None:
    """A complete successful receipt must validate."""

    receipt = make_successful_receipt()

    validation = validate_execution_receipt(receipt)

    assert validation.valid is True
    assert validation.reason is ReceiptValidationReason.VALID
    assert validation.failures == ()
    assert receipt.successful is True


def test_success_requires_all_completion_conditions() -> None:
    """
    Successful status alone must never be enough to report a successful
    execution.
    """

    incomplete_cases = [
        {
            "execution_attempted": False,
            "execution_succeeded": True,
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
        {
            "execution_attempted": True,
            "execution_succeeded": False,
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
        {
            "execution_attempted": True,
            "execution_succeeded": True,
            "evidence_complete": False,
            "provenance_valid": True,
            "state_consistent": True,
        },
        {
            "execution_attempted": True,
            "execution_succeeded": True,
            "evidence_complete": True,
            "provenance_valid": False,
            "state_consistent": True,
        },
        {
            "execution_attempted": True,
            "execution_succeeded": True,
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": False,
        },
    ]

    for values in incomplete_cases:
        receipt = create_execution_receipt(
            action_id="incomplete-success",
            status=ReceiptStatus.EXECUTED,
            **values,
        )

        validation = validate_execution_receipt(receipt)

        assert validation.valid is False
        assert receipt.successful is False


@pytest.mark.parametrize(
    ("status", "execution_attempted", "execution_succeeded"),
    [
        (ReceiptStatus.BLOCKED, False, False),
        (ReceiptStatus.FAILED, True, False),
        (ReceiptStatus.EXECUTED, True, True),
    ],
)
def test_lifecycle_states_are_deterministic(
    status: ReceiptStatus,
    execution_attempted: bool,
    execution_succeeded: bool,
) -> None:
    """Supported lifecycle states must retain their supplied semantics."""

    receipt = create_execution_receipt(
        action_id="lifecycle-001",
        status=status,
        execution_attempted=execution_attempted,
        execution_succeeded=execution_succeeded,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    assert receipt.status is status
    assert receipt.execution_attempted is execution_attempted
    assert receipt.execution_succeeded is execution_succeeded


def test_blocked_receipt_is_valid_when_execution_was_not_attempted() -> None:
    """A blocked action must not claim that execution occurred."""

    receipt = create_execution_receipt(
        action_id="blocked-001",
        status=ReceiptStatus.BLOCKED,
        execution_attempted=False,
        execution_succeeded=False,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is True
    assert receipt.successful is False


def test_blocked_receipt_with_execution_attempt_is_rejected() -> None:
    """BLOCKED cannot simultaneously claim an execution attempt."""

    receipt = create_execution_receipt(
        action_id="blocked-invalid-001",
        status=ReceiptStatus.BLOCKED,
        execution_attempted=True,
        execution_succeeded=False,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert (
        ReceiptValidationReason.EXECUTION_NOT_ATTEMPTED.value
        in validation.failures
    )


def test_failed_receipt_cannot_claim_success() -> None:
    """FAILED receipts must never report successful execution."""

    receipt = create_execution_receipt(
        action_id="failed-001",
        status=ReceiptStatus.FAILED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert receipt.successful is False
    assert (
        ReceiptValidationReason.EXECUTION_FAILED.value
        in validation.failures
    )


def test_missing_evidence_blocks_success() -> None:
    """Incomplete evidence must fail closed."""

    receipt = create_execution_receipt(
        action_id="evidence-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=False,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert (
        ReceiptValidationReason.EVIDENCE_INCOMPLETE.value
        in validation.failures
    )
    assert receipt.successful is False


def test_invalid_provenance_blocks_success() -> None:
    """Invalid provenance must prevent successful completion."""

    receipt = create_execution_receipt(
        action_id="provenance-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=False,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert (
        ReceiptValidationReason.PROVENANCE_INVALID.value
        in validation.failures
    )


def test_inconsistent_state_blocks_success() -> None:
    """State inconsistency must prevent successful completion."""

    receipt = create_execution_receipt(
        action_id="state-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=False,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert (
        ReceiptValidationReason.STATE_INCONSISTENT.value
        in validation.failures
    )


def test_empty_action_id_is_rejected() -> None:
    """A receipt without an action identity must fail closed."""

    receipt = create_execution_receipt(
        action_id="",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert validation.reason is ReceiptValidationReason.INVALID_ACTION_ID


def test_non_string_action_id_is_normalized_to_invalid_identity() -> None:
    """Malformed action identity must not become a valid receipt."""

    receipt = create_execution_receipt(
        action_id=123,  # type: ignore[arg-type]
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert receipt.action_id == ""
    assert validation.valid is False
    assert validation.reason is ReceiptValidationReason.INVALID_ACTION_ID


def test_invalid_status_is_fail_closed() -> None:
    """Unsupported status values must never validate as execution success."""

    receipt = create_execution_receipt(
        action_id="invalid-status-001",
        status="UNKNOWN",  # type: ignore[arg-type]
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    validation = validate_execution_receipt(receipt)

    assert receipt.status is ReceiptStatus.INVALID
    assert validation.valid is False


def test_factory_preserves_evidence() -> None:
    """Caller-supplied evidence must survive receipt creation."""

    evidence = {
        "trace_id": "trace-123",
        "source": "mutation-boundary",
        "sequence": 7,
    }

    receipt = make_successful_receipt(evidence=evidence)

    assert receipt.evidence["trace_id"] == "trace-123"
    assert receipt.evidence["source"] == "mutation-boundary"
    assert receipt.evidence["sequence"] == 7


def test_receipt_to_dict_is_json_compatible() -> None:
    """Receipt serialization must expose deterministic primitive values."""

    receipt = make_successful_receipt()

    data = receipt.to_dict()

    assert data["action_id"] == "receipt-001"
    assert data["status"] == "EXECUTED"
    assert data["execution_attempted"] is True
    assert data["execution_succeeded"] is True
    assert data["evidence_complete"] is True
    assert data["provenance_valid"] is True
    assert data["state_consistent"] is True
    assert data["successful"] is True
    assert isinstance(data["evidence"], dict)


def test_validation_to_dict_is_json_compatible() -> None:
    """Validation serialization must remain deterministic."""

    validation = validate_execution_receipt(
        make_successful_receipt()
    )

    data = validation.to_dict()

    assert data == {
        "valid": True,
        "reason": "VALID",
        "failures": [],
    }


def test_receipt_is_immutable() -> None:
    """Frozen receipt objects must reject field mutation."""

    receipt = make_successful_receipt()

    with pytest.raises(FrozenInstanceError):
        receipt.action_id = "tampered"  # type: ignore[misc]


def test_receipt_evidence_is_not_the_authority() -> None:
    """
    Evidence metadata must not magically turn an incomplete receipt into
    a successful receipt.
    """

    receipt = create_execution_receipt(
        action_id="authority-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=False,
        evidence_complete=False,
        provenance_valid=False,
        state_consistent=False,
        evidence={
            "authorized": True,
            "success": True,
            "controller": "REOS_CONTROL_CENTER",
        },
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is False
    assert receipt.successful is False


def test_validation_has_no_execution_side_effect() -> None:
    """Receipt validation must be completely side-effect free."""

    calls: list[str] = []

    receipt = make_successful_receipt(
        evidence={
            "executor": lambda: calls.append("called"),
        }
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is True
    assert calls == []


def test_factory_does_not_execute_embedded_executor() -> None:
    """Creating a receipt must never execute supplied evidence objects."""

    calls: list[str] = []

    receipt = make_successful_receipt(
        evidence={
            "executor": lambda: calls.append("called"),
        }
    )

    assert receipt.successful is True
    assert calls == []


def test_factory_creates_independent_evidence_mapping() -> None:
    """Receipt evidence must not depend on later mutation of caller mapping."""

    evidence = {
        "trace_id": "original",
    }

    receipt = make_successful_receipt(evidence=evidence)

    evidence["trace_id"] = "tampered"

    assert receipt.evidence["trace_id"] == "original"


def test_factory_instances_are_stateless() -> None:
    """Separate factory instances must produce independent results."""

    factory_one = ExecutionReceiptFactory()
    factory_two = ExecutionReceiptFactory()

    receipt_one = factory_one.create(
        action_id="factory-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    receipt_two = factory_two.create(
        action_id="factory-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
    )

    assert receipt_one.to_dict() == receipt_two.to_dict()


def test_validation_is_deterministic() -> None:
    """Repeated validation of the same receipt must return the same result."""

    receipt = create_execution_receipt(
        action_id="deterministic-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=False,
        provenance_valid=False,
        state_consistent=False,
    )

    first = validate_execution_receipt(receipt)
    second = validate_execution_receipt(receipt)

    assert first.to_dict() == second.to_dict()


def test_invalid_receipt_object_is_rejected() -> None:
    """Non-receipt objects must fail closed."""

    validation = validate_execution_receipt(
        {"action_id": "fake"}  # type: ignore[arg-type]
    )

    assert validation.valid is False
    assert validation.failures == ("receipt_type",)


def test_successful_receipt_contains_no_authority_behavior() -> None:
    """
    Receipt creation must remain observational.

    This deliberately uses an executor-like callable as evidence and verifies
    that no execution occurs.
    """

    calls: list[str] = []

    receipt = create_execution_receipt(
        action_id="observational-001",
        status=ReceiptStatus.EXECUTED,
        execution_attempted=True,
        execution_succeeded=True,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
        evidence={
            "executor": lambda: calls.append("must-not-run"),
        },
    )

    assert receipt.successful is True
    assert calls == []


def test_failed_execution_remains_terminal_in_receipt() -> None:
    """A failed execution receipt cannot silently become successful."""

    receipt = create_execution_receipt(
        action_id="terminal-001",
        status=ReceiptStatus.FAILED,
        execution_attempted=True,
        execution_succeeded=False,
        evidence_complete=True,
        provenance_valid=True,
        state_consistent=True,
        evidence={
            "failure_type": "RuntimeError",
        },
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is True
    assert receipt.successful is False
    assert receipt.status is ReceiptStatus.FAILED


def test_blocked_execution_preserves_failure_semantics() -> None:
    """Blocked execution remains blocked and non-successful."""

    receipt = create_execution_receipt(
        action_id="blocked-002",
        status=ReceiptStatus.BLOCKED,
        execution_attempted=False,
        execution_succeeded=False,
        evidence_complete=False,
        provenance_valid=False,
        state_consistent=False,
        evidence={
            "block_reason": "POLICY_DENIED",
        },
    )

    validation = validate_execution_receipt(receipt)

    assert validation.valid is True
    assert receipt.successful is False
    assert receipt.evidence["block_reason"] == "POLICY_DENIED"