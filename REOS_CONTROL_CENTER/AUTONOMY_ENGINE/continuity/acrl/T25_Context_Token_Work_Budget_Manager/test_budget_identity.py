from .budget_identity import (
    canonicalize,
    fingerprint,
)


def test_canonicalization_is_stable():
    assert canonicalize(
        {"b": 2, "a": 1}
    ) == canonicalize(
        {"a": 1, "b": 2}
    )


def test_fingerprint_is_stable():
    value = {
        "layer": "T25",
        "request": "budget",
    }

    assert (
        fingerprint(value)
        == fingerprint(value)
    )


def test_fingerprint_changes_with_input():
    assert fingerprint(
        {"x": 1}
    ) != fingerprint(
        {"x": 2}
    )
