"""ACRL T03 — state identity tests."""

from __future__ import annotations

from .state_identity import build_state_identity


def test_semantic_identity_is_deterministic() -> None:
    state = {
        "gate": "CORE-005",
        "pending": ["T01", "T02"],
    }

    first = build_state_identity(
        state,
        "a" * 64,
    )

    second = build_state_identity(
        state,
        "a" * 64,
    )

    assert first.semantic_sha256 == second.semantic_sha256
    assert first.identity_key() == second.identity_key()


def test_semantic_hash_ignores_mapping_order() -> None:
    first = build_state_identity(
        {"a": 1, "b": 2},
        "a" * 64,
    )

    second = build_state_identity(
        {"b": 2, "a": 1},
        "a" * 64,
    )

    assert first.semantic_sha256 == second.semantic_sha256


def test_source_hash_participates_in_identity() -> None:
    first = build_state_identity(
        {"a": 1},
        "a" * 64,
    )

    second = build_state_identity(
        {"a": 1},
        "b" * 64,
    )

    assert first.semantic_sha256 == second.semantic_sha256
    assert first.identity_key() != second.identity_key()


def test_identity_serializes() -> None:
    identity = build_state_identity(
        {"a": 1},
        "a" * 64,
    )

    payload = identity.to_dict()

    assert payload["schema_version"] == "1.0"
    assert len(payload["semantic_sha256"]) == 64
    assert len(payload["source_sha256"]) == 64
