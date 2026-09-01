"""ACRL T02 — Architecture Lock tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from AUTONOMY_ENGINE.continuity.acrl.architecture_lock import (
    ArchitectureDriftError,
    ArchitectureLockReader,
    ArchitectureLockSourceError,
    ArchitectureNotLockedError,
)


def _write_state(
    root: Path,
    *,
    architecture_status: str = "FROZEN",
    architecture_before_code: bool = True,
    no_silent_changes: bool = True,
    no_duplicate_logic: bool = True,
) -> None:
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
            "architecture_before_code": architecture_before_code,
            "no_silent_architecture_changes": no_silent_changes,
            "no_duplicate_logic": no_duplicate_logic,
        },
        "architecture": {
            "id": "ARCH-039",
            "version": "1.0",
            "status": architecture_status,
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


def test_reads_frozen_architecture(tmp_path: Path) -> None:
    _write_state(tmp_path)

    lock = ArchitectureLockReader(tmp_path).read()

    assert lock.architecture_id == "ARCH-039"
    assert lock.architecture_version == "1.0"
    assert lock.architecture_status == "FROZEN"
    assert lock.is_locked() is True


def test_projection_is_serializable(tmp_path: Path) -> None:
    _write_state(tmp_path)

    payload = ArchitectureLockReader(tmp_path).read().to_dict()

    assert payload["schema_version"] == "1.0"
    assert payload["architecture_status"] == "FROZEN"
    assert len(payload["architecture_fingerprint"]) == 64
    assert len(payload["source_state_sha256"]) == 64


def test_fingerprint_is_deterministic(tmp_path: Path) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)

    first = reader.read().architecture_fingerprint
    second = reader.read().architecture_fingerprint

    assert first == second


def test_matching_fingerprint_passes(tmp_path: Path) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    verified = reader.verify_fingerprint(fingerprint)

    assert verified.architecture_fingerprint == fingerprint


def test_changed_architecture_is_detected(tmp_path: Path) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    state_path = tmp_path / "data" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["architecture"]["version"] = "2.0"

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    with pytest.raises(ArchitectureDriftError):
        reader.verify_fingerprint(fingerprint)


def test_non_frozen_architecture_is_rejected(tmp_path: Path) -> None:
    _write_state(tmp_path, architecture_status="DRAFT")

    with pytest.raises(ArchitectureNotLockedError):
        ArchitectureLockReader(tmp_path).read()


def test_architecture_before_code_is_required(tmp_path: Path) -> None:
    _write_state(tmp_path, architecture_before_code=False)

    with pytest.raises(ArchitectureNotLockedError):
        ArchitectureLockReader(tmp_path).read()


def test_silent_changes_policy_is_required(tmp_path: Path) -> None:
    _write_state(tmp_path, no_silent_changes=False)

    with pytest.raises(ArchitectureNotLockedError):
        ArchitectureLockReader(tmp_path).read()


def test_duplicate_logic_policy_is_required(tmp_path: Path) -> None:
    _write_state(tmp_path, no_duplicate_logic=False)

    with pytest.raises(ArchitectureNotLockedError):
        ArchitectureLockReader(tmp_path).read()


def test_missing_state_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ArchitectureLockSourceError):
        ArchitectureLockReader(tmp_path).read()