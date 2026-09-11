from .continuity_identity import (
    canonicalize,
    fingerprint,
)


def test_canonicalization():
    assert canonicalize(
        {"b": 2, "a": 1}
    ) == canonicalize(
        {"a": 1, "b": 2}
    )


def test_fingerprint_stable():
    value = {
        "project": "HOMIO",
        "layer": "T24",
    }

    assert (
        fingerprint(value)
        == fingerprint(value)
    )


def test_fingerprint_changes():
    assert fingerprint(
        {"x": 1}
    ) != fingerprint(
        {"x": 2}
    )
