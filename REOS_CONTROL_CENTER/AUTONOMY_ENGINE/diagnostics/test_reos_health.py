"""
Tests for the REOS Health Diagnostic Engine.

These tests intentionally validate the diagnostic surface itself.

They do not mutate the canonical project state.
"""

from __future__ import annotations

import json
from pathlib import Path

from .reos_health import REOSHealth


def _create_project(tmp_path: Path) -> Path:
    """
    Create the minimum valid REOS structure required by the diagnostic.
    """

    root = tmp_path / "repo"

    control_center = root / "REOS_CONTROL_CENTER"
    autonomy = control_center / "AUTONOMY_ENGINE"
    acrl = autonomy / "continuity" / "acrl"
    runtime = autonomy / "runtime"
    data = control_center / "data"

    acrl.mkdir(parents=True)
    runtime.mkdir(parents=True)
    data.mkdir(parents=True)

    (runtime / "mission_cycle.py").write_text(
        "# test runtime mission cycle\n",
        encoding="utf-8",
    )

    (runtime / "checkpoint_runtime.py").write_text(
        "# test checkpoint runtime\n",
        encoding="utf-8",
    )

    (runtime / "handoff_runtime.py").write_text(
        "# test handoff runtime\n",
        encoding="utf-8",
    )

    state = {
        "current_gate": "CORE-004",
        "current_task": "CORE-004-T02",
        "current_subtask": "inventory-domain",
        "architecture_status": "LOCKED",
    }

    (data / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    return root


def test_health_passes_for_valid_reos_structure(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    report = REOSHealth(root).run()

    assert report.result == "PASS"
    assert not report.failed


def test_health_reports_missing_runtime(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    runtime = (
        root
        / "REOS_CONTROL_CENTER"
        / "AUTONOMY_ENGINE"
        / "runtime"
    )

    for file in runtime.iterdir():
        file.unlink()

    report = REOSHealth(root).run()

    assert report.result == "BLOCKED"

    runtime_check = next(
        check
        for check in report.checks
        if check.name == "RUNTIME"
    )

    assert runtime_check.status == "BLOCKED"


def test_health_reports_missing_state(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    state_file = (
        root
        / "REOS_CONTROL_CENTER"
        / "data"
        / "state.json"
    )

    state_file.unlink()

    report = REOSHealth(root).run()

    assert report.result == "BLOCKED"

    state_check = next(
        check
        for check in report.checks
        if check.name == "STATE"
    )

    assert state_check.status == "BLOCKED"


def test_health_reports_invalid_state_json(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    state_file = (
        root
        / "REOS_CONTROL_CENTER"
        / "data"
        / "state.json"
    )

    state_file.write_text(
        "{invalid-json",
        encoding="utf-8",
    )

    report = REOSHealth(root).run()

    assert report.result == "BLOCKED"

    state_check = next(
        check
        for check in report.checks
        if check.name == "STATE"
    )

    assert state_check.status == "BLOCKED"


def test_health_reports_missing_acrl(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    acrl = (
        root
        / "REOS_CONTROL_CENTER"
        / "AUTONOMY_ENGINE"
        / "continuity"
        / "acrl"
    )

    acrl.rmdir()

    report = REOSHealth(root).run()

    assert report.result == "BLOCKED"

    acrl_check = next(
        check
        for check in report.checks
        if check.name == "ACRL"
    )

    assert acrl_check.status == "BLOCKED"


def test_health_reports_missing_mission_cycle(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    mission_cycle = (
        root
        / "REOS_CONTROL_CENTER"
        / "AUTONOMY_ENGINE"
        / "runtime"
        / "mission_cycle.py"
    )

    mission_cycle.unlink()

    report = REOSHealth(root).run()

    assert report.result == "BLOCKED"

    check = next(
        check
        for check in report.checks
        if check.name == "MISSION_CYCLE"
    )

    assert check.status == "BLOCKED"


def test_health_reports_missing_checkpoint(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    checkpoint = (
        root
        / "REOS_CONTROL_CENTER"
        / "AUTONOMY_ENGINE"
        / "runtime"
        / "checkpoint_runtime.py"
    )

    checkpoint.unlink()

    report = REOSHealth(root).run()

    assert report.result == "BLOCKED"

    check = next(
        check
        for check in report.checks
        if check.name == "CHECKPOINT"
    )

    assert check.status == "BLOCKED"


def test_health_is_read_only(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    state_file = (
        root
        / "REOS_CONTROL_CENTER"
        / "data"
        / "state.json"
    )

    before = state_file.read_bytes()

    REOSHealth(root).run()

    after = state_file.read_bytes()

    assert before == after


def test_health_exposes_current_position(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    report = REOSHealth(root).run()

    assert report.current_gate == "CORE-004"
    assert report.current_task == "CORE-004-T02"
    assert report.current_subtask == "inventory-domain"


def test_compact_output_is_small_and_machine_stable(
    tmp_path: Path,
) -> None:
    root = _create_project(tmp_path)

    output = REOSHealth(root).compact()

    assert "REOS HEALTH" in output
    assert "CONTROL_CENTER" in output
    assert "STATE" in output
    assert "ARCHITECTURE" in output
    assert "AUTONOMY_ENGINE" in output
    assert "ACRL" in output
    assert "RUNTIME" in output
    assert "MISSION_CYCLE" in output
    assert "CHECKPOINT" in output
    assert "RECOVERY" in output
    assert "INTEGRATION" in output
    assert "RESULT" in output
    assert "PASS" in output


def test_json_output_is_machine_readable(tmp_path: Path) -> None:
    root = _create_project(tmp_path)

    engine = REOSHealth(root)

    payload = json.loads(engine.json())

    assert payload["schema_version"] == "1.0"
    assert payload["module"] == "REOS_HEALTH"
    assert payload["result"] == "PASS"
    assert isinstance(payload["checks"], list)


def test_failed_health_contains_targeted_next_action(
    tmp_path: Path,
) -> None:
    root = _create_project(tmp_path)

    runtime = (
        root
        / "REOS_CONTROL_CENTER"
        / "AUTONOMY_ENGINE"
        / "runtime"
    )

    for file in runtime.iterdir():
        file.unlink()

    output = REOSHealth(root).compact()

    assert "RESULT" in output
    assert "BLOCKED" in output
    assert "RUNTIME" in output
    assert "NEXT" in output
