"""ACRL T06 — checkpoint provenance tests."""

from __future__ import annotations

from .checkpoint_engine import (
    CheckpointEngine,
)
from .checkpoint_provenance import (
    CheckpointProvenance,
    build_checkpoint_provenance,
)


def make_checkpoint():
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-004",
            "current_subtask": "CORE-004-T06",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id="CP-PROV-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def test_provenance_is_deterministic():
    checkpoint = make_checkpoint()

    first = build_checkpoint_provenance(
        checkpoint
    )
    second = build_checkpoint_provenance(
        checkpoint
    )

    assert isinstance(
        first,
        CheckpointProvenance,
    )
    assert first == second


def test_provenance_preserves_authority():
    provenance = build_checkpoint_provenance(
        make_checkpoint()
    )

    assert (
        provenance.authoritative_source
        == "REOS_STATE"
    )
    assert (
        provenance.authoritative_state_path
        == "data/state.json"
    )


def test_provenance_contains_identity():
    provenance = build_checkpoint_provenance(
        make_checkpoint()
    )

    assert (
        len(provenance.checkpoint_identity)
        == 64
    )