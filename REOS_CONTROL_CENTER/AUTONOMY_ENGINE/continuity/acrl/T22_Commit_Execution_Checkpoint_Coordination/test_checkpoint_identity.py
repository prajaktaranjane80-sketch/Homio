from .checkpoint_identity import (
    canonicalize,
    fingerprint,
)


def test_canonicalization_is_deterministic():
    left = canonicalize(
        {"b": 2, "a": 1}
    )

    right = canonicalize(
        {"a": 1, "b": 2}
    )

    assert left == right


def test_fingerprint_is_deterministic():
    value = {
        "checkpoint": "T22",
        "version": "1.0",
    }

    assert fingerprint(value) == fingerprint(
        value
    )


def test_different_values_have_different_fingerprints():
    assert fingerprint({"a": 1}) != fingerprint(
        {"a": 2}
    )
