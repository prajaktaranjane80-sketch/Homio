"""ACRL T06 — checkpoint lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .checkpoint_engine import ExecutionCheckpoint
from .checkpoint_validation import (
    validate_checkpoint,
)


class CheckpointLifecycleState(
    str,
    Enum,
):
    CREATED = "CREATED"
    VALID = "VALID"
    SUPERSEDED = "SUPERSEDED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class CheckpointLifecycle:
    """Immutable checkpoint lifecycle projection."""

    checkpoint_id: str
    state: CheckpointLifecycleState


def derive_checkpoint_lifecycle(
    checkpoint: ExecutionCheckpoint,
) -> CheckpointLifecycle:
    """Derive lifecycle state without mutating checkpoint."""

    report = validate_checkpoint(
        checkpoint
    )

    if report.valid:
        state = (
            CheckpointLifecycleState.VALID
        )
    else:
        state = (
            CheckpointLifecycleState.INVALID
        )

    return CheckpointLifecycle(
        checkpoint_id=(
            checkpoint.metadata.checkpoint_id
        ),
        state=state,
    )


def supersede_checkpoint(
    lifecycle: CheckpointLifecycle,
) -> CheckpointLifecycle:
    """Return a new superseded lifecycle projection."""

    if not isinstance(
        lifecycle,
        CheckpointLifecycle,
    ):
        raise TypeError(
            "lifecycle must be CheckpointLifecycle."
        )

    if lifecycle.state not in {
        CheckpointLifecycleState.VALID,
        CheckpointLifecycleState.CREATED,
    }:
        raise ValueError(
            "Only valid or created checkpoints can be superseded."
        )

    return CheckpointLifecycle(
        checkpoint_id=lifecycle.checkpoint_id,
        state=CheckpointLifecycleState.SUPERSEDED,
    )


__all__ = [
    "CheckpointLifecycle",
    "CheckpointLifecycleState",
    "derive_checkpoint_lifecycle",
    "supersede_checkpoint",
]