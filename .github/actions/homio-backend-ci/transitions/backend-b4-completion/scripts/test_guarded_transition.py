from __future__ import annotations

import ast
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

from guarded_transition import (
    APPROVAL_PREFIX,
    B4_ACCEPTANCE_CRITERIA,
    B4_COMPLETION_EVIDENCE_PATH,
    BASELINE_GUARD_TEST_BLOB_SHA,
    BASELINE_HEAD,
    BASELINE_MASTER_BLOB_SHA,
    BASELINE_PLAN_BLOB_SHA,
    BASELINE_REGISTER_BLOB_SHA,
    BASELINE_STATE_BLOB_SHA,
    BRANCH_REF,
    EXPECTED_SOURCE_PATHS,
    GUARD_PATH,
    GUARD_TEST_PATH,
    MIGRATION_DIRECTORY,
    OWNER,
    REPOSITORY,
    TARGET_RECOVERY_EVIDENCE_PATH,
    _CredentialSafeRedirectHandler,
    _download_job_log,
    controller,
    expected_subtask_statuses,
    read_state,
    render_completion_evidence,
    validate_backend_verification_log,
    validate_source_paths,
    validate_state,
    verify_migration_manifest,
    verify_owner_push,
    verify_physical_schema_manifest,
    verify_target_recovery_evidence_text,
)


B4_APPROVAL_TEST_SHA = "0123456789abcdef0123456789abcdef01234567"


class B4CanonicalTransitionContractTests(unittest.TestCase):
    @staticmethod
    def _rehash(state: dict) -> None:
        state["integrity"]["sha256"] = controller.calculate_hash(state)

    @staticmethod
    def _transitioned_state() -> dict:
        state = copy.deepcopy(read_state())
        gate = state["gate_plans"]["BACKEND-001"]
        execution = state["execution"]
        subtasks = {item["id"]: item for item in gate["subtasks"]}

        subtasks["BACKEND-001-B4"]["status"] = "DONE"
        subtasks["BACKEND-001-B4"]["note"] = (
            "BACKEND-001-B4 completed through the guarded Control Center; "
            "source SHA=0123456789abcdef0123456789abcdef01234567; "
            "run 987654321, attempt 1. All eight B4 acceptance criteria "
            "were independently verified. Production release readiness "
            "is not claimed."
        )
        subtasks["BACKEND-001-B2-PRODUCTION-BINDING"]["status"] = "CURRENT"
        gate["current_subtask"] = "BACKEND-001-B2-PRODUCTION-BINDING"
        execution["current_subtask"] = "BACKEND-001-B2-PRODUCTION-BINDING"
        execution["current_task"] = (
            "BACKEND-001-B2-PRODUCTION-BINDING: "
            "API security and trusted context — production binding."
        )
        execution["current_acceptance_criteria"] = subtasks[
            "BACKEND-001-B2-PRODUCTION-BINDING"
        ]["acceptance_criteria"]
        B4CanonicalTransitionContractTests._rehash(state)
        return state

    @staticmethod
    def _owner_push_environment(
        directory: Path,
        *,
        actor: str = OWNER,
        event_name: str = "push",
        environment_ref: str = BRANCH_REF,
        environment_repository: str = REPOSITORY,
        expected_sha: str = B4_APPROVAL_TEST_SHA,
        verified_code_sha: str = B4_APPROVAL_TEST_SHA,
        event_ref: str = BRANCH_REF,
        event_after: str = B4_APPROVAL_TEST_SHA,
        event_repository: str = REPOSITORY,
        sender: str = OWNER,
        message: object = (
            f"{APPROVAL_PREFIX} Owner-authorized B4 completion request"
        ),
    ) -> dict[str, str]:
        event_path = directory / "github-push-event.json"
        event = {
            "ref": event_ref,
            "after": event_after,
            "repository": {"full_name": event_repository},
            "sender": {"login": sender},
            "head_commit": {"message": message},
        }
        event_path.write_text(
            json.dumps(event),
            encoding="utf-8",
        )

        return {
            "GITHUB_ACTOR": actor,
            "GITHUB_EVENT_NAME": event_name,
            "GITHUB_EVENT_PATH": str(event_path),
            "GITHUB_REF": environment_ref,
            "GITHUB_REPOSITORY": environment_repository,
            "EXPECTED_SHA": expected_sha,
            "VERIFIED_CODE_SHA": verified_code_sha,
            "ACTIONS_RUN_ID": "45800000000",
            "ACTIONS_RUN_ATTEMPT": "1",
            "ACTIONS_SERVER_URL": "https://github.com",
            "ACTIONS_REPOSITORY": REPOSITORY,
        }

    def test_completion_evidence_renderer_removes_trailing_whitespace(self) -> None:
        lines = [
            "**Document ID:** B4-CI-001  ",
            "",
            "- **Workstream:** BACKEND-001\t",
            "## Evidence identity",
            "Final marker",
        ]

        rendered = render_completion_evidence(lines)

        self.assertEqual(
            rendered,
            "**Document ID:** B4-CI-001\n\n"
            "- **Workstream:** BACKEND-001\n"
            "## Evidence identity\n"
            "Final marker",
        )
        self.assertTrue(
            all(line == line.rstrip() for line in rendered.splitlines()),
            "generated completion evidence must not contain trailing whitespace",
        )
        self.assertEqual(
            render_completion_evidence(rendered.split("\n")),
            rendered,
            "completion evidence rendering must be idempotent",
        )

    def test_guard_required_entry_points_remain_at_module_scope(self) -> None:
        source_path = Path(__file__).with_name("guarded_transition.py")
        source = source_path.read_text(encoding="utf-8")
        syntax_tree = ast.parse(source, filename=str(source_path))

        module_functions = {
            node.name
            for node in syntax_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        required_functions = {
            "verify_master_and_plan",
            "request_github_oidc_token",
            "read_state",
            "main",
        }
        self.assertTrue(
            required_functions.issubset(module_functions),
            "B4 guard entry points must remain top-level module functions; "
            f"missing={sorted(required_functions - module_functions)}",
        )

    def test_owner_push_accepts_exact_owner_identity_and_approval_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = self._owner_push_environment(Path(temporary))
            with patch.dict(os.environ, environment, clear=True):
                event = verify_owner_push(B4_APPROVAL_TEST_SHA)

        self.assertEqual(event["ref"], BRANCH_REF)
        self.assertEqual(event["after"], B4_APPROVAL_TEST_SHA)
        self.assertEqual(
            event["repository"]["full_name"],
            REPOSITORY,
        )
        self.assertEqual(event["sender"]["login"], OWNER)
        self.assertTrue(
            event["head_commit"]["message"].startswith(APPROVAL_PREFIX)
        )

    def test_owner_push_rejects_invalid_owner_event_and_approval_metadata(self) -> None:
        invalid_cases = (
            ("non-owner actor", {"actor": "untrusted-actor"}),
            ("non-push event", {"event_name": "workflow_dispatch"}),
            ("wrong environment branch", {"environment_ref": "refs/heads/main"}),
            (
                "wrong environment repository",
                {"environment_repository": "another-owner/another-repo"},
            ),
            ("wrong expected SHA", {"expected_sha": "f" * 40}),
            ("wrong verified SHA", {"verified_code_sha": "e" * 40}),
            ("wrong event branch", {"event_ref": "refs/heads/main"}),
            ("wrong event SHA", {"event_after": "d" * 40}),
            (
                "wrong event repository",
                {"event_repository": "another-owner/another-repo"},
            ),
            ("wrong event sender", {"sender": "untrusted-sender"}),
            (
                "leading whitespace before approval prefix",
                {"message": f" {APPROVAL_PREFIX} invalid prefix position"},
            ),
            (
                "missing approval prefix",
                {"message": "Update test_guarded_transition.py"},
            ),
            ("non-string commit message", {"message": None}),
        )

        for label, changes in invalid_cases:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temporary:
                    environment = self._owner_push_environment(
                        Path(temporary),
                        **changes,
                    )
                    with patch.dict(os.environ, environment, clear=True):
                        with self.assertRaises(SystemExit):
                            verify_owner_push(B4_APPROVAL_TEST_SHA)

    def test_baseline_is_pinned_to_the_live_b4_checkpoint(self) -> None:
        self.assertEqual(len(BASELINE_HEAD), 40)
        self.assertEqual(len(BASELINE_STATE_BLOB_SHA), 40)
        self.assertEqual(len(BASELINE_MASTER_BLOB_SHA), 40)
        self.assertEqual(len(BASELINE_PLAN_BLOB_SHA), 40)
        self.assertEqual(len(BASELINE_REGISTER_BLOB_SHA), 40)
        self.assertEqual(len(BASELINE_GUARD_TEST_BLOB_SHA), 40)
        self.assertEqual(
            TARGET_RECOVERY_EVIDENCE_PATH,
            "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
            "B4-target-backup-restore-evidence.md",
        )
        self.assertEqual(
            B4_COMPLETION_EVIDENCE_PATH,
            "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
            "B4-completion-ci-evidence.md",
        )

    def test_guard_and_regression_test_are_the_only_allowed_source_paths(self) -> None:
        self.assertEqual(
            EXPECTED_SOURCE_PATHS,
            {
                GUARD_PATH,
                GUARD_TEST_PATH,
            },
        )
        validate_source_paths(sorted(EXPECTED_SOURCE_PATHS))

        with self.assertRaises(SystemExit):
            validate_source_paths(
                sorted(EXPECTED_SOURCE_PATHS | {"REOS_CONTROL_CENTER/data/state.json"})
            )

        with self.assertRaises(SystemExit):
            validate_source_paths([GUARD_PATH])

    def test_expected_statuses_close_only_b4_and_advance_to_b2_production(self) -> None:
        before = expected_subtask_statuses(transitioned=False)
        after = expected_subtask_statuses(transitioned=True)

        self.assertEqual(before["BACKEND-001-B3"], "DONE")
        self.assertEqual(before["BACKEND-001-B4"], "CURRENT")
        self.assertEqual(
            before["BACKEND-001-B2-PRODUCTION-BINDING"], "PENDING"
        )
        self.assertEqual(after["BACKEND-001-B4"], "DONE")
        self.assertEqual(
            after["BACKEND-001-B2-PRODUCTION-BINDING"], "CURRENT"
        )
        self.assertEqual(after["BACKEND-001-B5"], "PENDING")
        self.assertEqual(after["BACKEND-001-B10"], "PENDING")

    def test_live_canonical_state_passes_b4_pre_transition_validation(self) -> None:
        state = read_state()
        validate_state(state, transitioned=False)
        self.assertEqual(
            state["execution"]["current_subtask"], "BACKEND-001-B4"
        )
        self.assertEqual(
            state["execution"]["current_acceptance_criteria"],
            B4_ACCEPTANCE_CRITERIA,
        )

    def test_post_transition_projection_changes_only_b4_to_b2_production(self) -> None:
        state = self._transitioned_state()
        validate_state(
            state,
            transitioned=True,
            expected_sha="0123456789abcdef0123456789abcdef01234567",
            run_id="987654321",
        )
        statuses = {
            item["id"]: item["status"]
            for item in state["gate_plans"]["BACKEND-001"]["subtasks"]
        }
        self.assertEqual(statuses["BACKEND-001-B4"], "DONE")
        self.assertEqual(
            statuses["BACKEND-001-B2-PRODUCTION-BINDING"], "CURRENT"
        )
        self.assertEqual(statuses["BACKEND-001-B5"], "PENDING")

    def test_transition_rejects_reopening_b3_predecessor(self) -> None:
        state = copy.deepcopy(read_state())
        subtasks = state["gate_plans"]["BACKEND-001"]["subtasks"]
        next(item for item in subtasks if item["id"] == "BACKEND-001-B3")[
            "status"
        ] = "CURRENT"
        self._rehash(state)
        with self.assertRaises(SystemExit):
            validate_state(state, transitioned=False)

    def test_transition_rejects_any_b4_acceptance_criterion_change(self) -> None:
        state = copy.deepcopy(read_state())
        gate = state["gate_plans"]["BACKEND-001"]
        b4 = next(
            item for item in gate["subtasks"] if item["id"] == "BACKEND-001-B4"
        )
        b4["acceptance_criteria"][0] = "Invented or weakened criterion."
        self._rehash(state)
        with self.assertRaises(SystemExit):
            validate_state(state, transitioned=False)

    def test_transition_rejects_gate_level_acceptance_mutation(self) -> None:
        state = copy.deepcopy(read_state())
        state["gate_plans"]["BACKEND-001"]["criteria_state"][0][
            "status"
        ] = "VERIFIED"
        self._rehash(state)
        with self.assertRaises(SystemExit):
            validate_state(state, transitioned=False)

    def test_transition_rejects_a_note_without_exact_source_and_run_identity(self) -> None:
        state = self._transitioned_state()
        b4 = next(
            item
            for item in state["gate_plans"]["BACKEND-001"]["subtasks"]
            if item["id"] == "BACKEND-001-B4"
        )
        b4["note"] = "B4 complete without source or Actions evidence."
        self._rehash(state)
        with self.assertRaises(SystemExit):
            validate_state(
                state,
                transitioned=True,
                expected_sha="0123456789abcdef0123456789abcdef01234567",
                run_id="987654321",
            )

    def test_job_log_download_reads_github_plain_text_response(self) -> None:
        expected_log = (
            "2026-11-26T08:21:18.0000000Z HEAD is now at 6c41cc7 "
            "Fix authenticated Actions log redirect handling\n"
            "Backend verification completed successfully.\n"
        )
        with (
            patch.dict(
                os.environ,
                {"ACTIONS_API_URL": "https://api.github.com"},
            ),
            patch(
                "guarded_transition._api_get_bytes",
                return_value=expected_log.encode("utf-8"),
            ) as get_bytes,
        ):
            actual_log = _download_job_log(139780942465)

        self.assertEqual(actual_log, expected_log)
        get_bytes.assert_called_once_with(
            "https://api.github.com/repos/"
            "prajaktaranjane80-sketch/Homio/"
            "actions/jobs/139780942465/logs"
        )

    def test_job_log_download_rejects_invalid_job_identifiers(self) -> None:
        invalid_ids = (
            0,
            -1,
            True,
            False,
            "139780942465",
            None,
        )

        for job_id in invalid_ids:
            with self.subTest(job_id=job_id):
                with patch(
                    "guarded_transition._api_get_bytes"
                ) as get_bytes:
                    with self.assertRaises(SystemExit):
                        _download_job_log(job_id)

                    get_bytes.assert_not_called()

    def test_job_log_download_rejects_an_empty_response(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"ACTIONS_API_URL": "https://api.github.com"},
            ),
            patch(
                "guarded_transition._api_get_bytes",
                return_value=b"",
            ),
        ):
            with self.assertRaises(SystemExit):
                _download_job_log(139780942465)

    def test_job_log_download_rejects_zip_archive_payload(self) -> None:
        zip_payload = b"PK\x03\x04fake-archive-payload"

        with (
            patch.dict(
                os.environ,
                {"ACTIONS_API_URL": "https://api.github.com"},
            ),
            patch(
                "guarded_transition._api_get_bytes",
                return_value=zip_payload,
            ),
        ):
            with self.assertRaises(SystemExit):
                _download_job_log(139780942465)

    def test_job_log_download_rejects_binary_payload(self) -> None:
        binary_payload = b"plain-prefix\x00binary-suffix"

        with (
            patch.dict(
                os.environ,
                {"ACTIONS_API_URL": "https://api.github.com"},
            ),
            patch(
                "guarded_transition._api_get_bytes",
                return_value=binary_payload,
            ),
        ):
            with self.assertRaises(SystemExit):
                _download_job_log(139780942465)

    def test_job_log_download_preserves_readable_text_with_invalid_utf8_bytes(self) -> None:
        raw_log = b"GitHub job log contains a replacement byte: \xff\n"

        with (
            patch.dict(
                os.environ,
                {"ACTIONS_API_URL": "https://api.github.com"},
            ),
            patch(
                "guarded_transition._api_get_bytes",
                return_value=raw_log,
            ),
        ):
            actual_log = _download_job_log(139780942465)

        self.assertIn("GitHub job log contains a replacement byte:", actual_log)
        self.assertIn("\ufffd", actual_log)

    def test_redirect_handler_removes_credentials_for_cross_origin_redirects(self) -> None:
        request = Request(
            "https://api.github.com/repos/example/repo/actions/jobs/123/logs",
            headers={
                "Authorization": "Bearer sensitive-token",
                "Proxy-Authorization": "Basic sensitive-proxy-token",
                "Accept": "application/vnd.github+json",
            },
        )
        redirected = _CredentialSafeRedirectHandler().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://logs.githubusercontent.example/signed-download",
        )

        self.assertIsNotNone(redirected)
        self.assertNotIn("Authorization", redirected.headers)
        self.assertNotIn("Proxy-Authorization", redirected.headers)
        self.assertEqual(
            redirected.headers.get("Accept"),
            "application/vnd.github+json",
        )

    def test_redirect_handler_preserves_credentials_for_same_origin_redirects(self) -> None:
        request = Request(
            "https://api.github.com/repos/example/repo/actions/jobs/123/logs",
            headers={
                "Authorization": "Bearer same-origin-token",
                "Accept": "application/vnd.github+json",
            },
        )
        redirected = _CredentialSafeRedirectHandler().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://api.github.com/repos/example/repo/actions/jobs/123/logs/",
        )

        self.assertIsNotNone(redirected)
        self.assertEqual(
            redirected.headers.get("Authorization"),
            "Bearer same-origin-token",
        )

    def test_verification_log_requires_all_suites_and_no_skips(self) -> None:
        log = """
        PASS: 16 independent PostgreSQL tenant writes committed without lost updates.
        PASS: Redis 8.0.3 atomic shared-window enforcement, 24 concurrent calls across independent clients, and TTL reset.
        ✓ tests/integration/postgres-arch037-schema.integration.test.ts (12 tests) 758ms
        ✓ tests/unit/postgres-migrations.test.ts (26 tests) 27ms
        ✓ tests/integration/postgres-b4-recovery.integration.test.ts (1 test) 1721ms
        ✓ tests/integration/postgres-security-audit.integration.test.ts (7 tests) 331ms
        ✓ tests/integration/postgres-session-store.integration.test.ts (3 tests) 435ms
        ✓ tests/unit/postgres-global-transaction.test.ts (3 tests) 12ms
        ✓ tests/unit/postgres-role-safety.test.ts (7 tests) 11ms
        ✓ tests/unit/redis-rate-limit.test.ts (8 tests) 12ms
        ✓ tests/integration/production-persistence.integration.test.ts (5 tests) 396ms
        ✓ tests/integration/core002-outbox.integration.test.ts (1 test) 510ms
        ✓ tests/unit/postgres.test.ts (12 tests) 17ms
        ✓ tests/unit/production-runtime.test.ts (6 tests) 10ms
        ✓ tests/unit/dependency-readiness.test.ts (1 test) 73ms
        ✓ tests/unit/api-security.test.ts (25 tests) 492ms
        B4_RECOVERY_METHOD=FULL_DATABASE_PG_DUMP_TO_SEPARATE_DATABASE
        B4_RECOVERY_SOURCE_DATABASE=homio_b4_recovery_abcd1234
        B4_RECOVERY_TARGET_DATABASE=homio_b4_restore_abcd1234
        B4_RECOVERY_BACKUP_SHA256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        B4_RECOVERY_BACKUP_BYTES=113631
        B4_RECOVERY_SCHEMA_SHA256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
        B4_RECOVERY_MIGRATION_COUNT=11
        B4_RECOVERY_REPLAY_APPLIED_COUNT=0
        B4_RECOVERY_SCHEMA_INTEGRITY=PASS
        B4_RECOVERY_DATA_INTEGRITY=PASS
        B4_RECOVERY_TENANT_ISOLATION=PASS
        B4_RECOVERY_DATABASE_ACL=PASS
        B4_RECOVERY_ROLE_AND_GRANT_INTEGRITY=PASS
        B4_RECOVERY_TARGET_CLASS=EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4
        B4_RECOVERY_PRODUCTION_TARGET=NOT_TESTED
        B4_RECOVERY_VERIFICATION=PASS
        B1_REPRODUCIBLE_BUILD=PASS
        PRODUCTION_RELEASE_READY=false
        PRODUCTION_RELEASE_BLOCKERS=18
        Run complete ACRL suite
        1466 passed in 9.47s
        Test Files 24 passed (24)
        Tests 201 passed (201)
        """
        summary = validate_backend_verification_log(log)
        self.assertEqual(summary["test_files_passed"], 24)
        self.assertEqual(summary["tests_passed"], 201)
        self.assertEqual(summary["acrl_tests_passed"], 1466)
        self.assertFalse(summary["production_release_ready"])
        self.assertEqual(summary["production_release_blockers"], 18)
        self.assertEqual(summary["recovery"]["migration_count"], 11)

    def test_verification_log_parses_timestamp_prefixed_github_actions_lines(self) -> None:
        timestamped = "\n".join(
            f"2026-11-25T14:15:40.0000000Z {line.strip()}"
            for line in self._valid_log().splitlines()
            if line.strip()
        )
        summary = validate_backend_verification_log(timestamped)
        self.assertEqual(summary["recovery"]["backup_bytes"], 113631)
        self.assertEqual(
            summary["recovery"]["B4_RECOVERY_SOURCE_DATABASE"],
            "homio_b4_recovery_abcd1234",
        )
        self.assertEqual(summary["production_release_blockers"], 18)

    def test_verification_log_rejects_skipped_vitest_tests(self) -> None:
        log = self._valid_log().replace(
            "Tests 201 passed (201)", "Tests 201 passed | 1 skipped (202)"
        )
        with self.assertRaises(SystemExit):
            validate_backend_verification_log(log)

    def test_verification_log_rejects_missing_recovery_integrity_marker(self) -> None:
        log = self._valid_log().replace(
            "B4_RECOVERY_TENANT_ISOLATION=PASS\n", ""
        )
        with self.assertRaises(SystemExit):
            validate_backend_verification_log(log)

    def test_verification_log_rejects_missing_transaction_owner_test(self) -> None:
        log = self._valid_log().replace(
            "✓ tests/unit/postgres-global-transaction.test.ts (3 tests) 12ms\n",
            "",
        )
        with self.assertRaises(SystemExit):
            validate_backend_verification_log(log)

    def test_verification_log_rejects_missing_production_persistence_owner_test(self) -> None:
        log = self._valid_log().replace(
            "✓ tests/integration/production-persistence.integration.test.ts (5 tests) 396ms\n",
            "",
        )
        with self.assertRaises(SystemExit):
            validate_backend_verification_log(log)

    @staticmethod
    def _valid_log() -> str:
        return """
        PASS: 16 independent PostgreSQL tenant writes committed without lost updates.
        PASS: Redis 8.0.3 atomic shared-window enforcement, 24 concurrent calls across independent clients, and TTL reset.
        ✓ tests/integration/postgres-arch037-schema.integration.test.ts (12 tests) 758ms
        ✓ tests/unit/postgres-migrations.test.ts (26 tests) 27ms
        ✓ tests/integration/postgres-b4-recovery.integration.test.ts (1 test) 1721ms
        ✓ tests/integration/postgres-security-audit.integration.test.ts (7 tests) 331ms
        ✓ tests/integration/postgres-session-store.integration.test.ts (3 tests) 435ms
        ✓ tests/unit/postgres-global-transaction.test.ts (3 tests) 12ms
        ✓ tests/unit/postgres-role-safety.test.ts (7 tests) 11ms
        ✓ tests/unit/redis-rate-limit.test.ts (8 tests) 12ms
        ✓ tests/integration/production-persistence.integration.test.ts (5 tests) 396ms
        ✓ tests/integration/core002-outbox.integration.test.ts (1 test) 510ms
        ✓ tests/unit/postgres.test.ts (12 tests) 17ms
        ✓ tests/unit/production-runtime.test.ts (6 tests) 10ms
        ✓ tests/unit/dependency-readiness.test.ts (1 test) 73ms
        ✓ tests/unit/api-security.test.ts (25 tests) 492ms
        B4_RECOVERY_METHOD=FULL_DATABASE_PG_DUMP_TO_SEPARATE_DATABASE
        B4_RECOVERY_SOURCE_DATABASE=homio_b4_recovery_abcd1234
        B4_RECOVERY_TARGET_DATABASE=homio_b4_restore_abcd1234
        B4_RECOVERY_BACKUP_SHA256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        B4_RECOVERY_BACKUP_BYTES=113631
        B4_RECOVERY_SCHEMA_SHA256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
        B4_RECOVERY_MIGRATION_COUNT=11
        B4_RECOVERY_REPLAY_APPLIED_COUNT=0
        B4_RECOVERY_SCHEMA_INTEGRITY=PASS
        B4_RECOVERY_DATA_INTEGRITY=PASS
        B4_RECOVERY_TENANT_ISOLATION=PASS
        B4_RECOVERY_DATABASE_ACL=PASS
        B4_RECOVERY_ROLE_AND_GRANT_INTEGRITY=PASS
        B4_RECOVERY_TARGET_CLASS=EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4
        B4_RECOVERY_PRODUCTION_TARGET=NOT_TESTED
        B4_RECOVERY_VERIFICATION=PASS
        B1_REPRODUCIBLE_BUILD=PASS
        PRODUCTION_RELEASE_READY=false
        PRODUCTION_RELEASE_BLOCKERS=18
        Run complete ACRL suite
        1466 passed in 9.47s
        Test Files 24 passed (24)
        Tests 201 passed (201)
        """

    def test_physical_schema_manifest_preserves_canonical_schema_owners(self) -> None:
        result = verify_physical_schema_manifest()
        self.assertEqual(
            result["schemas"],
            [
                "core001",
                "core002",
                "core003",
                "core004",
                "core006",
                "core007",
                "core008",
                "reos_infra",
            ],
        )
        self.assertTrue(result["no_second_schema_authority"])

    def test_recovery_evidence_requires_ci_only_classification_and_explicit_pitr_limit(self) -> None:
        path = Path(__file__).resolve().parents[6] / TARGET_RECOVERY_EVIDENCE_PATH
        content = path.read_text(encoding="utf-8")
        result = verify_target_recovery_evidence_text(content)
        self.assertEqual(
            result["classification"],
            "EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4",
        )
        self.assertFalse(result["production_tested"])
        self.assertFalse(result["pitr_tested"])
        with self.assertRaises(SystemExit):
            verify_target_recovery_evidence_text(
                content.replace(
                    "| Backup encryption at rest | `NOT_TESTED` |\n",
                    "",
                )
            )

    def test_migration_manifest_has_exact_order_and_checksums(self) -> None:
        records = verify_migration_manifest(MIGRATION_DIRECTORY)
        self.assertEqual(len(records), 11)
        self.assertEqual(
            [record["id"] for record in records],
            [f"{index:08d}" for index in range(1, 12)],
        )
        self.assertTrue(all(len(record["sha256"]) == 64 for record in records))

    def test_migration_manifest_rejects_a_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "migrations"
            shutil.copytree(MIGRATION_DIRECTORY, target)
            (target / "00000011-b4-security-audit-tenant-write-guard.sql").unlink()
            with self.assertRaises(SystemExit):
                verify_migration_manifest(target)


if __name__ == "__main__":
    unittest.main(verbosity=2)
