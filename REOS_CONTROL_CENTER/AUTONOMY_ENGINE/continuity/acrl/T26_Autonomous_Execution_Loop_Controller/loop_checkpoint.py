from __future__ import annotations


def validate_checkpoint_binding(
    loop,
    checkpoint_result,
) -> None:
    if checkpoint_result is None:
        raise ValueError(
            "Execution checkpoint is required."
        )

    decision = getattr(
        getattr(
            checkpoint_result,
            "decision",
            None,
        ),
        "value",
        None,
    )

    if decision not in {
        "CHECKPOINT_CREATED",
        "READ_ONLY",
    }:
        raise ValueError(
            "T22 checkpoint is not valid for loop control."
        )

    checkpoint = getattr(
        checkpoint_result,
        "checkpoint",
        None,
    )

    if checkpoint is None:
        raise ValueError(
            "Checkpoint payload is missing."
        )

    if (
        checkpoint.checkpoint_fingerprint
        != loop.checkpoint_fingerprint
    ):
        raise ValueError(
            "Checkpoint fingerprint mismatch."
        )

    if (
        checkpoint.checkpoint_id
        != loop.checkpoint_id
    ):
        raise ValueError(
            "Checkpoint identity mismatch."
        )
