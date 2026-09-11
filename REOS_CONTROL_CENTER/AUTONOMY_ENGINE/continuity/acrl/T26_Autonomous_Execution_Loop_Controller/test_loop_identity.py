from .loop_identity import (
    canonicalize,
    fingerprint,
    iteration_fingerprint,
)


def test_canonicalization():
    assert canonicalize(
        {"b": 2, "a": 1}
    ) == canonicalize(
        {"a": 1, "b": 2}
    )


def test_fingerprint_stable():
    value = {
        "layer": "T26",
        "loop": "test",
    }

    assert (
        fingerprint(value)
        == fingerprint(value)
    )


def test_iteration_identity_stable():
    first = iteration_fingerprint(
        "loop",
        1,
        "a" * 64,
        "b" * 64,
    )

    second = iteration_fingerprint(
        "loop",
        1,
        "a" * 64,
        "b" * 64,
    )

    assert first == second
