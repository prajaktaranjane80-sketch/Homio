from .evidence_identity import (
    canonicalize,
    fingerprint,
)


def test_canonicalize_is_deterministic():
    assert canonicalize(
        {"b": 2, "a": 1}
    ) == canonicalize(
        {"a": 1, "b": 2}
    )


def test_fingerprint_is_deterministic():
    value = {
        "layer": "T23",
        "subject": "commit",
    }

    assert (
        fingerprint(value)
        == fingerprint(value)
    )


def test_different_values_change_identity():
    assert fingerprint(
        {"x": 1}
    ) != fingerprint(
        {"x": 2}
    )
