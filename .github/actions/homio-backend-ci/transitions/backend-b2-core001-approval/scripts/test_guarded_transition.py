from __future__ import annotations

import copy
import unittest

import guarded_transition as guard
from REOS_CONTROL_CENTER.context.backend_workstream_transition import (
    BACKEND_STAGES,
    BACKEND_ACCEPTANCE_CRITERIA,
    B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA,
)
from REOS_CONTROL_CENTER.context.github_actions_identity import (
    EXPECTED_OIDC_SUBJECT,
    OIDC_ISSUER,
    OWNER,
    OWNER_ID,
    REPOSITORY_ID,
)


def make_state() -> dict:
    subtasks = []

    for stage_id, title, priority in BACKEND_STAGES:
        if stage_id in {
            "B0",
            "B1",
            "B2-FOUNDATION",
            "B3",
            "B4",
        }:
            status = "DONE"
        elif stage_id == "B2-PRODUCTION-BINDING":
            status = "CURRENT"
        else:
            status = "PENDING"

        subtasks.append({
            "id": f"BACKEND-001-{stage_id}",
            "title": title,
            "priority": priority,
            "status": status,
        })

    criteria = [
        {
            "id": f"BACKEND-001-AC{index:02d}",
            "criterion": item,
            "status": "PENDING",
            "evidence": None,
            "verified_at": None,
        }
        for index, item in enumerate(
            BACKEND_ACCEPTANCE_CRITERIA,
            start=1,
        )
    ]

    state = {
        "execution": {
            "current_gate": "BACKEND-001",
            "current_subtask": "BACKEND-001-B2-PRODUCTION-BINDING",
            "current_task": (
                "BACKEND-001-B2-PRODUCTION-BINDING: "
                "API security and trusted context — production binding."
            ),
            "status": "CONTROL_CENTER_DRIVEN",
            "current_acceptance_criteria": list(
                B2_PRODUCTION_BINDING_ACCEPTANCE_CRITERIA
            ),
        },
        "gate_plans": {
            "BACKEND-001": {
                "id": "BACKEND-001",
                "status": "CURRENT",
                "current_subtask": (
                    "BACKEND-001-B2-PRODUCTION-BINDING"
                ),
                "subtasks": subtasks,
                "acceptance_criteria": list(
                    BACKEND_ACCEPTANCE_CRITERIA
                ),
                "criteria_state": criteria,
            }
        },
        "change_requests": [
            {
                "id": "CR-BACKEND-001",
                "type": "WORKSTREAM_ACTIVATION",
                "status": "APPROVED",
            },
            {
                "id": "CR-BACKEND-001-B2-DEPENDENCY",
                "type": "STAGE_DEPENDENCY_CORRECTION",
                "status": "APPROVED",
            },
        ],
        "events": [],
        "integrity": {"sha256": None},
    }
    state["integrity"]["sha256"] = guard.controller.calculate_hash(state)
    return state


def valid_reports():
    t15 = {
        "decision": "PROPOSE",
        "execution_authorized": False,
        "request_fingerprint": "a" * 64,
        "proposal": {
            "risk": "MEDIUM",
            "requires_authorization": True,
        },
    }
    t17 = {
        "decision": "ANALYZE",
        "ready_for_handoff": True,
        "unknown_paths": [],
        "protected_paths": [],
        "fingerprint": "b" * 64,
        "changed_paths": sorted(guard.EXPECTED_SOURCE_PATHS),
    }
    t18 = {
        "decision": "AUTHORIZE",
        "execution_authorized": True,
        "state_mutated": False,
        "requires_external_executor": True,
        "authorization_fingerprint": "c" * 64,
        "request_fingerprint": "d" * 64,
    }
    return t15, t17, t18


def valid_approval_record():
    return {
        "actor": OWNER,
        "actor_id": OWNER_ID,
        "owner_id": OWNER_ID,
        "repository_id": REPOSITORY_ID,
        "source_commit": "f" * 40,
        "state_blob_sha": "1" * 40,
        "oidc_issuer": OIDC_ISSUER,
        "oidc_subject": EXPECTED_OIDC_SUBJECT,
        "actions_run_id": "123456789",
    }


def build(state=None, *, t15=None, t17=None, t18=None, approval=None):
    t15_valid, t17_valid, t18_valid = valid_reports()
    state = make_state() if state is None else state

    return guard.build_approved_state(
        state,
        timestamp="2026-11-26T00:00:00+00:00",
        baseline_sha=guard.BASELINE_HEAD,
        source_sha="f" * 40,
        state_blob_sha="1" * 40,
        master_blob_sha=guard.BASELINE_MASTER_BLOB_SHA,
        request_blob_sha=guard.BASELINE_REQUEST_BLOB_SHA,
        t15_report=t15_valid if t15 is None else t15,
        t17_report=t17_valid if t17 is None else t17,
        authorization=t18_valid if t18 is None else t18,
        approval_record=(
            valid_approval_record() if approval is None else approval
        ),
    )


class TestB2Core001ApprovalTransition(unittest.TestCase):
    def test_approves_only_the_bounded_change_request(self):
        source = make_state()
        candidate = build(source)

        approved = [
            item
            for item in candidate["change_requests"]
            if item.get("id") == guard.CHANGE_REQUEST_ID
        ]

        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0]["status"], "APPROVED")
        self.assertFalse(
            approved[0]["scope"]["production_customer_routes_enabled"]
        )
        self.assertFalse(approved[0]["scope"]["b2_task_completed"])

    def test_does_not_mutate_the_input_state(self):
        source = make_state()
        before = copy.deepcopy(source)

        build(source)

        self.assertEqual(source, before)

    def test_preserves_current_b2_task_and_all_stage_statuses(self):
        candidate = build()

        self.assertEqual(
            candidate["execution"]["current_subtask"],
            "BACKEND-001-B2-PRODUCTION-BINDING",
        )
        self.assertEqual(
            candidate["gate_plans"]["BACKEND-001"]["current_subtask"],
            "BACKEND-001-B2-PRODUCTION-BINDING",
        )

        statuses = {
            item["id"]: item["status"]
            for item in candidate["gate_plans"]["BACKEND-001"]["subtasks"]
        }
        self.assertEqual(
            statuses["BACKEND-001-B4"],
            "DONE",
        )
        self.assertEqual(
            statuses["BACKEND-001-B2-PRODUCTION-BINDING"],
            "CURRENT",
        )
        self.assertEqual(statuses["BACKEND-001-B5"], "PENDING")

    def test_does_not_verify_any_backend_acceptance_criterion(self):
        candidate = build()
        criteria = candidate["gate_plans"]["BACKEND-001"]["criteria_state"]

        self.assertEqual(len(criteria), 10)
        self.assertTrue(
            all(item["status"] == "PENDING" for item in criteria)
        )

    def test_rejects_wrong_current_subtask(self):
        state = make_state()
        state["execution"]["current_subtask"] = "BACKEND-001-B5"
        state["integrity"]["sha256"] = guard.controller.calculate_hash(state)

        with self.assertRaises(guard.GuardedTransitionError):
            build(state)

    def test_rejects_b4_not_done(self):
        state = make_state()
        b4 = next(
            item
            for item in state["gate_plans"]["BACKEND-001"]["subtasks"]
            if item["id"] == "BACKEND-001-B4"
        )
        b4["status"] = "PENDING"
        state["integrity"]["sha256"] = guard.controller.calculate_hash(state)

        with self.assertRaises(guard.GuardedTransitionError):
            build(state)

    def test_rejects_already_verified_gate_criterion(self):
        state = make_state()
        state["gate_plans"]["BACKEND-001"]["criteria_state"][0]["status"] = (
            "VERIFIED"
        )
        state["integrity"]["sha256"] = guard.controller.calculate_hash(state)

        with self.assertRaises(guard.GuardedTransitionError):
            build(state)

    def test_rejects_duplicate_change_request(self):
        state = make_state()
        state["change_requests"].append({
            "id": guard.CHANGE_REQUEST_ID,
            "status": "APPROVED",
        })
        state["integrity"]["sha256"] = guard.controller.calculate_hash(state)

        with self.assertRaises(guard.GuardedTransitionError):
            build(state)

    def test_rejects_non_owner_approval(self):
        approval = valid_approval_record()
        approval["actor"] = "another-user"

        with self.assertRaises(ValueError):
            build(approval=approval)

    def test_rejects_t15_without_propose(self):
        t15, _, _ = valid_reports()
        t15["decision"] = "DENY"

        with self.assertRaises(guard.GuardedTransitionError):
            build(t15=t15)

    def test_rejects_t17_unknown_paths(self):
        _, t17, _ = valid_reports()
        t17["unknown_paths"] = ["unclassified/file.py"]

        with self.assertRaises(guard.GuardedTransitionError):
            build(t17=t17)

    def test_rejects_t17_protected_paths(self):
        _, t17, _ = valid_reports()
        t17["protected_paths"] = ["REOS_CONTROL_CENTER/data/state.json"]

        with self.assertRaises(guard.GuardedTransitionError):
            build(t17=t17)

    def test_rejects_t18_without_external_authorization(self):
        _, _, t18 = valid_reports()
        t18["execution_authorized"] = False

        with self.assertRaises(guard.GuardedTransitionError):
            build(t18=t18)

    def test_rejects_t18_that_mutates_state(self):
        _, _, t18 = valid_reports()
        t18["state_mutated"] = True

        with self.assertRaises(guard.GuardedTransitionError):
            build(t18=t18)


if __name__ == "__main__":
    unittest.main(verbosity=2)
