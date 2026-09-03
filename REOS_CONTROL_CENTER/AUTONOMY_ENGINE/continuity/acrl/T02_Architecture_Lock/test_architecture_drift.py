"""ACRL T02 — Architecture Drift Detection tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .architecture_drift import (
    ArchitectureDriftStatus,
    detect_architecture_drift,
)
from .architecture_lock import ArchitectureLockReader


def _write_state(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "product": "HOMIO / REOS",
            "schema_version": 3,
            "control_center_version": "7.0",
        },
        "constitution": {
            "canonical_source": "data/state.json",
            "architecture_before_code": True,
            "no_silent_architecture_changes": True,
            "no_duplicate_logic": True,
        },
        "architecture": {
            "id": "ARCH-039",
            "version": "1.0",
            "status": "FROZEN",
            "phase": "MASTER BLUEPRINT",
            "components": [
                "REOS_CONTROL_CENTER",
                "AUTONOMY_ENGINE",
            ],
        },
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_unchanged_architecture_is_safe(tmp_path: Path) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    report = detect_architecture_drift(
        fingerprint,
        reader=reader,
    )

    assert report.status == ArchitectureDriftStatus.UNCHANGED
    assert report.safe is True
    assert report.current_fingerprint == fingerprint


def test_changed_architecture_is_drifted(tmp_path: Path) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(
        state_path.read_text(encoding="utf-8")
    )

    state["architecture"]["version"] = "2.0"

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    report = detect_architecture_drift(
        fingerprint,
        reader=reader,
    )

    assert report.status == ArchitectureDriftStatus.DRIFTED
    assert report.safe is False
    assert report.current_fingerprint != fingerprint


def test_missing_authority_is_unavailable(
    tmp_path: Path,
) -> None:
    reader = ArchitectureLockReader(tmp_path)

    report = detect_architecture_drift(
        "0" * 64,
        reader=reader,
    )

    assert report.status == ArchitectureDriftStatus.UNAVAILABLE
    assert report.safe is False
    assert report.current_fingerprint is None


def test_empty_fingerprint_is_rejected() -> None:
    with pytest.raises(ValueError):
        detect_architecture_drift("")


def test_non_string_fingerprint_is_rejected() -> None:
    with pytest.raises(TypeError):
        detect_architecture_drift(123)  # type: ignore[arg-type]


def test_report_serializes(tmp_path: Path) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    report = detect_architecture_drift(
        fingerprint,
        reader=reader,
    )

    payload = report.to_dict()

    assert payload["status"] == "UNCHANGED"
    assert payload["safe"] is True
    assert payload["expected_fingerprint"] == fingerprint
