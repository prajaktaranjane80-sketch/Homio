"""ACRL T06 — checkpoint registry tests."""

from __future__ import annotations

import pytest

from .checkpoint_engine import (
    CheckpointEngine,
)
from .checkpoint_identity import (
    build_checkpoint_identity,
)
from .checkpoint_registry import (
    CheckpointConflictError,
    CheckpointRegistry,
    DuplicateCheckpointError,
)


def make_checkpoint(
    checkpoint_id: str,
    subtask: str = "CORE-004-T06",
):
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-004",
            "current_subtask": subtask,
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id=checkpoint_id,
        created_at="2026-08-31T00:00:00+00:00",
    )


def test_register_and_get():
    registry = CheckpointRegistry()
    checkpoint = make_checkpoint("CP-REG-001")

    entry = registry.register(
        checkpoint
    )

    key = build_checkpoint_identity(
        checkpoint
    ).identity_key()

    assert registry.contains(key)
    assert registry.get(key) == entry
    assert registry.count() == 1


def test_duplicate_identity_is_rejected():
    registry = CheckpointRegistry()
    checkpoint = make_checkpoint("CP-REG-002")

    registry.register(checkpoint)

    with pytest.raises(
        DuplicateCheckpointError
    ):
        registry.register(checkpoint)


def test_conflicting_checkpoint_id_is_rejected():
    registry = CheckpointRegistry()

    registry.register(
        make_checkpoint(
            "CP-REG-003",
            "CORE-004-T06",
        )
    )

    with pytest.raises(
        CheckpointConflictError
    ):
        registry.register(
            make_checkpoint(
                "CP-REG-003",
                "CORE-004-T07",
            )
        )


def test_entries_are_sorted_deterministically():
    registry = CheckpointRegistry()

    registry.register(
        make_checkpoint("CP-REG-005")
    )
    registry.register(
        make_checkpoint("CP-REG-004")
    )

    entries = registry.list_entries()

    assert (
        entries[0]
        .checkpoint
        .metadata
        .checkpoint_id
        == "CP-REG-004"
    )