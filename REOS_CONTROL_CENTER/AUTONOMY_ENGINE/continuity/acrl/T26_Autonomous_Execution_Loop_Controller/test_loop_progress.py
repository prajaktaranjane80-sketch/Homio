from .loop_progress import (
    detect_no_progress,
    progress_fingerprint,
)


def test_same_progress_detected():
    value = progress_fingerprint(
        iteration=1,
        completed_units=("a",),
        pending_units=("b",),
    )

    assert detect_no_progress(
        value,
        value,
    )


def test_new_progress_is_not_no_progress():
    old = progress_fingerprint(
        iteration=1,
        completed_units=("a",),
        pending_units=("b",),
    )

    new = progress_fingerprint(
        iteration=2,
        completed_units=("a", "b"),
        pending_units=(),
    )

    assert not detect_no_progress(
        old,
        new,
    )
