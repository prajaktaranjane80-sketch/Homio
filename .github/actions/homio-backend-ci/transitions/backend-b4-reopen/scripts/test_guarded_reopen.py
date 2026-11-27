
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import guarded_reopen

from guarded_reopen import (
    APPROVAL_PREFIX,
    B4_ID,
    B2_ID,
    OWNER,
    OWNER_ID,
    REPOSITORY_ID,
    OIDC_ISSUER,
    EXPECTED_OIDC_SUBJECT,
    REPOSITORY,
    BRANCH_REF,
    apply_reopen_transition,
    validate_owner_push,
    validate_reopen_baseline,
    validate_reopen_baseline_after,
    verify_commit_scope,
    ALLOWED_OWNER_COMMIT_PATHS,
    STATE_PATH,
)


SOURCE_SHA = "ab51c9706cdbec2441658e82f3c534170f1e5969"
PREVIOUS_B4_SHA = "17784ada3e96edc5182cebb9cc548b2266b40296"
PREVIOUS_RUN_ID = "45808014761"
TIMESTAMP = "2026-11-27T13:00:00+05:30"
OLD_SHA = PREVIOUS_B4_SHA
RUN_ID = PREVIOUS_RUN_ID


def sample_state() -> dict:
    b4_criteria = [
        "Only the approved ARCH-037 schema and canonical owners are used.",
        "Migrations have deterministic ordering and integrity checks.",
        "Tenant access is enforced by the target persistence boundary.",
        "Repositories and transaction boundaries have explicit write ownership.",
        "Durable session and revocation storage is supported.",
        "Shared rate-limit state and minimized audit persistence are supported.",
        "Migration, concurrency, backup and recovery tests pass.",
        "No second schema or persistence authority is introduced.",
    ]
    b2_criteria = ["B2 criterion one", "B2 criterion two"]
    b4_note = (
        f"B4 completed for source {OLD_SHA}, Actions run {RUN_ID}. "
        "Controlled non-production target restore, production disaster recovery "
        "and WAL/PITR remain NOT TESTED."
    )
    return {
        "execution": {
            "current_gate": "BACKEND-001",
            "current_subtask": B2_ID,
            "current_task": f"{B2_ID}: API security and trusted context — production binding.",
            "current_acceptance_criteria": b2_criteria,
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "gate_plans": {
            "BACKEND-001": {
                "status": "CURRENT",
                "current_subtask": B2_ID,
                "acceptance_criteria": [
                    f"BACKEND-001-AC{i:02d}" for i in range(1, 11)
                ],
                "criteria_state": [
                    {
                        "id": f"BACKEND-001-AC{i:02d}",
                        "status": "PENDING",
                        "evidence": None,
                        "verified_at": None,
                    }
                    for i in range(1, 11)
                ],
                "subtasks": [
                    {"id": "BACKEND-001-B0", "status": "DONE"},
                    {"id": "BACKEND-001-B1", "status": "DONE"},
                    {"id": "BACKEND-001-B2-FOUNDATION", "status": "DONE"},
                    {"id": "BACKEND-001-B3", "status": "DONE"},
                    {
                        "id": B4_ID,
                        "title": "PostgreSQL integration",
                        "status": "DONE",
                        "completed_at": "2026-11-26T11:13:45+00:00",
                        "acceptance_criteria": b4_criteria,
                        "note": b4_note,
                    },
                    {
                        "id": B2_ID,
                        "title": "API security and trusted context — production binding",
                        "status": "CURRENT",
                        "acceptance_criteria": b2_criteria,
                    },
                    {"id": "BACKEND-001-B5", "status": "PENDING"},
                ],
            }
        },
        "events": [
            {
                "id": "236ee797-3a16-4f94-9dc8-e548ef5000db",
                "time": "2026-11-26T11:13:45+00:00",
                "type": "SUBTASK_COMPLETED",
                "payload": {"id": B4_ID, "note": b4_note},
            }
        ],
    }


class OwnerPushTests(unittest.TestCase):
    def test_accepts_exact_owner_push_and_reopen_prefix(self) -> None:
        event = {
            "ref": BRANCH_REF,
            "after": SOURCE_SHA,
            "repository": {"full_name": REPOSITORY},
            "sender": {"login": OWNER},
            "head_commit": {
                "message": f"{APPROVAL_PREFIX} reopen B4 for recovery completion"
            },
        }
        env = {
            "GITHUB_ACTOR": OWNER,
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": BRANCH_REF,
            "GITHUB_REPOSITORY": REPOSITORY,
            "EXPECTED_SHA": SOURCE_SHA,
            "VERIFIED_CODE_SHA": SOURCE_SHA,
        }
        validate_owner_push(event, env, SOURCE_SHA)

    def test_rejects_non_owner_actor(self) -> None:
        event = {
            "ref": BRANCH_REF,
            "after": SOURCE_SHA,
            "repository": {"full_name": REPOSITORY},
            "sender": {"login": OWNER},
            "head_commit": {"message": f"{APPROVAL_PREFIX} reason"},
        }
        env = {
            "GITHUB_ACTOR": "other-user",
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": BRANCH_REF,
            "GITHUB_REPOSITORY": REPOSITORY,
            "EXPECTED_SHA": SOURCE_SHA,
            "VERIFIED_CODE_SHA": SOURCE_SHA,
        }
        with self.assertRaises(ValueError):
            validate_owner_push(event, env, SOURCE_SHA)

    def test_rejects_wrong_branch_repo_sha_sender_or_prefix(self) -> None:
        base_event = {
            "ref": BRANCH_REF,
            "after": SOURCE_SHA,
            "repository": {"full_name": REPOSITORY},
            "sender": {"login": OWNER},
            "head_commit": {"message": f"{APPROVAL_PREFIX} reason"},
        }
        env = {
            "GITHUB_ACTOR": OWNER,
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": BRANCH_REF,
            "GITHUB_REPOSITORY": REPOSITORY,
            "EXPECTED_SHA": SOURCE_SHA,
            "VERIFIED_CODE_SHA": SOURCE_SHA,
        }
        cases = [
            ({**base_event, "ref": "refs/heads/main"}, env),
            ({**base_event, "repository": {"full_name": "other/repo"}}, env),
            ({**base_event, "sender": {"login": "not-owner"}}, env),
            ({**base_event, "head_commit": {"message": "ordinary commit"}}, env),
            (base_event, {**env, "GITHUB_EVENT_NAME": "workflow_dispatch"}),
            (base_event, {**env, "VERIFIED_CODE_SHA": "f" * 40}),
        ]
        for event, environment in cases:
            with self.subTest(event=event, environment=environment):
                with self.assertRaises(ValueError):
                    validate_owner_push(event, environment, SOURCE_SHA)


class StateReopenTests(unittest.TestCase):
    def test_baseline_requires_b4_done_b2_current_and_incomplete_target_recovery(self) -> None:
        validate_reopen_baseline(sample_state())

    def test_rejects_stale_or_already_reopened_state(self) -> None:
        state = sample_state()
        state["gate_plans"]["BACKEND-001"]["subtasks"][4]["status"] = "CURRENT"
        with self.assertRaises(ValueError):
            validate_reopen_baseline(state)

        state = sample_state()
        state["execution"]["current_subtask"] = B4_ID
        with self.assertRaises(ValueError):
            validate_reopen_baseline(state)

    def test_rejects_state_without_explicit_recovery_gap(self) -> None:
        state = sample_state()
        b4 = state["gate_plans"]["BACKEND-001"]["subtasks"][4]
        b4["note"] = (
            f"Completed for source {PREVIOUS_B4_SHA}; "
            f"Actions run {PREVIOUS_RUN_ID}."
        )
        with self.assertRaises(ValueError):
            validate_reopen_baseline(state)

    def test_reopen_changes_only_b4_and_b2_task_statuses_and_preserves_history(self) -> None:
        state = sample_state()
        before = copy.deepcopy(state)
        payload = apply_reopen_transition(
            state,
            expected_sha=SOURCE_SHA,
            run_id="45980000000",
            attempt="1",
            owner=OWNER,
            owner_id=OWNER_ID,
            repository_id=REPOSITORY_ID,
            oidc_issuer=OIDC_ISSUER,
            oidc_subject=EXPECTED_OIDC_SUBJECT,
            timestamp=TIMESTAMP,
        )
        gate = state["gate_plans"]["BACKEND-001"]
        tasks = {item["id"]: item for item in gate["subtasks"]}

        self.assertEqual(tasks[B4_ID]["status"], "CURRENT")
        self.assertNotIn("completed_at", tasks[B4_ID])
        self.assertEqual(tasks[B2_ID]["status"], "PENDING")
        self.assertEqual(gate["current_subtask"], B4_ID)
        self.assertEqual(state["execution"]["current_subtask"], B4_ID)
        self.assertEqual(
            state["execution"]["current_acceptance_criteria"],
            tasks[B4_ID]["acceptance_criteria"],
        )

        before_tasks = {
            item["id"]: item
            for item in before["gate_plans"]["BACKEND-001"]["subtasks"]
        }
        for task_id in (
            "BACKEND-001-B0",
            "BACKEND-001-B1",
            "BACKEND-001-B2-FOUNDATION",
            "BACKEND-001-B3",
            "BACKEND-001-B5",
        ):
            self.assertEqual(
                tasks[task_id]["status"],
                before_tasks[task_id]["status"],
            )

        self.assertEqual(
            gate["criteria_state"],
            before["gate_plans"]["BACKEND-001"]["criteria_state"],
        )
        self.assertEqual(state["events"][0], before["events"][0])
        self.assertEqual(state["events"][-1]["type"], "SUBTASK_REOPENED")
        self.assertEqual(state["events"][-1]["payload"], payload)
        self.assertIn(PREVIOUS_B4_SHA, payload["previous_completion_note"])
        self.assertEqual(payload["previous_completion_run_id"], PREVIOUS_RUN_ID)
        self.assertEqual(payload["approved_owner_id"], OWNER_ID)
        self.assertEqual(payload["approved_repository_id"], REPOSITORY_ID)
        self.assertEqual(payload["oidc_issuer"], OIDC_ISSUER)
        self.assertEqual(payload["oidc_subject"], EXPECTED_OIDC_SUBJECT)

    def test_refuses_unexpected_reopen_task_or_invalid_sha(self) -> None:
        with self.assertRaises(ValueError):
            apply_reopen_transition(
                sample_state(),
                expected_sha="bad-sha",
                run_id="45980000000",
                attempt="1",
                owner=OWNER,
                owner_id=OWNER_ID,
                repository_id=REPOSITORY_ID,
                oidc_issuer=OIDC_ISSUER,
                oidc_subject=EXPECTED_OIDC_SUBJECT,
                timestamp=TIMESTAMP,
            )

    def test_reopen_rejects_unverified_owner_or_repository_oidc_identity(self) -> None:
        cases = [
            {
                "owner_id": "999",
                "repository_id": REPOSITORY_ID,
                "oidc_issuer": OIDC_ISSUER,
                "oidc_subject": EXPECTED_OIDC_SUBJECT,
            },
            {
                "owner_id": OWNER_ID,
                "repository_id": "999",
                "oidc_issuer": OIDC_ISSUER,
                "oidc_subject": EXPECTED_OIDC_SUBJECT,
            },
            {
                "owner_id": OWNER_ID,
                "repository_id": REPOSITORY_ID,
                "oidc_issuer": "https://invalid.example",
                "oidc_subject": EXPECTED_OIDC_SUBJECT,
            },
            {
                "owner_id": OWNER_ID,
                "repository_id": REPOSITORY_ID,
                "oidc_issuer": OIDC_ISSUER,
                "oidc_subject": "wrong-subject",
            },
        ]
        for identity in cases:
            with self.subTest(identity=identity):
                with self.assertRaises(ValueError):
                    apply_reopen_transition(
                        sample_state(),
                        expected_sha=SOURCE_SHA,
                        run_id="45980000000",
                        attempt="1",
                        owner=OWNER,
                        **identity,
                        timestamp=TIMESTAMP,
                    )


class CommitScopeTests(unittest.TestCase):
    def test_exact_owner_reopen_files_and_unchanged_authority_blobs_are_required(self) -> None:
        pins = {
            "REOS_CONTROL_CENTER/data/state.json": "3482877a8e321f9d81782270bb44cfaeec297496",
            "REOS_CONTROL_CENTER/B4 ka work plan": "84c94c82ac5b0fde7c7bdf94acca235402c465ab",
            "REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure": "f8d9cd456568cc6c8eaae0caf764123a7e859ba6",
            "REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-target-backup-restore-evidence.md": "9798c2b964426dd37f190108460f9120a6174555",
            "REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-completion-ci-evidence.md": "9d954208406309a55afba3d1b22fe0ceea65ed69",
        }

        def fake_run(command, *, capture=True):
            if command == ["git", "rev-parse", "HEAD"]:
                return SOURCE_SHA
            if command[:2] == ["git", "merge-base"]:
                return ""
            if command[:2] == ["git", "diff"]:
                return "\n".join(sorted(ALLOWED_OWNER_COMMIT_PATHS))
            if command == ["git", "status", "--porcelain=v1", "--untracked-files=all"]:
                return ""
            if command[:2] == ["git", "rev-parse"] and len(command) == 3 and ":" in command[2]:
                return pins[command[2].split(":", 1)[1]]
            if command[:2] == ["git", "fetch"]:
                return ""
            if command == ["git", "rev-parse", "FETCH_HEAD"]:
                return SOURCE_SHA
            raise AssertionError(f"unexpected command: {command}")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ALLOWED_OWNER_COMMIT_PATHS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("verified non-empty source", encoding="utf-8")

            with (
                patch.object(guarded_reopen, "ROOT", root),
                patch("guarded_reopen.run", side_effect=fake_run),
            ):
                verify_commit_scope(SOURCE_SHA)

    def test_commit_scope_rejects_state_or_other_unapproved_file_changes(self) -> None:
        with patch("guarded_reopen.run") as run_mock:
            run_mock.side_effect = [
                SOURCE_SHA,
                "",
                STATE_PATH,
            ]
            with self.assertRaises(SystemExit):
                verify_commit_scope(SOURCE_SHA)


class RemoteReadbackTests(unittest.TestCase):
    def test_remote_readback_requires_exact_reopen_event_and_preserved_original_event(self) -> None:
        state = sample_state()
        payload = apply_reopen_transition(
            state,
            expected_sha=SOURCE_SHA,
            run_id="45980000000",
            attempt="1",
            owner=OWNER,
            owner_id=OWNER_ID,
            repository_id=REPOSITORY_ID,
            oidc_issuer=OIDC_ISSUER,
            oidc_subject=EXPECTED_OIDC_SUBJECT,
            timestamp=TIMESTAMP,
        )
        validate_reopen_baseline_after(
            state,
            expected_sha=SOURCE_SHA,
            run_id="45980000000",
        )
        self.assertEqual(
            payload["previous_completion_event_id"],
            "236ee797-3a16-4f94-9dc8-e548ef5000db",
        )

    def test_remote_readback_rejects_missing_or_duplicate_reopen_event(self) -> None:
        state = sample_state()
        apply_reopen_transition(
            state,
            expected_sha=SOURCE_SHA,
            run_id="45980000000",
            attempt="1",
            owner=OWNER,
            owner_id=OWNER_ID,
            repository_id=REPOSITORY_ID,
            oidc_issuer=OIDC_ISSUER,
            oidc_subject=EXPECTED_OIDC_SUBJECT,
            timestamp=TIMESTAMP,
        )
        state["events"].append(copy.deepcopy(state["events"][-1]))
        with self.assertRaises(SystemExit):
            validate_reopen_baseline_after(
                state,
                expected_sha=SOURCE_SHA,
                run_id="45980000000",
            )

    def test_remote_readback_rejects_acceptance_criteria_or_gate_projection_drift(self) -> None:
        state = sample_state()
        apply_reopen_transition(
            state,
            expected_sha=SOURCE_SHA,
            run_id="45980000000",
            attempt="1",
            owner=OWNER,
            owner_id=OWNER_ID,
            repository_id=REPOSITORY_ID,
            oidc_issuer=OIDC_ISSUER,
            oidc_subject=EXPECTED_OIDC_SUBJECT,
            timestamp=TIMESTAMP,
        )
        state["gate_plans"]["BACKEND-001"]["subtasks"][4]["acceptance_criteria"][0] = "changed"
        with self.assertRaises(SystemExit):
            validate_reopen_baseline_after(
                state,
                expected_sha=SOURCE_SHA,
                run_id="45980000000",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
