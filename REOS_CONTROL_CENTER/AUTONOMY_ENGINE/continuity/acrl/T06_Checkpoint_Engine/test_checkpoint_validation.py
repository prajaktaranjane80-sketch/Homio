"""ACRL T06 — checkpoint validation tests."""

from __future__ import annotations

from .checkpoint_engine import (
    CheckpointEngine,
)
from .checkpoint_validation import (
    CheckpointValidationStatus,
    validate_checkpoint,
)


def make_checkpoint():
    return CheckpointEngine.build_checkpoint(
        {
            "phase": "PRE-CODING ARCHITECTURE",
            "current_gate": "CORE-004",
            "current_subtask": "CORE-004-T06",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        checkpoint_id="CP-VAL-001",
        created_at="2026-08-31T00:00:00+00:00",
    )


def test_valid_checkpoint():
    report = validate_checkpoint(
        make_checkpoint()
    )

    assert (
        report.status
        == CheckpointValidationStatus.VALID
    )
    assert report.valid is True
    assert report.failures == ()


def test_tampered_checkpoint_is_invalid():
    checkpoint = make_checkpoint()

    object.__setattr__(
        checkpoint,
        "state_fingerprint",
        "0" * 64,
    )

    report = validate_checkpoint(
        checkpoint
    )

    assert (
        report.status
        == CheckpointValidationStatus.INVALID
    )
    assert report.valid is False


def test_wrong_schema_is_invalid():
    checkpoint = make_checkpoint()

    object.__setattr__(
        checkpoint.metadata,
        "schema_version",
        "999.0",
    )

    report = validate_checkpoint(
        checkpoint
    )

    assert report.valid is False


def test_wrong_source_is_invalid():
    checkpoint = make_checkpoint()

    object.__setattr__(
        checkpoint,
        "source",
        "CHAT_CONTEXT",
    )

    report = validate_checkpoint(
        checkpoint
    )

    assert report.valid is False