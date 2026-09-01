"""ACRL T06 — Checkpoint Engine tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.checkpoint_engine import (
    CheckpointEngine,
    CheckpointIntegrityError,
    CheckpointSourceError,
    CheckpointValidationError,
    ExecutionCheckpoint,
)


def make_state() -> dict[str, object]:
    return {
        "phase": "PRE-CODING ARCHITECTURE",
        "current_gate": "CORE-004",
        "current_subtask": "CORE-004-T06",
        "status": "CONTROL_CENTER_DRIVEN",
        "extra": {
            "example": True,
        },
    }


def test_checkpoint_can_be_created() -> None:
    checkpoint = CheckpointEngine.build_checkpoint(
        make_state(),
        checkpoint_id="CP-001",
        created_at="2026-08-31T00:00:00+00:00",
    )

    assert isinstance(
        checkpoint,
        ExecutionCheckpoint,
    )

    assert checkpoint.metadata.checkpoint_id == "CP-001"
    assert checkpoint.source == "REOS_STATE"


def test_checkpoint_uses_reos_state_as_authority() -> None:
    checkpoint = CheckpointEngine.build_checkpoint(
        make_state(),
        checkpoint_id="CP-002",
    )

    assert (
        checkpoint.source
        == CheckpointEngine.AUTHORITATIVE_SOURCE
    )

    assert (
        CheckpointEngine.AUTHORITATIVE_SOURCE
        == "REOS_STATE"
    )


def test_checkpoint_preserves_state_snapshot() -> None:
    state = make_state()

    checkpoint = CheckpointEngine.build_checkpoint(
        state,
        checkpoint_id="CP-003",
    )

    assert dict(checkpoint.state_snapshot) == state


def test_state_fingerprint_is_deterministic() -> None:
    state = make_state()

    first = CheckpointEngine.calculate_state_fingerprint(
        state
    )

    second = CheckpointEngine.calculate_state_fingerprint(
        state
    )

    assert first == second
    assert len(first) == 64


def test_checkpoint_fingerprint_is_deterministic() -> None:
    state = make_state()

    first = CheckpointEngine.build_checkpoint(
        state,
        checkpoint_id="CP-004",
        created_at="2026-08-31T00:00:00+00:00",
    )

    second = CheckpointEngine.build_checkpoint(
        state,
        checkpoint_id="CP-004",
        created_at="2026-08-31T00:00:00+00:00",
    )

    assert (
        first.checkpoint_fingerprint
        == second.checkpoint_fingerprint
    )


def test_checkpoint_integrity_verifies() -> None:
    checkpoint = CheckpointEngine.build_checkpoint(
        make_state(),
        checkpoint_id="CP-005",
    )

    assert checkpoint.verify_integrity() is True


def test_checkpoint_can_restore_state_projection() -> None:
    state = make_state()

    checkpoint = CheckpointEngine.build_checkpoint(
        state,
        checkpoint_id="CP-006",
    )

    restored = CheckpointEngine.restore_state(
        checkpoint
    )

    assert restored == state


def test_checkpoint_matches_current_state() -> None:
    state = make_state()

    checkpoint = CheckpointEngine.build_checkpoint(
        state,
        checkpoint_id="CP-007",
    )

    assert (
        CheckpointEngine.compare_checkpoint_state(
            checkpoint,
            state,
        )
        is True
    )


def test_checkpoint_detects_state_difference() -> None:
    state = make_state()

    checkpoint = CheckpointEngine.build_checkpoint(
        state,
        checkpoint_id="CP-008",
    )

    changed = dict(state)
    changed["current_subtask"] = "CORE-004-T07"

    assert (
        CheckpointEngine.compare_checkpoint_state(
            checkpoint,
            changed,
        )
        is False
    )


def test_missing_phase_is_rejected() -> None:
    state = make_state()
    state.pop("phase")

    with pytest.raises(CheckpointSourceError):
        CheckpointEngine.build_checkpoint(
            state,
            checkpoint_id="CP-009",
        )


def test_missing_gate_is_rejected() -> None:
    state = make_state()
    state.pop("current_gate")

    with pytest.raises(CheckpointSourceError):
        CheckpointEngine.build_checkpoint(
            state,
            checkpoint_id="CP-010",
        )


def test_missing_subtask_is_rejected() -> None:
    state = make_state()
    state.pop("current_subtask")

    with pytest.raises(CheckpointSourceError):
        CheckpointEngine.build_checkpoint(
            state,
            checkpoint_id="CP-011",
        )


def test_empty_checkpoint_id_is_rejected() -> None:
    with pytest.raises(CheckpointValidationError):
        CheckpointEngine.build_checkpoint(
            make_state(),
            checkpoint_id="",
        )


def test_invalid_checkpoint_is_rejected_on_restore() -> None:
    checkpoint = CheckpointEngine.build_checkpoint(
        make_state(),
        checkpoint_id="CP-012",
    )

    object.__setattr__(
        checkpoint,
        "state_fingerprint",
        "invalid",
    )

    with pytest.raises(CheckpointIntegrityError):
        CheckpointEngine.restore_state(
            checkpoint
        )


def test_checkpoint_summary_contains_recovery_position() -> None:
    checkpoint = CheckpointEngine.build_checkpoint(
        make_state(),
        checkpoint_id="CP-013",
    )

    summary = CheckpointEngine.checkpoint_summary(
        checkpoint
    )

    assert summary["checkpoint_id"] == "CP-013"
    assert summary["current_gate"] == "CORE-004"
    assert (
        summary["current_subtask"]
        == "CORE-004-T06"
    )
    assert summary["status"] == "CONTROL_CENTER_DRIVEN"