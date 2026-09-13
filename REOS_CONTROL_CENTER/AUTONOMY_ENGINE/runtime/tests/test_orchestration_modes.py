from __future__ import annotations

import json
import subprocess
from pathlib import Path

from autonomous_mission_runtime import (
    AutonomousMissionRuntime,
)
from builder_runtime import BuilderRuntime
from homio_runtime import HOMIORuntime
from runtime_orchestrator import RuntimeOrchestrator


def build_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "REOS_CONTROL_CENTER"

    (root / "data").mkdir(parents=True)

    plan = {
        "authority": {
            "canonical_project_state": "REOS_CONTROL_CENTER/data/state.json"
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

    state["integrity"]["sha256"] = (
        AutonomousMissionRuntime._calculate_hash(
            state
        )
    )

    (root / "HOMIO_AUTONOMOUS_MASTER_PLAN.json").write_text(
        json.dumps(plan),
        encoding="utf-8",
    )

    (root / "data" / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "init"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "Runtime Test"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "add", "."],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "runtime fixture"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return root


def test_orchestrator_prepares_ready_observation(tmp_path):
    root = build_fixture(tmp_path)

    orchestrator = RuntimeOrchestrator(root)

    result = orchestrator.prepare(
        mode="HOMIO_BUILDER"
    )

    assert result.status == "READY"
    assert result.mission["current_gate"] == "CORE-004"
    assert result.mission["current_subtask"] == "CORE-004-T02"

    assert result.repository["head"]
    assert result.repository["branch"]

    assert isinstance(result.tests, list)
    assert result.context["count"] >= 3

    assert result.risk["mutation_allowed"] is False


def test_orchestrator_records_evidence(tmp_path):
    root = build_fixture(tmp_path)

    orchestrator = RuntimeOrchestrator(root)

    orchestrator.prepare()

    evidence = (
        root
        / "runtime"
        / "evidence.jsonl"
    )

    assert evidence.exists()

    records = [
        line
        for line in evidence.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert records


def test_builder_runtime_returns_current_work(tmp_path):
    root = build_fixture(tmp_path)

    runtime = BuilderRuntime(root)

    payload = runtime.prepare_next_work()

    assert payload["status"] == "READY"
    assert payload["mission"]["current_gate"] == "CORE-004"
    assert payload["mission"]["current_subtask"] == "CORE-004-T02"


def test_homio_runtime_is_observe_first(tmp_path):
    root = build_fixture(tmp_path)

    runtime = HOMIORuntime(root)

    payload = runtime.observe()

    assert payload["status"] == "READY"

    contract = runtime.health_contract()

    assert contract["observe"] is True
    assert contract["verify"] is True
    assert contract["govern"] is True
    assert contract["execute"] is False
    assert contract["direct_state_mutation"] is False
    assert contract["direct_repository_mutation"] is False


def test_duplicate_current_gate_blocks_orchestrator(tmp_path):
    root = build_fixture(tmp_path)

    state_path = (
        root
        / "data"
        / "state.json"
    )

    state = json.loads(
        state_path.read_text(
            encoding="utf-8"
        )
    )

    state["execution_plan"][
        "authoritative_sequence"
    ].append(
        {
            "gate": "CORE-006",
            "status": "CURRENT",
        }
    )

    state["integrity"]["sha256"] = (
        AutonomousMissionRuntime._calculate_hash(
            state
        )
    )

    state_path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    orchestrator = RuntimeOrchestrator(root)

    result = orchestrator.prepare()

    assert result.status == "BLOCKED"
    assert "CURRENT_GATE_NOT_UNIQUE" in result.blockers
