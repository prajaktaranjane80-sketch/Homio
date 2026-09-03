"""ACRL T02 — architecture lock hardening tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .architecture_contract import (
    contract_dict,
    validate_architecture_lock_contract,
)
from .architecture_drift import (
    ArchitectureDriftStatus,
    detect_architecture_drift,
)
from .architecture_identity import (
    build_architecture_identity,
)
from .architecture_lock import (
    ArchitectureLockReader,
    ArchitectureLockIntegrityError,
)


def _write_state(
    root: Path,
    *,
    architecture_status: str = "FROZEN",
) -> None:
    data = root / "data"
    data.mkdir(parents=True)

    state = {
        "meta": {
            "product": "HOMIO / REOS",
            "schema_version": 3,
            "control_center_version": "7.0"
        },
        "constitution": {
            "canonical_source": "data/state.json",
            "architecture_before_code": True,
            "no_silent_architecture_changes": True,
            "no_duplicate_logic": True
        },
        "architecture": {
            "id": "ARCH-039",
            "version": "1.0",
            "status": architecture_status,
            "phase": "MASTER BLUEPRINT",
            "components": [
                "REOS_CONTROL_CENTER",
                "AUTONOMY_ENGINE"
            ]
        }
    }

    (
        data / "state.json"
    ).write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_default_resolution_points_to_control_center() -> None:
    reader = ArchitectureLockReader()

    assert reader.root.name == "REOS_CONTROL_CENTER"
    assert reader.state_path.name == "state.json"


def test_architecture_identity_is_deterministic(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    lock = ArchitectureLockReader(tmp_path).read()

    first = build_architecture_identity(lock)
    second = build_architecture_identity(lock)

    assert first.identity_key() == second.identity_key()


def test_contract_accepts_valid_lock(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    lock = ArchitectureLockReader(tmp_path).read()

    validate_architecture_lock_contract(lock)


def test_contract_is_non_authorizing() -> None:
    contract = contract_dict()

    assert contract["permissions"]["write_state"] is False
    assert contract["permissions"]["approve_changes"] is False
    assert contract["permissions"]["authorize_execution"] is False


def test_drift_engine_reports_unchanged(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    report = detect_architecture_drift(
        fingerprint,
        reader=reader,
    )

    assert report.status == ArchitectureDriftStatus.UNCHANGED
    assert report.safe is True


def test_drift_engine_reports_drift(
    tmp_path: Path,
) -> None:
    _write_state(tmp_path)

    reader = ArchitectureLockReader(tmp_path)
    fingerprint = reader.read().architecture_fingerprint

    state_path = tmp_path / "data" / "state.json"

    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
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
    assert (
        report.current_fingerprint
        != fingerprint
    )


def test_invalid_state_shape_fails_closed(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    data.mkdir(parents=True)

    (
        data / "state.json"
    ).write_text(
        "[]",
        encoding="utf-8",
    )

    with pytest.raises(
        ArchitectureLockIntegrityError
    ):
        ArchitectureLockReader(tmp_path).read()