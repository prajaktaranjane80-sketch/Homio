"""ACRL T06 — machine-readable checkpoint contract."""

from __future__ import annotations

from .checkpoint_engine import (
    CheckpointEngine,
    ExecutionCheckpoint,
)
from .checkpoint_validation import (
    validate_checkpoint,
)


def validate_checkpoint_contract(
    checkpoint: ExecutionCheckpoint,
) -> None:
    """Validate the public T06 checkpoint boundary."""

    if not isinstance(
        checkpoint,
        ExecutionCheckpoint,
    ):
        raise TypeError(
            "checkpoint must be ExecutionCheckpoint."
        )

    if (
        checkpoint.source
        != CheckpointEngine.AUTHORITATIVE_SOURCE
    ):
        raise ValueError(
            "T06 requires REOS_STATE as checkpoint source."
        )

    report = validate_checkpoint(
        checkpoint
    )

    if not report.valid:
        raise ValueError(
            "T06 checkpoint contract validation failed: "
            + "; ".join(report.failures)
        )


def contract_dict() -> dict[str, object]:
    """Return non-authorizing T06 contract metadata."""

    return {
        "schema_version": "1.0",
        "layer": "T06",
        "name": "Checkpoint Engine",
        "mode": "READ_CREATE_VERIFY",
        "authority": {
            "primary_execution_authority": (
                "REOS_STATE"
            ),
            "canonical_state_path": (
                "data/state.json"
            ),
        },
        "capabilities": {
            "checkpoint_creation": True,
            "checkpoint_identity": True,
            "checkpoint_validation": True,
            "checkpoint_registry": True,
            "checkpoint_lifecycle": True,
            "checkpoint_provenance": True,
            "integrity_verification": True,
            "state_projection": True,
            "state_comparison": True,
        },
        "permissions": {
            "read_state": True,
            "create_checkpoint": True,
            "rewrite_checkpoint": False,
            "mutate_reos_state": False,
            "advance_gate": False,
            "authorize_execution": False,
            "approve_changes": False,
            "repair_code": False,
            "modify_architecture": False,
        },
        "guarantees": {
            "immutable_checkpoint": True,
            "deterministic_identity": True,
            "tamper_detection": True,
            "authority_preservation": True,
            "replay_conflict_detection": True,
        },
    }


__all__ = [
    "contract_dict",
    "validate_checkpoint_contract",
]