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

    assert "not current" in snapshot["continuity_state_warning"].lower()

    assert "historical evidence" in snapshot["latest_actions_warning"].lower()


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
