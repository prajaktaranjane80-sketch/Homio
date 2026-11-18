
from __future__ import annotations

import copy

import pytest

from .backend_workstream_transition import (
    BACKEND_ACCEPTANCE_CRITERIA,
    BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID,
    BACKEND_GATE_ID,
    BACKEND_STAGES,
    BACKEND_TECHNICAL_SEQUENCE,
    B2_FOUNDATION_ACCEPTANCE_CRITERIA,
    B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA,
    B3_ACCEPTANCE_CRITERIA,
    B4_ACCEPTANCE_CRITERIA,
    BackendWorkstreamTransitionError,
    activate_backend_workstream_state,
    correct_backend_b2_dependency_state,
)


def make_state() -> dict:
    return {
        "architecture": {
            "approved": [
                {"id": "ARCH-037", "status": "APPROVED"},
                {"id": "ARCH-038", "status": "APPROVED"},
            ],
            "pending": [
                {"id": "ARCH-039", "status": "PENDING"},
            ],
            "locked": False,
        },
        "execution": {
            "current_gate": "APP-001",
            "current_subtask": "APP-001-T01",
            "current_task": (
                "APP-001-T01: Implement application shell and design system."
            ),
            "status": "CONTROL_CENTER_DRIVEN",
            "current_acceptance_criteria": [],
        },
        "execution_plan": {
            "status": "ACTIVE",
            "authoritative_sequence": [
                {
                    "id": "PLAN-015",
                    "gate": "AI-001",
                    "name": "AI Platform & Agents",
                    "status": "COMPLETE",
                },
                {
                    "id": "PLAN-016",
                    "gate": "APP-001",
                    "name": "Buyer / Broker / Builder Applications",
                    "status": "CURRENT",
                },
                {
                    "id": "PLAN-017",
                    "gate": "REL-001",
                    "name": "Testing, Security & Release Gates",
                    "status": "FUTURE",
                },
                {
                    "id": "PLAN-018",
                    "gate": "SCALE-001",
                    "name": "Production Scale & International Rollout",
                    "status": "FUTURE",
                },
            ],
        },
        "dependencies": {
            "nodes": [
                {"id": "AI-001", "status": "FUTURE"},
                {"id": "APP-001", "status": "FUTURE"},
                {"id": "REL-001", "status": "FUTURE"},
                {"id": "SCALE-001", "status": "FUTURE"},
            ],
            "edges": [
                ["AI-001", "APP-001"],
                ["APP-001", "REL-001"],
                ["REL-001", "SCALE-001"],
            ],
        },
        "gate_plans": {
            "APP-001": {
                "id": "APP-001",
                "status": "CURRENT",
                "current_subtask": "APP-001-T01",
                "subtasks": [
                    {
                        "id": "APP-001-T01",
                        "title": "Implement application shell and design system",
                        "status": "CURRENT",
                    },
                ],
            },
        },
        "change_requests": [],
        "events": [],
        "tasks": [],
        "phases": {
            "phase_2": (
                "Data, Search, Services, Analytics, Security, DevOps & AI Infrastructure"
            ),
            "current": (
                "Data, Search, Services, Analytics, Security, DevOps & AI Infrastructure"
            ),
        },
    }


def valid_evidence():
    return {
        "actor": "prajaktaranjane80-sketch",
        "actor_id": "verified-by-github-oidc",
        "source_commit": "a" * 40,
        "state_blob_sha": "b" * 40,
        "oidc_issuer": "https://token.actions.githubusercontent.com",
        "oidc_subject": (
            "repo:prajaktaranjane80-sketch/Homio:"
            "ref:refs/heads/reos-development"
        ),
        "actions_run_id": "123456789",
    }


def valid_t15():
    return {
        "decision": "PROPOSE",
        "execution_authorized": False,
        "request_fingerprint": "c" * 64,
        "proposal": {
            "action_type": "PROPOSE_CHANGE",
            "risk": "MEDIUM",
            "requires_authorization": True,
        },
    }


def valid_t17():
    return {
        "schema_version": "1.0",
        "decision": "ANALYZE",
        "fingerprint": "d" * 64,
        "changed_paths": [
            "REOS_CONTROL_CENTER/architecture/backend/plans/"
            "HOMIO_Backend_Structure",
            "REOS_CONTROL_CENTER/context/backend_workstream_transition.py",
        ],
        "unknown_paths": [],
        "protected_paths": [],
        "state_mutated": False,
        "execution_authorized": False,

        # Required by correct_backend_b2_dependency_state().
        # This mirrors ChangeImpactReport.to_dict().
        "ready_for_handoff": True,
    }


def valid_t18():
    return {
        "decision": "AUTHORIZE",
        "authorization_fingerprint": "e" * 64,
        "request_fingerprint": "f" * 64,
        "execution_authorized": True,
        "state_mutated": False,
        "requires_external_executor": True,
    }


def activate(state):
    return activate_backend_workstream_state(
        state,
        timestamp="2026-11-02T12:00:00+00:00",
        baseline_sha="a" * 40,
        master_blob_sha="b" * 40,
        work_plan_blob_sha="c" * 40,
        b0_evidence_path=(
            "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
            "B0-live-repository-audit.md"
        ),
        approval_record=valid_evidence(),
        t15_report=valid_t15(),
        t17_report=valid_t17(),
        authorization=valid_t18(),
    )


def make_backend_b2_state() -> dict:
    titles = {
        0: "Live repository audit and ownership verification",
        1: "Backend application foundation",
        2: "API security and trusted context",
        3: "Python domain-runtime bridge",
        4: "PostgreSQL integration",
        5: "Domain API adapters",
        6: "Event and durable workflow integration",
        7: "Search, AI and provider integration",
        8: "Complete customer and business journeys",
        9: "Production operations",
        10: "Release verification and final freeze approval",
    }

    subtasks = []

    for number in range(11):
        status = (
            "DONE"
            if number in (0, 1)
            else "CURRENT"
            if number == 2
            else "PENDING"
        )

        item = {
            "id": f"BACKEND-001-B{number}",
            "title": titles[number],
            "priority": (
                "HIGH"
                if number in (6, 7)
                else "CRITICAL"
            ),
            "status": status,
        }

        if number == 1:
            item["acceptance_criteria"] = [
                "Build is reproducible.",
                "Invalid runtime configuration fails safely.",
                "Health and readiness semantics are tested.",
                "Graceful shutdown is tested.",
                "No duplicate public API application exists.",
            ]

        subtasks.append(item)

    criteria_state = [
        {
            "id": f"BACKEND-001-AC{index:02d}",
            "criterion": criterion,
            "status": "PENDING",
            "evidence": None,
            "verified_at": None,
        }
        for index, criterion in enumerate(
            BACKEND_ACCEPTANCE_CRITERIA,
            start=1,
        )
    ]

    return {
        "execution": {
            "current_gate": "BACKEND-001",
            "current_subtask": "BACKEND-001-B2",
            "current_task": (
                "BACKEND-001-B2: API security and trusted context."
            ),
            "status": "CONTROL_CENTER_DRIVEN",
            "current_acceptance_criteria": list(
                BACKEND_ACCEPTANCE_CRITERIA
            ),
        },
        "gate_plans": {
            "BACKEND-001": {
                "id": "BACKEND-001",
                "status": "CURRENT",
                "current_subtask": "BACKEND-001-B2",
                "subtasks": subtasks,
                "acceptance_criteria": list(
                    BACKEND_ACCEPTANCE_CRITERIA
                ),
                "criteria_state": criteria_state,
            }
        },
        "change_requests": [
            {
                "id": "CR-BACKEND-001",
                "type": "WORKSTREAM_ACTIVATION",
                "status": "APPROVED",
            }
        ],
        "events": [],
    }


def correct_b2(state, **overrides):
    arguments = {
        "timestamp": "2026-11-16T13:00:00+00:00",
        "baseline_sha": "1" * 40,
        "master_blob_sha": "2" * 40,
        "approval_record": {
            "actor": "prajaktaranjane80-sketch",
            "actor_id": "320960487",
            "source_commit": "3" * 40,
            "state_blob_sha": "4" * 40,
            "oidc_issuer": "https://token.actions.githubusercontent.com",
            "oidc_subject": "verified-owner-subject",
            "owner_id": "320960487",
            "repository_id": "1346051793",
            "actions_run_id": "123456789",
        },
        "t15_report": valid_t15(),
        "t17_report": valid_t17(),
        "authorization": valid_t18(),
    }
    arguments.update(overrides)

    return correct_backend_b2_dependency_state(
        state,
        **arguments,
    )


def test_activation_selects_backend_b1_and_preserves_app_t01():
    original = make_state()
    original_before = copy.deepcopy(original)

    result = activate(original)

    assert original == original_before
    assert result["execution"]["current_gate"] == BACKEND_GATE_ID
    assert result["execution"]["current_subtask"] == "BACKEND-001-B1"
    assert result["execution"]["status"] == "CONTROL_CENTER_DRIVEN"

    backend = result["gate_plans"]["BACKEND-001"]
    statuses = {
        item["id"]: item["status"]
        for item in backend["subtasks"]
    }

    assert statuses["BACKEND-001-B0"] == "DONE"
    assert statuses["BACKEND-001-B1"] == "CURRENT"
    assert statuses["BACKEND-001-B2-FOUNDATION"] == "PENDING"
    assert statuses["BACKEND-001-B3"] == "PENDING"
    assert statuses["BACKEND-001-B4"] == "PENDING"
    assert statuses["BACKEND-001-B2-PRODUCTION-BINDING"] == "PENDING"
    assert statuses["BACKEND-001-B10"] == "PENDING"

    assert backend["technical_sequence"] == BACKEND_TECHNICAL_SEQUENCE

    app = result["gate_plans"]["APP-001"]
    assert app["status"] == "FUTURE"
    assert app["current_subtask"] == "APP-001-T01"
    assert app["subtasks"][0]["status"] == "CURRENT"

    sequence = {
        item["gate"]: item["status"]
        for item in result["execution_plan"]["authoritative_sequence"]
    }

    assert sequence["AI-001"] == "COMPLETE"
    assert sequence["BACKEND-001"] == "CURRENT"
    assert sequence["APP-001"] == "FUTURE"
    assert sequence["REL-001"] == "FUTURE"
    assert sequence["SCALE-001"] == "FUTURE"

    dependencies = result["dependencies"]
    dependency_statuses = {
        item["id"]: item["status"]
        for item in dependencies["nodes"]
    }

    assert dependency_statuses == {
        "AI-001": "COMPLETE",
        "BACKEND-001": "CURRENT",
        "APP-001": "FUTURE",
        "REL-001": "FUTURE",
        "SCALE-001": "FUTURE",
    }

    assert dependencies["edges"] == [
        ["AI-001", "BACKEND-001"],
        ["BACKEND-001", "APP-001"],
        ["APP-001", "REL-001"],
        ["REL-001", "SCALE-001"],
    ]


def test_activation_assigns_stage_specific_acceptance_criteria():
    backend = activate(make_state())["gate_plans"]["BACKEND-001"]
    subtasks = {
        item["id"]: item
        for item in backend["subtasks"]
    }

    assert (
        subtasks["BACKEND-001-B2-FOUNDATION"]["acceptance_criteria"]
        == B2_FOUNDATION_ACCEPTANCE_CRITERIA
    )
    assert (
        subtasks["BACKEND-001-B3"]["acceptance_criteria"]
        == B3_ACCEPTANCE_CRITERIA
    )
    assert (
        subtasks["BACKEND-001-B4"]["acceptance_criteria"]
        == B4_ACCEPTANCE_CRITERIA
    )
    assert (
        subtasks[
            "BACKEND-001-B2-PRODUCTION-BINDING"
        ]["acceptance_criteria"]
        == B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
    )


def test_activation_reconciles_arch039_from_pending_to_approved():
    result = activate(make_state())

    assert not any(
        item["id"] == "ARCH-039"
        for item in result["architecture"]["pending"]
    )
    assert any(
        item["id"] == "ARCH-039"
        and item["status"] == "APPROVED"
        for item in result["architecture"]["approved"]
    )
    assert result["architecture"]["locked"] is True


def test_activation_records_approved_change_request():
    result = activate(make_state())

    request = result["change_requests"][0]

    assert request["id"] == "CR-BACKEND-001"
    assert request["status"] == "APPROVED"
    assert request["scope"]["gate"] == "BACKEND-001"
    assert request["scope"]["sequence"] == BACKEND_TECHNICAL_SEQUENCE
    assert (
        request["preserved_work"]["subtask"]
        == "APP-001-T01"
    )
    assert request["execution_authorization"]["decision"] == "AUTHORIZE"


def test_activation_rejects_wrong_current_task():
    state = make_state()
    state["execution"]["current_subtask"] = "APP-001-T02"

    with pytest.raises(BackendWorkstreamTransitionError):
        activate(state)


def test_activation_rejects_missing_t18_authorization():
    state = make_state()
    evidence = valid_t18()
    evidence["decision"] = "BLOCK"

    with pytest.raises(BackendWorkstreamTransitionError):
        activate_backend_workstream_state(
            state,
            timestamp="2026-11-02T12:00:00+00:00",
            baseline_sha="a" * 40,
            master_blob_sha="b" * 40,
            work_plan_blob_sha="c" * 40,
            b0_evidence_path="evidence.md",
            approval_record=valid_evidence(),
            t15_report=valid_t15(),
            t17_report=valid_t17(),
            authorization=evidence,
        )


def test_activation_rejects_unknown_or_protected_t17_paths():
    state = make_state()
    report = valid_t17()
    report["unknown_paths"] = ["unknown/path.py"]

    with pytest.raises(BackendWorkstreamTransitionError):
        activate_backend_workstream_state(
            state,
            timestamp="2026-11-02T12:00:00+00:00",
            baseline_sha="a" * 40,
            master_blob_sha="b" * 40,
            work_plan_blob_sha="c" * 40,
            b0_evidence_path="evidence.md",
            approval_record=valid_evidence(),
            t15_report=valid_t15(),
            t17_report=report,
            authorization=valid_t18(),
        )


def test_activation_rejects_duplicate_backend_gate():
    state = make_state()
    state["gate_plans"]["BACKEND-001"] = {"id": "BACKEND-001"}

    with pytest.raises(BackendWorkstreamTransitionError):
        activate(state)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda state: state["dependencies"]["nodes"].pop(),
        lambda state: state["dependencies"]["nodes"].append(
            {"id": "APP-001", "status": "CURRENT"}
        ),
        lambda state: state["dependencies"]["edges"].append(
            ["AI-001", "UNKNOWN-GATE"]
        ),
        lambda state: state["dependencies"]["edges"].__setitem__(
            0, ["AI-001", "REL-001"]
        ),
    ],
    ids=[
        "missing-node",
        "duplicate-node",
        "unknown-edge-target",
        "sequence-mismatch",
    ],
)
def test_activation_rejects_invalid_dependency_graph(mutate):
    state = make_state()
    mutate(state)

    with pytest.raises(BackendWorkstreamTransitionError):
        activate(state)


def test_activation_rejects_missing_dependency_graph():
    state = make_state()
    state.pop("dependencies")

    with pytest.raises(BackendWorkstreamTransitionError):
        activate(state)


def test_activation_does_not_mutate_input_when_change_requests_are_absent():
    state = make_state()
    state.pop("change_requests")
    original = copy.deepcopy(state)

    activate(state)

    assert state == original
    assert "change_requests" not in state


def test_b2_dependency_correction_preserves_foundation_and_delays_production():
    original = make_backend_b2_state()
    original_before = copy.deepcopy(original)

    result = correct_b2(original)

    assert original == original_before

    execution = result["execution"]
    gate = result["gate_plans"]["BACKEND-001"]

    assert execution["current_gate"] == "BACKEND-001"
    assert execution["current_subtask"] == "BACKEND-001-B2-FOUNDATION"
    assert execution["status"] == "CONTROL_CENTER_DRIVEN"

    assert gate["current_subtask"] == "BACKEND-001-B2-FOUNDATION"
    assert gate["technical_sequence"] == BACKEND_TECHNICAL_SEQUENCE

    actual_order = [item["id"] for item in gate["subtasks"]]

    assert actual_order == [
        f"BACKEND-001-{stage_id}"
        for stage_id, _, _ in BACKEND_STAGES
    ]

    statuses = {
        item["id"]: item["status"]
        for item in gate["subtasks"]
    }

    assert statuses["BACKEND-001-B0"] == "DONE"
    assert statuses["BACKEND-001-B1"] == "DONE"
    assert statuses["BACKEND-001-B2-FOUNDATION"] == "CURRENT"
    assert statuses["BACKEND-001-B3"] == "PENDING"
    assert statuses["BACKEND-001-B4"] == "PENDING"
    assert statuses["BACKEND-001-B2-PRODUCTION-BINDING"] == "PENDING"

    assert "BACKEND-001-B2" not in statuses

    assert (
        execution["current_acceptance_criteria"]
        == B2_FOUNDATION_ACCEPTANCE_CRITERIA
    )

    assert all(
        item["status"] == "PENDING"
        and item["evidence"] is None
        and item["verified_at"] is None
        for item in gate["criteria_state"]
    )

    request = next(
        item
        for item in result["change_requests"]
        if item["id"] == BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID
    )

    assert request["status"] == "APPROVED"
    assert (
        request["scope"]["production_binding_position"]
        == "AFTER_B3_AND_B4"
    )
    assert request["execution_authorization"]["decision"] == "AUTHORIZE"
    assert request["owner_approval"]["bearer_token_persisted"] is False


def test_b2_dependency_correction_records_stage_specific_contracts():
    result = correct_b2(make_backend_b2_state())
    subtasks = {
        item["id"]: item
        for item in result["gate_plans"]["BACKEND-001"]["subtasks"]
    }

    assert (
        subtasks["BACKEND-001-B2-FOUNDATION"]["acceptance_criteria"]
        == B2_FOUNDATION_ACCEPTANCE_CRITERIA
    )
    assert (
        subtasks["BACKEND-001-B3"]["acceptance_criteria"]
        == B3_ACCEPTANCE_CRITERIA
    )
    assert (
        subtasks["BACKEND-001-B4"]["acceptance_criteria"]
        == B4_ACCEPTANCE_CRITERIA
    )
    assert (
        subtasks[
            "BACKEND-001-B2-PRODUCTION-BINDING"
        ]["acceptance_criteria"]
        == B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
    )


def test_b2_dependency_correction_rejects_a_stale_current_subtask():
    state = make_backend_b2_state()
    state["execution"]["current_subtask"] = "BACKEND-001-B3"

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state)


def test_b2_dependency_correction_rejects_unknown_t17_paths():
    state = make_backend_b2_state()
    report = valid_t17()
    report["unknown_paths"] = ["unclassified/file"]

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state, t17_report=report)


def test_b2_dependency_correction_rejects_protected_t17_paths():
    state = make_backend_b2_state()
    report = valid_t17()
    report["protected_paths"] = ["REOS_CONTROL_CENTER/data/state.json"]

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state, t17_report=report)


def test_b2_dependency_correction_rejects_blocked_t18():
    state = make_backend_b2_state()
    authorization = valid_t18()
    authorization["decision"] = "BLOCK"

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state, authorization=authorization)


def test_b2_dependency_correction_rejects_missing_oidc_owner_identity():
    state = make_backend_b2_state()
    approval = {
        **valid_evidence(),
        "owner_id": "wrong-owner",
        "repository_id": "1346051793",
    }

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state, approval_record=approval)


def test_b2_dependency_correction_rejects_duplicate_change_request():
    state = make_backend_b2_state()
    state["change_requests"].append(
        {
            "id": BACKEND_B2_DEPENDENCY_CHANGE_REQUEST_ID,
            "status": "APPROVED",
        }
    )

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state)


def test_b2_dependency_correction_rejects_changed_gate_acceptance_baseline():
    state = make_backend_b2_state()
    criteria = state["gate_plans"]["BACKEND-001"]["criteria_state"]
    criteria[0]["status"] = "VERIFIED"

    with pytest.raises(BackendWorkstreamTransitionError):
        correct_b2(state)


def test_b2_dependency_correction_never_completes_full_b2_or_backend_gate():
    result = correct_b2(make_backend_b2_state())
    gate = result["gate_plans"]["BACKEND-001"]

    assert gate["status"] == "CURRENT"
    assert all(
        item["status"] == "PENDING"
        for item in gate["criteria_state"]
    )

    assert next(
        item
        for item in gate["subtasks"]
        if item["id"] == "BACKEND-001-B2-PRODUCTION-BINDING"
    )["status"] == "PENDING"
