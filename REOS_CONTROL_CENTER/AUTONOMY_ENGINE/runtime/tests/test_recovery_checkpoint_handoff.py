from __future__ import annotations

from pathlib import Path

from checkpoint_runtime import CheckpointRuntime
from handoff_runtime import HandoffRecord, HandoffRuntime
from recovery_runtime import RecoveryRuntime


def test_terminal_failure_escalates():
    runtime = RecoveryRuntime()

    result = runtime.classify(
        "STATE_INTEGRITY_FAILURE"
    )

    assert result.status == "ESCALATE"
    assert result.retry_allowed is False
    assert result.recoverable is False
    assert result.escalate is True


def test_recoverable_failure_does_not_auto_retry():
    runtime = RecoveryRuntime()

    result = runtime.classify(
        "TRANSIENT_TIMEOUT"
    )

    assert result.status == "RECOVERABLE"
    assert result.retry_allowed is False
    assert result.recoverable is True


def test_unknown_failure_escalates():
    runtime = RecoveryRuntime()

    result = runtime.classify(
        "UNKNOWN_FAILURE"
    )

    assert result.status == "UNKNOWN"
    assert result.escalate is True
    assert result.retry_allowed is False


def test_checkpoint_intent():
    runtime = CheckpointRuntime()

    result = runtime.prepare(
        checkpoint_id="CP-TEST-001",
        mission_id="MISSION-001",
        note="verified runtime checkpoint",
        evidence={
            "test": True,
        },
    )

    assert result.checkpoint_id == "CP-TEST-001"
    assert result.mission_id == "MISSION-001"
    assert result.evidence["test"] is True


def test_checkpoint_requires_note():
    runtime = CheckpointRuntime()

    import pytest

    with pytest.raises(ValueError):
        runtime.prepare(
            checkpoint_id="CP-TEST-001",
            mission_id="MISSION-001",
            note="",
            evidence={},
        )


def test_handoff_roundtrip(tmp_path: Path):
    path = tmp_path / "handoff.json"

    runtime = HandoffRuntime(path)

    original = HandoffRecord(
        handoff_id="HANDOFF-001",
        mission_id="MISSION-001",
        current_gate="CORE-004",
        current_task="CORE-004-T02",
        current_subtask="CORE-004-T02",
        status="READY",
        blockers=(),
        next_action="inspect current subtask",
        evidence_fingerprint="abc123",
    )

    runtime.write(original)

    restored = runtime.read()

    assert restored is not None
    assert restored.handoff_id == original.handoff_id
    assert restored.mission_id == original.mission_id
    assert restored.current_gate == "CORE-004"
    assert restored.current_subtask == "CORE-004-T02"
    assert restored.next_action == "inspect current subtask"


def test_missing_handoff_returns_none(tmp_path: Path):
    runtime = HandoffRuntime(
        tmp_path / "missing.json"
    )

    assert runtime.read() is None
