from __future__ import annotations

import copy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import guarded_transition as guard
import verify_core001_source_baseline as source_verifier

from test_core001_source_baseline import TestCore001SourceBaseline  # noqa: F401

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


def run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return completed.stdout.strip()


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
        self.assertFalse(
            approved[0]["scope"]["b2_task_completed"]
        )

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

        self.assertEqual(statuses["BACKEND-001-B4"], "DONE")
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

    def test_source_inventory_uses_exact_approval_commit_not_historical_branch_diff(self):
        historical_paths = {
            "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py",
            (
                "REOS_CONTROL_CENTER/backend/tests/integration/"
                "postgres-financial-ledger.integration.test.ts"
            ),
        }

        with tempfile.TemporaryDirectory(
            prefix="homio-b2-approval-"
        ) as temporary_directory:
            repository = Path(temporary_directory)

            run_git(repository, "init")
            run_git(repository, "config", "user.name", "HOMIO Guard Tests")
            run_git(
                repository,
                "config",
                "user.email",
                "homio-guard-tests@example.invalid",
            )

            baseline_readme = repository / "README.md"
            baseline_readme.write_text(
                "Synthetic approval-guard baseline.\n",
                encoding="utf-8",
            )

            for relative_path in sorted(
                source_verifier.CORE001_SOURCE_BLOB_SHAS
            ):
                target = repository / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    "Reviewed CORE-001 source fixture.\n",
                    encoding="utf-8",
                )

            run_git(repository, "add", "--all")
            run_git(repository, "commit", "-m", "baseline")
            baseline_sha = run_git(repository, "rev-parse", "HEAD")

            for relative_path in sorted(historical_paths):
                target = repository / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    "Previously committed unrelated change.\n",
                    encoding="utf-8",
                )

                run_git(repository, "add", "--all")
                run_git(
                    repository,
                    "commit",
                    "-m",
                    f"previous unrelated save: {target.name}",
                )

            approval_content = getattr(
                guard,
                "APPROVAL_RECORD_CONTENT",
                "Exact owner approval source bundle.\n",
            )

            for relative_path in sorted(guard.EXPECTED_SOURCE_PATHS):
                target = repository / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    approval_content,
                    encoding="utf-8",
                    newline="\n",
                )

            run_git(repository, "add", "--all")
            run_git(
                repository,
                "commit",
                "-m",
                "exact owner approval source bundle",
            )
            owner_source_sha = run_git(repository, "rev-parse", "HEAD")

            reviewed_blob_shas = {
                guard.STATE_PATH: guard.BASELINE_STATE_BLOB_SHA,
                guard.MASTER_PATH: guard.BASELINE_MASTER_BLOB_SHA,
                guard.REQUEST_PATH: guard.BASELINE_REQUEST_BLOB_SHA,
                **source_verifier.CORE001_SOURCE_BLOB_SHAS,
            }

            def reviewed_blob_sha(path: str, ref: str = "HEAD") -> str:
                if path not in reviewed_blob_shas:
                    raise AssertionError(
                        f"Unexpected source blob lookup: {path}"
                    )
                return reviewed_blob_shas[path]

            with (
                patch.object(guard, "ROOT", repository),
                patch.object(guard, "BASELINE_HEAD", baseline_sha),
                patch.object(
                    guard,
                    "file_blob_sha",
                    side_effect=reviewed_blob_sha,
                ),
                patch.object(guard, "assert_exact_branch"),
                patch.object(guard, "verify_request_document"),
            ):
                changed_paths = guard.verify_source_baseline(
                    owner_source_sha
                )

            self.assertEqual(
                changed_paths,
                sorted(guard.EXPECTED_SOURCE_PATHS),
            )

            cumulative_paths = set(
                run_git(
                    repository,
                    "diff",
                    "--name-only",
                    baseline_sha,
                    owner_source_sha,
                ).splitlines()
            )

            self.assertEqual(
                cumulative_paths,
                guard.EXPECTED_SOURCE_PATHS | historical_paths,
            )

    def test_owner_record_inventory_is_available_after_guard_upgrade(self):
        if not hasattr(guard, "APPROVAL_RECORD_PATH"):
            self.skipTest("Dedicated owner-record guard is not installed yet.")

        self.assertEqual(
            guard.EXPECTED_SOURCE_PATHS,
            {guard.APPROVAL_RECORD_PATH},
        )

    def test_single_file_owner_record_is_accepted_by_t17_after_guard_upgrade(self):
        if not hasattr(guard, "APPROVAL_RECORD_PATH"):
            self.skipTest("Dedicated owner-record guard is not installed yet.")

        _, t17, _ = valid_reports()
        t17["changed_paths"] = [guard.APPROVAL_RECORD_PATH]

        candidate = build(t17=t17)

        approved_request = next(
            item
            for item in candidate["change_requests"]
            if item.get("id") == guard.CHANGE_REQUEST_ID
        )
        self.assertEqual(
            approved_request["impact_review"]["changed_paths"],
            [guard.APPROVAL_RECORD_PATH],
        )

    def test_rejects_modified_owner_approval_record_after_guard_upgrade(self):
        if not hasattr(guard, "APPROVAL_RECORD_CONTENT"):
            self.skipTest("Dedicated owner-record guard is not installed yet.")

        tampered_content = guard.APPROVAL_RECORD_CONTENT.replace(
            "- Decision: `APPROVE`",
            "- Decision: `PENDING`",
            1,
        )

        with patch.object(
            guard,
            "run",
            return_value=tampered_content,
        ):
            with self.assertRaisesRegex(
                guard.GuardedTransitionError,
                "does not exactly match",
            ):
                guard.verify_owner_approval_record("f" * 40)

    def test_rejects_extra_file_in_owner_approval_commit_after_guard_upgrade(self):
        if not hasattr(guard, "APPROVAL_RECORD_PATH"):
            self.skipTest("Dedicated owner-record guard is not installed yet.")

        with tempfile.TemporaryDirectory(
            prefix="homio-b2-extra-approval-path-"
        ) as temporary_directory:
            repository = Path(temporary_directory)

            run_git(repository, "init")
            run_git(repository, "config", "user.name", "HOMIO Guard Tests")
            run_git(
                repository,
                "config",
                "user.email",
                "homio-guard-tests@example.invalid",
            )

            baseline_readme = repository / "README.md"
            baseline_readme.write_text(
                "Synthetic approval-guard baseline.\n",
                encoding="utf-8",
            )

            run_git(repository, "add", "--all")
            run_git(repository, "commit", "-m", "baseline")
            baseline_sha = run_git(repository, "rev-parse", "HEAD")

            approval_path = repository / guard.APPROVAL_RECORD_PATH
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(
                guard.APPROVAL_RECORD_CONTENT,
                encoding="utf-8",
                newline="\n",
            )

            extra_path = repository / "UNEXPECTED-APPROVAL-CHANGE.txt"
            extra_path.write_text(
                "This extra change must block approval.\n",
                encoding="utf-8",
            )

            run_git(repository, "add", "--all")
            run_git(
                repository,
                "commit",
                "-m",
                "owner approval with an unexpected extra file",
            )
            owner_source_sha = run_git(repository, "rev-parse", "HEAD")

            reviewed_blob_shas = {
                guard.STATE_PATH: guard.BASELINE_STATE_BLOB_SHA,
                guard.MASTER_PATH: guard.BASELINE_MASTER_BLOB_SHA,
                guard.REQUEST_PATH: guard.BASELINE_REQUEST_BLOB_SHA,
            }

            def reviewed_blob_sha(path: str, ref: str = "HEAD") -> str:
                if path not in reviewed_blob_shas:
                    raise AssertionError(
                        f"Unexpected source blob lookup: {path}"
                    )
                return reviewed_blob_shas[path]

            with (
                patch.object(guard, "ROOT", repository),
                patch.object(guard, "BASELINE_HEAD", baseline_sha),
                patch.object(
                    guard,
                    "file_blob_sha",
                    side_effect=reviewed_blob_sha,
                ),
                patch.object(guard, "assert_exact_branch"),
                patch.object(guard, "verify_request_document"),
                patch.object(guard, "verify_owner_approval_record"),
            ):
                with self.assertRaisesRegex(
                    guard.GuardedTransitionError,
                    "Exact owner approval path inventory mismatch",
                ):
                    guard.verify_source_baseline(owner_source_sha)

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
