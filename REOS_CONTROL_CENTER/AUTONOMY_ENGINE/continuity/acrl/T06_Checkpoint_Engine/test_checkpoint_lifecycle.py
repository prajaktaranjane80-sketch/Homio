"""ACRL T06 — checkpoint lifecycle tests."""

from __future__ import annotations

import pytest

from .checkpoint_engine import (
    CheckpointEngine,
)
from .checkpoint_lifecycle import (
    CheckpointLifecycleState,
    derive_checkpoint_lifecycle,
    supersede_checkpoint,
)


def make_checkpoint():
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-004",
            "current_subtask": "CORE-004-T06",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id="CP-LIFE-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def test_valid_checkpoint_lifecycle():
    lifecycle = derive_checkpoint_lifecycle(
        make_checkpoint()
    )

    assert (
        lifecycle.state
        == CheckpointLifecycleState.VALID
    )


def test_valid_checkpoint_can_be_superseded():
    lifecycle = derive_checkpoint_lifecycle(
        make_checkpoint()
    )

    superseded = supersede_checkpoint(
        lifecycle
    )

    assert (
        superseded.state
        == CheckpointLifecycleState.SUPERSEDED
    )


def test_invalid_lifecycle_cannot_be_superseded():
    lifecycle = derive_checkpoint_lifecycle(
        make_checkpoint()
    )

    invalid = type(lifecycle)(
        checkpoint_id=lifecycle.checkpoint_id,
        state=CheckpointLifecycleState.INVALID,
    )

    with pytest.raises(ValueError):
        supersede_checkpoint(invalid)