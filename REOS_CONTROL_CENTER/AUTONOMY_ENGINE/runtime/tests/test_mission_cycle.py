from __future__ import annotations

import hashlib
import json
from pathlib import Path

from autonomous_mission_runtime import AutonomousMissionRuntime
from mission_cycle import MissionCycleEngine


def state_hash(state: dict) -> str:
    clone = json.loads(json.dumps(state))
    clone.setdefault("integrity", {})["sha256"] = None

    raw = json.dumps(
        clone,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


def write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "REOS_CONTROL_CENTER"
    (root / "data").mkdir(parents=True)

    plan = {
        "authority": {
            "canonical_project_state": (
                "REOS_CONTROL_CENTER/data/state.json"
            )
        },
        "phases": [
            {
                "id": "P2",
                "name": "HOMIO Autonomous Build",
            }
        ],
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
                {
                    "gate": "CORE-004",
                    "status": "CURRENT",
                },
                {
                    "gate": "CORE-005",
                    "status": "PENDING",
                },
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
        "integrity": {
            "sha256": None,
        },
    }

    state["integrity"]["sha256"] = state_hash(state)

    plan_path = (
        root / "HOMIO_AUTONOMOUS_MASTER_PLAN.json"
    )
    state_path = root / "data" / "state.json"

    plan_path.write_text(
        json.dumps(plan),
        encoding="utf-8",
    )

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    return plan_path, state_path


def build_engine(tmp_path: Path) -> MissionCycleEngine:
    plan_path, state_path = write_fixture(tmp_path)

    runtime = AutonomousMissionRuntime(
        root=plan_path.parent,
        master_plan_path=plan_path,
        state_path=state_path,
    )

    return MissionCycleEngine(runtime)


def test_cycle_prepares_targeted_homio_work_cycle(
    tmp_path: Path,
) -> None:
    engine = build_engine(tmp_path)

    cycle = engine.prepare()

    assert cycle.status == "READY"
    assert cycle.mode == "HOMIO_BUILDER"
    assert cycle.gate == "CORE-004"
    assert cycle.subtask == "CORE-004-T02"
    assert cycle.mutation_allowed is False

    target_ids = [
        target.target_id
        for target in cycle.evidence_targets
    ]

    assert target_ids == [
        "canonical-state",
        "current-gate",
        "current-subtask",
        "dependency-impact",
        "architecture-contract",
        "test-surface",
        "risk-boundary",
        "change-impact",
    ]


def test_cycle_creates_existing_agent_runtime(
    tmp_path: Path,
) -> None:
    engine = build_engine(tmp_path)

    cycle = engine.prepare()

    agent = engine.create_agent_runtime(
        cycle,
        agent_id="homio-builder-agent",
    )

    assert agent.status == "PLANNED"
    assert agent.context.agent_id == "homio-builder-agent"
    assert agent.context.task_id == "CORE-004-T02"
    assert agent.context.run_id == cycle.cycle_id


def test_cycle_build_is_machine_readable(
    tmp_path: Path,
) -> None:
    engine = build_engine(tmp_path)

    payload = engine.build_cycle(
        agent_id="homio-builder-agent",
    )

    assert payload["status"] == "READY"
    assert payload["agent_runtime"]["status"] == "PLANNED"
    assert payload["agent_runtime"]["task_id"] == "CORE-004-T02"
    assert payload["agent_context"]["execution_budget"][
        "never_dump_full_file"
    ] is True


def test_cycle_never_mutates_canonical_state(
    tmp_path: Path,
) -> None:
    plan_path, state_path = write_fixture(tmp_path)

    before = state_path.read_text(
        encoding="utf-8"
    )

    runtime = AutonomousMissionRuntime(
        root=plan_path.parent,
        master_plan_path=plan_path,
        state_path=state_path,
    )

    engine = MissionCycleEngine(runtime)

    cycle = engine.prepare()

    assert cycle.status == "READY"

    after = state_path.read_text(
        encoding="utf-8"
    )

    assert after == before
