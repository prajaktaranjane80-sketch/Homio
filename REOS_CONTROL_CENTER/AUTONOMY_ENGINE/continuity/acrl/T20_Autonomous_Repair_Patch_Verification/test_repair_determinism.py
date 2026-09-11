from __future__ import annotations

from .repair_identity import (
    canonicalize,
    fingerprint,
)


def test_canonicalization_is_deterministic():
    first = canonicalize(
        {
            "b": 2,
            "a": 1,
        }
    )

    second = canonicalize(
        {
            "a": 1,
            "b": 2,
        }
    )

    assert first == second


def test_fingerprint_is_deterministic():
    payload = {
        "repair": "T20",
        "scope": [
            "src/app.py",
        ],
    }

    assert fingerprint(payload) == (
        fingerprint(payload)
    )


def test_different_payload_has_different_identity():
    first = fingerprint(
        {
            "value": 1,
        }
    )

    second = fingerprint(
        {
            "value": 2,
        }
    )

    assert first != second
