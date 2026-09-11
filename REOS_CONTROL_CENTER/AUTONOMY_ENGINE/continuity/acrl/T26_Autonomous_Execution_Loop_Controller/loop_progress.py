from __future__ import annotations

from .loop_identity import fingerprint


def progress_fingerprint(
    *,
    iteration: int,
    completed_units: tuple[str, ...],
    pending_units: tuple[str, ...],
    scheduler_fingerprint: str = "",
) -> str:
    return fingerprint(
        {
            "iteration": iteration,
            "completed_units": list(
                completed_units
            ),
            "pending_units": list(
                pending_units
            ),
            "scheduler_fingerprint": (
                scheduler_fingerprint
            ),
        }
    )


def detect_no_progress(
    previous_fingerprint: str | None,
    current_fingerprint: str,
) -> bool:
    if previous_fingerprint is None:
        return False

    return (
        previous_fingerprint
        == current_fingerprint
    )
