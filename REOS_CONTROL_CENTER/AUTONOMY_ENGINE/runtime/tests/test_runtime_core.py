from __future__ import annotations

from pathlib import Path

from mission_cycle import MissionCycleEngine
from autonomous_mission_runtime import AutonomousMissionRuntime
from work_context import ContextItem, WorkContext
from evidence_runtime import EvidenceRuntime


def build_fixture(tmp_path: Path):
    root = tmp_path / "REOS_CONTROL_CENTER"
    (root / "data").mkdir(parents=True)

    plan = {
        "authority": {
            "canonical_project_state": "REOS_CONTROL_CENTER/data/state.json"
        },
        "phases": [{"id": "P2", "name": "HOMIO Autonomous Build"}],
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

    runtime = AutonomousMissionRuntime

    state["integrity"]["sha256"] = runtime._calculate_hash(state)

    plan_path = root / "HOMIO_AUTONOMOUS_MASTER_PLAN.json"
    state_path = root / "data" / "state.json"

    import json

    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    state_path.write_text(json.dumps(state), encoding="utf-8")

    return root, plan_path, state_path


def test_work_context_redacts_secrets():
    context = WorkContext()

    result = context.compile(
        [
            ContextItem(
                "SECURITY",
                "token",
                "SECRET-VALUE",
                100,
            ),
            ContextItem(
                "MISSION",
                "task",
                "CORE-004-T02",
                90,
            ),
        ]
    )

    values = {
        item["key"]: item["value"]
        for item in result["items"]
    }

    assert values["token"] == "[REDACTED]"
    assert values["task"] == "CORE-004-T02"
    assert result["full_file_dump"] is False


def test_work_context_is_bounded():
    context = WorkContext(
        max_items=2,
        max_chars=1000,
    )

    result = context.compile(
        [
            ContextItem("A", "one", "1", 10),
            ContextItem("B", "two", "2", 9),
            ContextItem("C", "three", "3", 8),
        ]
    )

    assert result["count"] == 2


def test_mission_cycle_prepares_non_mutating_work(tmp_path):
    root, plan_path, state_path = build_fixture(tmp_path)

    runtime = AutonomousMissionRuntime(
        root=root,
        master_plan_path=plan_path,
        state_path=state_path,
    )

    engine = MissionCycleEngine(runtime)
    cycle = engine.prepare()

    assert cycle.status == "READY"
    assert cycle.gate == "CORE-004"
    assert cycle.subtask == "CORE-004-T02"
    assert cycle.mutation_allowed is False
    assert cycle.approval_required is False

    categories = {
        item.category
        for item in cycle.evidence_targets
    }

    assert {
        "STATE",
        "GATE",
        "IMPLEMENTATION",
        "DEPENDENCY",
        "ARCHITECTURE",
        "TEST",
        "GOVERNANCE",
        "IMPACT",
    } <= categories


def test_evidence_runtime_append_and_read(tmp_path):
    ledger = tmp_path / "evidence.jsonl"

    runtime = EvidenceRuntime(ledger)

    item = runtime.create(
        evidence_id="E-001",
        kind="TEST",
        source="pytest",
        claim="runtime test passed",
    )

    runtime.append(item)

    records = runtime.read_all()

    assert len(records) == 1
    assert records[0]["evidence_id"] == "E-001"
    assert records[0]["claim"] == "runtime test passed"
    assert records[0]["fingerprint"]
