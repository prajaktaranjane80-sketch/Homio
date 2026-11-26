from __future__ import annotations

from pathlib import Path

import pytest

import AI_AGENT_ENTRYPOINT as entrypoint


REPOSITORY_NAME = "prajaktaranjane80-sketch/Homio"
CANONICAL_BRANCH = "reos-development"
CANONICAL_STATE = "REOS_CONTROL_CENTER/data/state.json"

EXPECTED_ORIGIN = (
    "https://github.com/prajaktaranjane80-sketch/Homio.git"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

ACRL_RUNTIME_RESUME_SCRIPT = (
    REPOSITORY_ROOT
    / ".github/actions/homio-backend-ci/verification/scripts/"
    / "acrl_runtime_resume.sh"
)

GIT_READ_COMMANDS = {
    ("rev-parse", "--show-toplevel"),
    ("branch", "--show-current"),
    ("config", "--get", "remote.origin.url"),
    ("rev-parse", "HEAD"),
    ("status", "--porcelain=v1", "--untracked-files=all"),
    (
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    ),
    (
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...@{upstream}",
    ),
}


def _install_preflight_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    status_output: str = "",
    upstream_output: str = "origin/reos-development",
    upstream_exit_code: int = 0,
    ahead_behind_output: str = "0\t0",
) -> list[tuple[str, ...]]:
    """Install deterministic local Git evidence without network access."""

    repository_root = tmp_path / "Homio"
    control_center = repository_root / "REOS_CONTROL_CENTER"

    t21_path = (
        control_center
        / "AUTONOMY_ENGINE"
        / "continuity"
        / "acrl"
        / "T21_Git_Repository_Read_Write_Coordination"
    )

    control_center.mkdir(parents=True)
    t21_path.mkdir(parents=True)

    monkeypatch.setattr(
        entrypoint,
        "CANONICAL_LOCAL_WORKSPACE",
        repository_root,
    )

    monkeypatch.setattr(
        entrypoint,
        "CANONICAL_CONTROL_CENTER",
        control_center,
    )

    monkeypatch.setattr(
        entrypoint,
        "CONTROL_CENTER_PATH",
        control_center,
    )

    monkeypatch.setattr(
        entrypoint,
        "ACRL_GIT_REPOSITORY_COORDINATION",
        t21_path,
    )

    monkeypatch.setattr(
        entrypoint,
        "EXPECTED_BRANCH",
        CANONICAL_BRANCH,
    )

    monkeypatch.setattr(
        entrypoint,
        "EXPECTED_ORIGIN",
        EXPECTED_ORIGIN,
    )

    monkeypatch.chdir(control_center)

    responses: dict[
        tuple[str, ...],
        tuple[int, str, str],
    ] = {

        ("rev-parse", "--show-toplevel"): (
            0,
            str(repository_root),
            "",
        ),

        ("branch", "--show-current"): (
            0,
            CANONICAL_BRANCH,
            "",
        ),

        ("config", "--get", "remote.origin.url"): (
            0,
            EXPECTED_ORIGIN,
            "",
        ),

        ("rev-parse", "HEAD"): (
            0,
            "a" * 40,
            "",
        ),

        (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ): (
            0,
            status_output,
            "",
        ),

        (
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
        ): (
            upstream_exit_code,
            upstream_output,
            (
                "no upstream configured"
                if upstream_exit_code
                else ""
            ),
        ),

        (
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
        ): (
            0,
            ahead_behind_output,
            "",
        ),
    }

    calls: list[tuple[str, ...]] = []

    def fake_run_git(*args: str) -> tuple[int, str, str]:
        command = tuple(args)
        calls.append(command)

        if command not in responses:
            return 2, "", f"Unexpected Git command: {command!r}"

        return responses[command]

    monkeypatch.setattr(
        entrypoint,
        "_run_git",
        fake_run_git,
    )

    return calls


# ===========================================================================
# CANONICAL IDENTITY AND ACRL BOUNDARIES
# ===========================================================================

def test_entrypoint_contract_has_canonical_identity_and_state_authority():
    contract = entrypoint.contract()
    paths = entrypoint.repository_paths()

    assert contract.project == "HOMIO / REOS"

    assert entrypoint.REPOSITORY_FULL_NAME == REPOSITORY_NAME

    assert entrypoint.EXPECTED_BRANCH == CANONICAL_BRANCH

    assert contract.authoritative_state == CANONICAL_STATE

    assert Path(paths["state"]).as_posix().endswith(
        CANONICAL_STATE
    )

    for key in (
        "t07",
        "t14",
        "t15",
        "t18",
        "t20",
        "t21",
        "t22",
        "t23",
        "t24",
    ):
        assert paths[key]


def test_entrypoint_policy_preserves_separate_acrl_responsibilities():
    combined_rules = "\n".join(
        (
            *entrypoint.AI_OPERATING_RULES,
            *entrypoint.DEVELOPMENT_WORKFLOW_RULES,
            *entrypoint.REMOTE_GIT_SYNCHRONIZATION_RULES,
            *entrypoint.REPOSITORY_PREFLIGHT_RULES,
        )
    )

    for layer in (
        "T07",
        "T14",
        "T15",
        "T18",
        "T20",
        "T21",
        "T22",
        "T23",
        "T24",
    ):
        assert layer in combined_rules

    assert "state.json" in combined_rules

    assert "chat history" in combined_rules.lower()

    assert "standalone runner" in combined_rules.lower()


# ===========================================================================
# DOCUMENT REGISTRY AND WORKSTREAM BOUNDARIES
# ===========================================================================

def test_document_registry_points_to_existing_master_references():
    registry = entrypoint.DOCUMENT_REGISTRY

    expected = {
        "execution_state": CANONICAL_STATE,
        "backend_master": (
            "REOS_CONTROL_CENTER/architecture/backend/plans/"
            "HOMIO_Backend_Structure"
        ),
        "frontend_master": (
            "REOS_CONTROL_CENTER/architecture/frontend/plans/"
            "HOMIO_FRONTEND_MASTER_EXECUTION_PLAN.md"
        ),
        "h360_gap_reference": (
            "REOS_CONTROL_CENTER/architecture/"
            "HOMIO_360_DEGREE_GAP_CLOSURE_EXECUTION_STRUCTURE.md"
        ),
        "ai001_blueprint": (
            "REOS_CONTROL_CENTER/architecture/"
            "AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md"
        ),
        "entrypoint_contract_test": (
            "REOS_CONTROL_CENTER/tets/"
            "test_ai_agent_entrypoint_contract.py"
        ),
    }

    for key, expected_path in expected.items():
        assert registry[key]["path"] == expected_path

    assert (
        registry["execution_state"]["authority"]
        == "SOLE_CANONICAL_EXECUTION_STATE"
    )


def test_backend_and_frontend_have_separate_master_owners():
    routing = entrypoint.WORKSTREAM_ROUTING

    assert set(routing) == {
        "BACKEND",
        "FRONTEND",
        "SHARED_INTEGRATION",
    }

    assert (
        routing["BACKEND"]["master_reference"]
        == entrypoint.DOCUMENT_REGISTRY["backend_master"]["path"]
    )

    assert (
        routing["FRONTEND"]["master_reference"]
        == entrypoint.DOCUMENT_REGISTRY["frontend_master"]["path"]
    )

    backend_exclusions = " ".join(
        routing["BACKEND"]["excludes"]
    ).lower()

    frontend_exclusions = " ".join(
        routing["FRONTEND"]["excludes"]
    ).lower()

    assert "css" in backend_exclusions
    assert "visual ui" in backend_exclusions
    assert "business rules" in frontend_exclusions
    assert "database" in frontend_exclusions


def test_backend_owns_api_contract_and_frontend_consumes_it():
    combined = "\n".join(
        entrypoint.CROSS_CHAT_SYNC_RULES
    ).lower()

    assert "backend is the single owner of api" in combined

    assert "frontend is a consumer" in combined

    assert "second contract owner" in combined


def test_plans_do_not_grant_parallel_task_authorization():
    combined = "\n".join(
        (
            *entrypoint.CROSS_CHAT_SYNC_RULES,
            *entrypoint.AI_OPERATING_RULES,
            *entrypoint.NEW_SESSION_WORKFLOW,
        )
    ).lower()

    assert "separate plans do not grant separate task authorization" in combined

    assert "explicitly approved parallel-work authorization" in combined

    assert "state.json" in combined


def test_shared_integration_is_not_a_third_implementation_owner():
    rule = (
        entrypoint.WORKSTREAM_ROUTING[
            "SHARED_INTEGRATION"
        ]["integration_rule"]
    ).lower()

    assert "not a third implementation owner" in rule

    assert "duplicate" in rule


# ===========================================================================
# CROSS-CHAT SYNC AND EVIDENCE RULES
# ===========================================================================

def test_cross_chat_sync_requires_live_sha_refresh_and_disjoint_paths():
    rules = "\n".join(
        entrypoint.CROSS_CHAT_SYNC_RULES
    ).lower()

    assert "live branch head" in rules

    assert "target blob sha" in rules

    assert "same path" in rules

    assert "commit history" in rules


def test_evidence_rules_bind_actions_to_exact_tested_sha():
    rules = "\n".join(
        entrypoint.EVIDENCE_VERIFICATION_RULES
    ).lower()

    assert "exact head_sha" in rules

    assert "tested sha" in rules

    assert "skipped, cancelled" in rules

    assert "production deployment" in rules


def test_old_handoff_and_continuity_snapshots_are_non_authoritative():
    registry = entrypoint.DOCUMENT_REGISTRY

    assert (
        registry["handoff_packet"]["authority"]
        == "NON_AUTHORITATIVE_DERIVED_SNAPSHOT"
    )

    assert (
        registry["continuity_state"]["authority"]
        == "CONTINUITY_CONTEXT_ONLY"
    )

    assert (
        registry["legacy_state_snapshot"]["authority"]
        == "NON_AUTHORITATIVE_LEGACY"
    )


def test_t14_template_is_not_manually_sealed_by_entrypoint_policy():
    rules = "\n".join(
        entrypoint.FAILURE_RULES
    ).lower()

    assert "t14 cache is uninitialized" in rules

    assert "do not mark it sealed manually" in rules


def test_audit_snapshot_is_explicitly_historical():
    snapshot = entrypoint.LAST_AUDIT_SNAPSHOT

    assert snapshot["branch"] == CANONICAL_BRANCH

    assert snapshot["current_gate_at_review"] == "APP-001"

    assert snapshot["current_task_at_review"] == "APP-001-T01"

    assert "old main-branch" in snapshot["continuity_state_warning"].lower()

    assert "historical evidence" in snapshot["latest_actions_warning"].lower()


# ===========================================================================
# SUPERPOWERS ENGINEERING SKILL INTEGRATION
# ===========================================================================

def test_superpowers_skill_policy_requires_session_start_and_task_routing():

    assert (
        entrypoint.ENGINEERING_SKILL_PROVIDER
        == "Superpowers"
    )

    assert (
        entrypoint.ENGINEERING_SKILL_ENTRYPOINT
        == "using-superpowers"
    )

    routing = entrypoint.ENGINEERING_SKILL_ROUTING

    assert "brainstorming" in routing["new_feature_or_behavior"]

    assert "test-driven-development" in routing["new_feature_or_behavior"]

    assert "systematic-debugging" in routing["bug_or_test_failure"]

    assert "test-driven-development" in routing["bug_or_test_failure"]

    assert (
        "verification-before-completion"
        in routing["completion_and_release_claim"]
    )


def test_superpowers_policy_preserves_acrl_and_state_authority():

    rules = "\n".join(
        entrypoint.ENGINEERING_SKILL_WORKFLOW_RULES
    ).lower()

    assert "does not grant task authorization" in rules

    assert "state.json" in rules

    assert "t07 restart" in rules

    assert "t14 repository manifests" in rules

    assert "duplicate orchestration engine" in rules


def test_startup_instructions_expose_superpowers_integration():

    instructions = entrypoint.startup_instructions()

    assert (
        instructions["engineering_skill_provider"]
        == "Superpowers"
    )

    assert (
        instructions["engineering_skill_entrypoint"]
        == "using-superpowers"
    )

    assert (
        instructions["engineering_skill_discovery_required"]
        is True
    )

    assert (
        instructions["engineering_skill_execution_is_project_authority"]
        is False
    )

    assert "bug_or_test_failure" in (
        instructions["engineering_skill_routing"]
    )

    assert "engineering_skill_workflow_rules" in instructions

    assert instructions["new_session_read_order"][0].startswith("0.")

    assert "using-superpowers" in (
        instructions["new_session_read_order"][0]
    )


# ===========================================================================
# OWNER SAVE POLICY
# ===========================================================================

def test_owner_controlled_github_web_save_is_default():
    assert (
        entrypoint.POWERSHELL_WRITE_MODE
        == "OWNER_CONTROLLED_GITHUB_WEB_UI_ONLY"
    )

    assert entrypoint.POWERSHELL_WRITE_ALLOWED is False

    assert entrypoint.POWERSHELL_IS_VERIFICATION_ONLY is True

    assert (
        entrypoint.POWERSHELL_REMOTE_GITHUB_API_WRITE_ALLOWED
        is False
    )

    assert (
        entrypoint.POWERSHELL_LOCAL_WORKTREE_WRITE_ALLOWED
        is False
    )

    assert (
        entrypoint.POWERSHELL_LOCAL_GIT_MUTATION_ALLOWED
        is False
    )

    assert "owner-controlled github web editor" in (
        entrypoint.IMPLEMENTATION_WRITE_INTERFACE.lower()
    )


# ===========================================================================
# LOCAL PREFLIGHT REGRESSION TESTS
# ===========================================================================

def test_clean_synchronized_checkout_can_pass_local_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    result = entrypoint.git_preflight()

    assert result["cwd_ok"] is True

    assert result["repository_root_ok"] is True

    assert result["branch_ok"] is True

    assert result["origin_ok"] is True

    assert result["local_head_ok"] is True

    assert result["t21_authority_ok"] is True

    assert result["clean_worktree"] is True

    assert result["upstream_configured"] is True

    assert result["upstream_ref"] == "origin/reos-development"

    assert result["ahead_by"] == 0

    assert result["behind_by"] == 0

    assert result["ahead_behind_ok"] is True

    assert result["divergent"] is False

    assert result["ready"] is True

    assert result["diagnostic_only"] is True


@pytest.mark.parametrize(
    "status_output",
    [
        " M tracked_file.py",
        "?? untracked_file.py",
        " M tracked_file.py\n?? untracked_file.py",
        "A  staged_file.py",
        " D deleted_file.py",
    ],
)
def test_dirty_or_untracked_worktree_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    status_output: str,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
        status_output=status_output,
    )

    result = entrypoint.git_preflight()

    assert result["clean_worktree"] is False

    assert result["ready"] is False


def test_missing_upstream_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
        upstream_output="",
        upstream_exit_code=128,
    )

    result = entrypoint.git_preflight()

    assert result["upstream_configured"] is False

    assert result["ahead_behind_ok"] is False

    assert result["ready"] is False


@pytest.mark.parametrize(
    (
        "counts",
        "expected_ahead",
        "expected_behind",
        "expected_divergent",
    ),
    [
        ("1\t0", 1, 0, False),
        ("0\t1", 0, 1, False),
        ("2\t3", 2, 3, True),
    ],
)
def test_ahead_behind_or_divergent_checkout_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    counts: str,
    expected_ahead: int,
    expected_behind: int,
    expected_divergent: bool,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
        ahead_behind_output=counts,
    )

    result = entrypoint.git_preflight()

    assert result["ahead_by"] == expected_ahead

    assert result["behind_by"] == expected_behind

    assert result["divergent"] is expected_divergent

    assert result["ahead_behind_ok"] is False

    assert result["ready"] is False


def test_local_upstream_tracking_does_not_claim_live_remote_proof(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    result = entrypoint.git_preflight()

    assert result["live_remote_tip_proven"] is False

    assert result["remote_readback_required"] is True


def test_preflight_uses_only_expected_read_only_git_queries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    calls = _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    entrypoint.git_preflight()

    assert calls

    assert set(calls).issubset(GIT_READ_COMMANDS)

    forbidden_commands = {
        "add",
        "checkout",
        "clean",
        "commit",
        "fetch",
        "merge",
        "pull",
        "push",
        "rebase",
        "reset",
        "restore",
        "switch",
        "update-ref",
    }

    for command in calls:
        assert command[0] not in forbidden_commands


# ===========================================================================
# STARTUP INSTRUCTION CONTRACT
# ===========================================================================

def test_startup_instructions_expose_canonical_authority_and_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    instructions = entrypoint.startup_instructions()

    preflight = instructions["git_preflight"] if (
        "git_preflight" in instructions
    ) else entrypoint.git_preflight()

    assert instructions["project"] == "HOMIO / REOS"

    assert instructions["authority"] == "REOS_CONTROL_CENTER"

    assert instructions["chat_history_authority"] == "NON_AUTHORITATIVE"

    assert preflight["live_remote_tip_proven"] is False

    assert preflight["remote_readback_required"] is True


def test_startup_instructions_include_registry_and_workstream_routing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    instructions = entrypoint.startup_instructions()

    assert "document_registry" in instructions

    assert "workstream_routing" in instructions

    assert "cross_chat_sync_rules" in instructions

    assert "evidence_verification_rules" in instructions

    assert "new_session_read_order" in instructions

    assert "last_audit_snapshot" in instructions

    assert (
        instructions["workstream_routing"]["BACKEND"]["master_reference"]
        == entrypoint.DOCUMENT_REGISTRY["backend_master"]["path"]
    )

    assert instructions["live_github_refresh_required"] is True

    assert instructions["canonical_state_refresh_required"] is True

    assert instructions["workstream_declaration_required"] is True

    assert instructions["plan_documents_authorize_tasks"] is False


def test_startup_instructions_preserve_owner_write_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    instructions = entrypoint.startup_instructions()

    assert (
        instructions["powershell_write_mode"]
        == "OWNER_CONTROLLED_GITHUB_WEB_UI_ONLY"
    )

    assert instructions["powershell_write_allowed"] is False

    assert (
        instructions["powershell_remote_github_api_write_allowed"]
        is False
    )

    assert instructions["local_preflight_is_diagnostic_only"] is True


# ===========================================================================
# FAILURE-TO-START CONTRACT
# ===========================================================================

def test_new_session_workflow_requires_lane_and_live_state():
    combined = "\n".join(
        (
            *entrypoint.NEW_SESSION_WORKFLOW,
            *entrypoint.NEW_SESSION_READ_ORDER,
        )
    ).lower()

    assert "backend" in combined

    assert "frontend" in combined

    assert "shared_integration" in combined

    assert "live github" in combined

    assert "state.json" in combined

    assert "t07" in combined

    assert "t14" in combined


def test_entrypoint_does_not_claim_it_fetches_live_github_or_authorizes_tasks():
    doc = entrypoint.startup_instructions()

    assert doc["live_github_refresh_required"] is True

    assert doc["plan_documents_authorize_tasks"] is False

    assert doc["canonical_state_refresh_required"] is True


# ===========================================================================
# SESSION EFFICIENCY AND ORIGINAL OWNER REUSE REGRESSION
# ===========================================================================

def test_repository_paths_preserve_original_and_add_existing_acrl_owners():
    paths = entrypoint.repository_paths()

    required = (
        "t03",
        "t07",
        "t08",
        "t09",
        "t12",
        "t14",
        "t14_full_regression",
        "t15",
        "t16",
        "t17",
        "t18",
        "t19",
        "t20",
        "t21",
        "t22",
        "t23",
        "t24",
        "t25",
        "t26",
        "t27",
        "t28",
        "t29",
        "t30",
    )

    for key in required:
        assert key in paths
        assert paths[key]


def test_document_registry_keeps_distinct_acrl_owners():
    registry = entrypoint.DOCUMENT_REGISTRY

    expected_owners = {
        "acrl_t07": "T07_New_Chat_Bootstrap",
        "acrl_t14": "T14_Repository_Intelligence_Context",
        "acrl_t16": "T16_Repository_Intelligence_File_Discovery",
        "acrl_t17": "T17_Change_Impact_Dependency_Analysis",
        "acrl_t19": "T19_Intelligent_Test_Selection_Failure_Diagnosis",
        "acrl_t23": "T23_Reference_Evidence_Resolution_Engine",
        "acrl_t25": "T25_Context_Token_Work_Budget_Manager",
        "acrl_t26": "T26_Autonomous_Execution_Loop_Controller",
        "acrl_t27": "T27_Dependency_Aware_Work_Scheduler",
        "acrl_t28": "T28_Conflict_Resolution_Reconciliation_Engine",
        "acrl_t29": "T29_Human_Decision_Boundary_Controller",
        "acrl_t30": "T30_Autonomous_Completion_Handoff_Engine",
    }

    for key, expected_path_fragment in expected_owners.items():
        assert key in registry
        assert expected_path_fragment in registry[key]["path"]


def test_acrl_owner_routing_does_not_create_new_execution_authority():
    routing = entrypoint.ACRL_OWNER_ROUTING

    assert routing["bootstrap"] == "acrl_t07"

    assert routing["resume_and_repository_context"] == "acrl_t14"

    assert routing["repository_discovery_and_snapshot"] == "acrl_t16"

    assert routing["change_impact_and_dependencies"] == "acrl_t17"

    assert routing["test_selection_and_failure_diagnosis"] == "acrl_t19"

    assert routing["evidence_identity_and_resolution"] == "acrl_t23"

    assert routing["context_token_and_work_budget"] == "acrl_t25"

    assert routing["completion_proof_and_handoff"] == "acrl_t30"


def test_session_efficiency_rules_preserve_authority_while_reusing_evidence():
    rules = "\n".join(
        entrypoint.SESSION_EFFICIENCY_RULES
    ).lower()

    assert "reuse-first" in rules

    assert "state.json" in rules

    assert "t14" in rules

    assert "t16 one-snapshot rule" in rules

    assert "t17 impact rule" in rules

    assert "t23 evidence rule" in rules

    assert "t19 test selection" in rules

    assert "never trade required verification" in rules


def test_t14_resume_decisions_are_explicit_and_fail_closed():
    assert set(entrypoint.T14_RESUME_DECISIONS) == {
        "FAST_RESUME",
        "TARGETED_REAUDIT",
        "FULL_AUDIT_REQUIRED",
        "INVALID_MANIFEST",
    }

    rules = "\n".join(
        entrypoint.T14_RESUME_RULES
    ).lower()

    assert "state.json" in rules

    assert "head" in rules

    assert "working-tree" in rules

    assert "deleted paths" in rules

    assert "do not manually" in rules

    assert "live state.json execution position" in rules


def test_t14_resume_policy_does_not_allow_manual_cache_sealing():
    rules = "\n".join(
        (
            *entrypoint.T14_RESUME_RULES,
            *entrypoint.FAILURE_RULES,
        )
    ).lower()

    assert "do not mark it sealed manually" in rules

    assert "only the existing ci cache-generation process" in rules


def test_research_reuse_uses_existing_t14_and_t23_owners():
    rules = "\n".join(
        entrypoint.RESEARCH_REUSE_RULES
    ).lower()

    assert "no new research" in rules

    assert "t14" in rules

    assert "t23" in rules

    assert "evidence identity" in rules

    assert "retrieval timestamp" in rules

    assert "do not invent" in rules


def test_session_policy_does_not_create_a_second_research_registry():
    combined = "\n".join(
        (
            *entrypoint.SESSION_EFFICIENCY_RULES,
            *entrypoint.RESEARCH_REUSE_RULES,
        )
    ).lower()

    assert "do not add another research" in combined

    assert (
        entrypoint.DOCUMENT_REGISTRY["acrl_t14"]["authority"]
        == "DERIVED_CONTEXT_ONLY"
    )

    assert (
        entrypoint.DOCUMENT_REGISTRY["acrl_t23"]["authority"]
        == "EVIDENCE_BOUNDARY"
    )


def test_ci_failure_deduplication_uses_exact_run_and_failure_identity():
    rules = "\n".join(
        entrypoint.CI_FAILURE_DEDUPLICATION_RULES
    ).lower()

    for item in (
        "repository",
        "branch",
        "workflow",
        "run id",
        "attempt",
        "tested head_sha",
        "job name",
        "failed step",
        "normalized error signature",
    ):
        assert item in rules


def test_context_budget_rules_do_not_claim_or_increase_model_capacity():
    rules = "\n".join(
        entrypoint.CONTEXT_BUDGET_RULES
    ).lower()

    assert "t25" in rules

    assert "do not claim knowledge" in rules

    assert "increase budgets implicitly" in rules

    assert "required technical requirements" in rules


def test_t26_to_t30_keep_distinct_non_execution_boundaries():
    combined = "\n".join(
        (
            entrypoint.DOCUMENT_REGISTRY["acrl_t26"]["role"],
            entrypoint.DOCUMENT_REGISTRY["acrl_t27"]["role"],
            entrypoint.DOCUMENT_REGISTRY["acrl_t28"]["role"],
            entrypoint.DOCUMENT_REGISTRY["acrl_t29"]["role"],
            entrypoint.DOCUMENT_REGISTRY["acrl_t30"]["role"],
            *entrypoint.SESSION_EFFICIENCY_RULES,
        )
    ).lower()

    assert "does not execute commands" in combined

    assert "does not execute scheduled work" in combined

    assert "human decision" in combined

    assert "human approval" in combined

    assert "completion" in combined


def test_startup_instructions_expose_complete_efficiency_policy():
    instructions = entrypoint.startup_instructions()

    assert "acrl_owner_routing" in instructions

    assert "session_efficiency_rules" in instructions

    assert "t14_resume_decisions" in instructions

    assert "t14_resume_rules" in instructions

    assert "research_reuse_rules" in instructions

    assert "ci_failure_deduplication_rules" in instructions

    assert "context_budget_rules" in instructions

    assert instructions["t14_manifest_is_non_authoritative"] is True

    assert instructions["t16_one_snapshot_per_investigation_batch"] is True

    assert instructions["t23_resolves_supplied_evidence_not_general_search"] is True

    assert instructions["t19_analysis_is_read_only"] is True

    assert instructions["t25_budget_manager_is_not_execution_authority"] is True

    assert instructions["t26_loop_control_is_not_execution_authority"] is True

    assert instructions["t27_scheduler_is_not_execution_authority"] is True

    assert instructions["t28_reconciliation_cannot_bypass_human_boundary"] is True

    assert instructions["t29_human_approval_cannot_be_inferred"] is True

    assert instructions["t30_completion_requires_proof_quorum"] is True


def test_new_session_workflow_uses_resume_before_broad_reaudit():
    workflow = "\n".join(
        entrypoint.NEW_SESSION_WORKFLOW
    ).lower()

    assert workflow.index("retrieve the exact current external t14 artifact") < (
        workflow.index("inspect exact target files")
    )

    assert "fast_resume" in workflow

    assert "targeted_reaudit" in workflow

    assert "full_audit_required" in workflow

    assert "one repository snapshot per investigation batch" in workflow

    assert "resolve exact evidence identities" in workflow


def test_failure_rules_block_redundant_ci_diagnosis_but_allow_new_failures():
    rules = "\n".join(
        entrypoint.FAILURE_RULES
    ).lower()

    assert "same tested sha" in rules

    assert "normalized error signature" in rules

    assert "fresh root-cause analysis" in rules


def test_entrypoint_contract_test_is_part_of_existing_acrl_runtime_script():
    assert ACRL_RUNTIME_RESUME_SCRIPT.is_file()

    content = ACRL_RUNTIME_RESUME_SCRIPT.read_text(
        encoding="utf-8"
    )

    assert (
        "tets/test_ai_agent_entrypoint_contract.py"
        in content
    )

    assert "AUTONOMY_ENGINE/continuity/acrl/runtime_integration" in content

    assert "test_audit_resume_manifest.py" in content

    assert "test_repository_context.py" in content

    assert "test_fast_resume_and_stale_manifest.py" in content

    assert "test_new_chat_bootstrap.py" in content

    assert "test_checkpoint_state_coherence.py" in content

    assert "test_audit_resume_manifest_cache.py" in content


def test_entrypoint_does_not_claim_live_github_fetch_or_task_authorization():
    instructions = entrypoint.startup_instructions()

    assert instructions["live_github_refresh_required"] is True

    assert instructions["canonical_state_refresh_required"] is True

    assert instructions["plan_documents_authorize_tasks"] is False

    assert instructions["engineering_skill_execution_is_project_authority"] is False
