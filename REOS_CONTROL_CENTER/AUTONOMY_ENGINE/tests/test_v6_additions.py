"""Tests for AUTONOMY_ENGINE V6 additive components."""

from __future__ import annotations

import json
from pathlib import Path

from orchestration.capability_registry import (
    Capability,
    CapabilityRegistry,
)


ROOT = Path(__file__).resolve().parents[1]


def test_capability_registry_register_and_lookup() -> None:
    registry = CapabilityRegistry()

    capability = Capability(
        capability_id="test.capability",
        name="Test Capability",
        description="Deterministic test capability",
    )

    registry.register(capability)

    assert registry.get("test.capability") == capability
    assert registry.is_enabled("test.capability") is True
    assert registry.ids() == ("test.capability",)


def test_capability_registry_rejects_duplicate() -> None:
    registry = CapabilityRegistry()

    capability = Capability(
        capability_id="duplicate.capability",
        name="Duplicate Capability",
    )

    registry.register(capability)

    try:
        registry.register(capability)
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("duplicate capability was accepted")


def test_action_proposal_schema_exists_and_is_valid_json() -> None:
    path = ROOT / "schemas" / "action_proposal.schema.json"

    assert path.is_file()

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["$schema"]
    assert data["type"] == "object"
    assert "proposal_id" in data["required"]
    assert "capability_id" in data["required"]


def test_session_state_schema_exists_and_is_valid_json() -> None:
    path = ROOT / "schemas" / "session_state.schema.json"

    assert path.is_file()

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["$schema"]
    assert data["type"] == "object"
    assert "session_id" in data["required"]
    assert "status" in data["required"]


def test_v6_paths_are_inside_autonomy_engine() -> None:
    expected_paths = (
        ROOT / "orchestration" / "capability_registry.py",
        ROOT / "schemas" / "action_proposal.schema.json",
        ROOT / "schemas" / "session_state.schema.json",
        ROOT / "tests" / "test_v6_additions.py",
    )

    for path in expected_paths:
        assert path.is_file()
        assert ROOT in path.parents