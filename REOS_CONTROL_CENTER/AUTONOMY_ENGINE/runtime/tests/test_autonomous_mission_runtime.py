from __future__ import annotations

import hashlib
import json
from pathlib import Path

from autonomous_mission_runtime import AutonomousMissionRuntime


def state_hash(state: dict) -> str:
    clone = json.loads(json.dumps(state))
    clone.setdefault("integrity", {})["sha256"] = None
    raw = json.dumps(clone, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "REOS_CONTROL_CENTER"
    (root / "data").mkdir(parents=True)
    plan = {
        "authority": {
            "canonical_project_state": "REOS_CONTROL_CENTER/data/state.json"
        },
        "phases": [{"id": "P0", "name": "test"}],
    }
    state = {
        "execution": {
            "current_gate": "CORE-004",
            "current_task": "CORE-004-T02",
            "current_subtask": "CORE-004-T02",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "execution_plan": {
            "authoritative_sequence": [
                {"gate": "CORE-004", "status": "CURRENT"},
                {"gate": "CORE-005", "status": "PENDING"},
            ]
        },
        "gate_plans": {
            "CORE-004": {
                "status": "CURRENT",
                "criteria_state": [
                    {"status": "VERIFIED"},
                    {"status": "PENDING"},
                ],
            }
        },
        "integrity": {"sha256": None},
    }
    state["integrity"]["sha256"] = state_hash(state)
    plan_path = root / "HOMIO_AUTONOMOUS_MASTER_PLAN.json"
    state_path = root / "data" / "state.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    state_path.write_text(json.dumps(state), encoding="utf-8")
    return plan_path, state_path


def test_builder_decision_is_non_mutating(tmp_path: Path):
    plan_path, state_path = write_fixture(tmp_path)
    before = state_path.read_text(encoding="utf-8")
    runtime = AutonomousMissionRuntime(
        root=plan_path.parents[0],
        master_plan_path=plan_path,
        state_path=state_path,
    )
    decision = runtime.decide()
    assert decision.status == "READY"
    assert decision.action is not None
    assert decision.action.requires_mutation is False
    assert decision.action.kind == "INSPECT_CURRENT_SUBTASK"
    assert state_path.read_text(encoding="utf-8") == before


def test_integrity_failure_blocks(tmp_path: Path):
    plan_path, state_path = write_fixture(tmp_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["execution"]["current_task"] = "tampered"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    runtime = AutonomousMissionRuntime(
        root=plan_path.parents[0],
        master_plan_path=plan_path,
        state_path=state_path,
    )
    try:
        runtime.decide()
    except RuntimeError as exc:
        assert "integrity" in str(exc).lower()
    else:
        raise AssertionError("integrity failure must fail closed")


def test_duplicate_current_gate_blocks(tmp_path: Path):
    plan_path, state_path = write_fixture(tmp_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["execution_plan"]["authoritative_sequence"].append(
        {"gate": "CORE-006", "status": "CURRENT"}
    )
    state["integrity"]["sha256"] = state_hash(state)
    state_path.write_text(json.dumps(state), encoding="utf-8")
    runtime = AutonomousMissionRuntime(
        root=plan_path.parents[0],
        master_plan_path=plan_path,
        state_path=state_path,
    )
    decision = runtime.decide()
    assert decision.status == "BLOCKED"
    assert "CURRENT_GATE_NOT_UNIQUE" in decision.blockers
