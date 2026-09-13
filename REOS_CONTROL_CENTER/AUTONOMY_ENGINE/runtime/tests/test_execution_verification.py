from __future__ import annotations

import pytest

from execution_runtime import (
    ExecutionIntent,
    ExecutionRuntime,
)
from verification_runtime import VerificationRuntime


def test_execution_runtime_requires_authorization_for_mutation():
    runtime = ExecutionRuntime()

    intent = ExecutionIntent(
        action="modify",
        target="inventory",
        reason="test",
        requires_mutation=True,
        risk_level="MEDIUM",
    )

    with pytest.raises(PermissionError):
        runtime.prepare(
            intent,
            evidence={},
        )


def test_execution_envelope_is_not_ready_by_default():
    runtime = ExecutionRuntime()

    intent = ExecutionIntent(
        action="inspect",
        target="inventory",
        reason="inspection",
        requires_mutation=False,
        risk_level="LOW",
    )

    envelope = runtime.prepare(
        intent,
        evidence={
            "source": "test",
        },
    )

    assert runtime.ready(envelope) is False


def test_execution_envelope_ready_when_all_boundaries_positive():
    runtime = ExecutionRuntime()

    intent = ExecutionIntent(
        action="controlled_mutation",
        target="inventory",
        reason="authorized test",
        requires_mutation=True,
        risk_level="MEDIUM",
    )

    envelope = runtime.prepare(
        intent,
        evidence={
            "source": "test",
        },
        authorized=True,
        capability_available=True,
        policy_allowed=True,
        guard_allowed=True,
        idempotency_clear=True,
        tripwires_clear=True,
    )

    assert runtime.ready(envelope) is True


def test_verification_passes():
    runtime = VerificationRuntime()

    result = runtime.verify(
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        }
    )

    assert result.status == "VERIFIED"
    assert result.passed is True
    assert result.blockers == ()


def test_verification_blocks_missing_evidence():
    runtime = VerificationRuntime()

    result = runtime.verify(
        postflight={
            "evidence_complete": False,
            "provenance_valid": True,
            "state_consistent": True,
        }
    )

    assert result.status == "BLOCKED"
    assert result.passed is False
    assert (
        "POSTFLIGHT_EVIDENCE_COMPLETE_FAILED"
        in result.blockers
    )


def test_unexpected_state_change_blocks():
    runtime = VerificationRuntime()

    result = runtime.verify(
        postflight={
            "evidence_complete": True,
            "provenance_valid": True,
            "state_consistent": True,
        },
        expected_state_changed=False,
        actual_state_changed=True,
    )

    assert result.status == "BLOCKED"
    assert "UNEXPECTED_STATE_CHANGE" in result.blockers
