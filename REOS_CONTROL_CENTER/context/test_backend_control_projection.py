from __future__ import annotations

try:
    from REOS_CONTROL_CENTER import reos_control_center as controller
except ModuleNotFoundError:
    import reos_control_center as controller

from .backend_workstream_transition import (
    BACKEND_ACCEPTANCE_CRITERIA,
    B1_ACCEPTANCE_CRITERIA,
)


PHASE_TWO = (
    "Data, Search, Services, Analytics, Security, DevOps & AI Infrastructure"
)


def projection_state(
    *,
    gate_id: str,
    subtask_id: str,
    gate_criteria: list[str],
    subtask_criteria: list[str] | None = None,
) -> dict:
    subtask = {
        "id": subtask_id,
        "title": "Test current backend task",
        "status": "CURRENT",
    }

    if subtask_criteria is not None:
        subtask["acceptance_criteria"] = list(subtask_criteria)

    return {
        "execution": {
            "current_gate": gate_id,
            "current_subtask": subtask_id,
            "current_task": "",
            "status": "CONTROL_CENTER_DRIVEN",
            "current_acceptance_criteria": [],
        },
        "execution_plan": {
            "authoritative_sequence": [
                {
                    "gate": gate_id,
                    "name": "Test gate",
                    "status": "CURRENT",
                },
            ],
        },
        "gate_plans": {
            gate_id: {
                "id": gate_id,
                "status": "CURRENT",
                "current_subtask": subtask_id,
                "acceptance_criteria": list(gate_criteria),
                "subtasks": [subtask],
            },
        },
        "phases": {
            "phase_2": PHASE_TWO,
            "current": PHASE_TWO,
        },
    }


def approval_resume_state() -> dict:
    return {
        "execution": {
            "current_gate": "AI-001",
            "current_subtask": "AI-001-T10",
            "current_task": "AI-001 final approval",
            "status": "READY_FOR_APPROVAL",
            "current_acceptance_criteria": [],
        },
        "architecture": {
            "pending": [
                {"id": "AI-001", "status": "PENDING"},
            ],
            "approved": [],
        },
        "execution_plan": {
            "authoritative_sequence": [
                {
                    "id": "PLAN-015",
                    "gate": "AI-001",
                    "name": "AI Platform & Agents",
                    "status": "CURRENT",
                },
                {
                    "id": "PLAN-016",
                    "gate": "APP-001",
                    "name": "Buyer / Broker / Builder Applications",
                    "status": "FUTURE",
                },
            ],
        },
        "dependencies": {
            "nodes": [
                {"id": "AI-001", "status": "CURRENT"},
                {"id": "APP-001", "status": "FUTURE"},
            ],
            "edges": [
                ["AI-001", "APP-001"],
            ],
        },
        "gate_plans": {
            "AI-001": {
                "id": "AI-001",
                "status": "VALIDATED",
                "current_subtask": "AI-001-T10",
                "subtasks": [
                    {
                        "id": "AI-001-T10",
                        "title": "Final approval and freeze",
                        "status": "READY_FOR_APPROVAL",
                    },
                ],
            },
            "APP-001": {
                "id": "APP-001",
                "status": "FUTURE",
                "current_subtask": "APP-001-T01",
                "subtasks": [
                    {
                        "id": "APP-001-T01",
                        "title": "Resume buyer application implementation",
                        "status": "PENDING",
                    },
                ],
                "acceptance_criteria": [
                    "Application gate-level criterion",
                ],
            },
        },
        "events": [],
    }


def test_b1_acceptance_criteria_survive_controller_projection():
    state = projection_state(
        gate_id="BACKEND-001",
        subtask_id="BACKEND-001-B1",
        gate_criteria=BACKEND_ACCEPTANCE_CRITERIA,
        subtask_criteria=B1_ACCEPTANCE_CRITERIA,
    )

    controller.synchronize_execution_projection(state)

    gate = state["gate_plans"]["BACKEND-001"]

    assert (
        state["execution"]["current_acceptance_criteria"]
        == B1_ACCEPTANCE_CRITERIA
    )
    assert gate["acceptance_criteria"] == BACKEND_ACCEPTANCE_CRITERIA
    assert (
        state["execution"]["current_acceptance_criteria"]
        != gate["acceptance_criteria"]
    )


def test_execution_projection_falls_back_to_gate_criteria():
    gate_criteria = [
        "Gate-level criterion one",
        "Gate-level criterion two",
    ]

    state = projection_state(
        gate_id="APP-001",
        subtask_id="APP-001-T01",
        gate_criteria=gate_criteria,
    )

    controller.synchronize_execution_projection(state)

    assert (
        state["execution"]["current_acceptance_criteria"]
        == gate_criteria
    )


def test_approve_gate_resumes_existing_next_plan_and_syncs_dependencies(
    monkeypatch,
):
    state = approval_resume_state()

    monkeypatch.setattr(
        controller,
        "build_handoff_packet",
        lambda _state: None,
    )
    monkeypatch.setattr(
        controller,
        "save_state",
        lambda _state: None,
    )

    controller.cmd_approve_gate(state)

    sequence = {
        item["gate"]: item["status"]
        for item in state["execution_plan"]["authoritative_sequence"]
    }

    assert sequence == {
        "AI-001": "COMPLETE",
        "APP-001": "CURRENT",
    }

    app_gate = state["gate_plans"]["APP-001"]

    assert app_gate["status"] == "CURRENT"
    assert app_gate["current_subtask"] == "APP-001-T01"
    assert app_gate["subtasks"][0]["status"] == "CURRENT"

    assert state["execution"]["current_gate"] == "APP-001"
    assert state["execution"]["current_subtask"] == "APP-001-T01"
    assert (
        state["execution"]["current_task"]
        == "APP-001-T01: Resume buyer application implementation."
    )
    assert state["execution"]["status"] == "CONTROL_CENTER_DRIVEN"

    dependency_statuses = {
        node["id"]: node["status"]
        for node in state["dependencies"]["nodes"]
    }

    assert dependency_statuses == sequence


def test_approve_gate_does_not_persist_mismatched_dependency_graph(
    monkeypatch,
):
    state = approval_resume_state()
    state["dependencies"]["nodes"].pop()

    save_calls: list[bool] = []

    monkeypatch.setattr(
        controller,
        "build_handoff_packet",
        lambda _state: None,
    )
    monkeypatch.setattr(
        controller,
        "save_state",
        lambda _state: save_calls.append(True),
    )

    import pytest

    with pytest.raises(
        SystemExit,
        match="inventory differs",
    ):
        controller.cmd_approve_gate(state)

    assert save_calls == []
