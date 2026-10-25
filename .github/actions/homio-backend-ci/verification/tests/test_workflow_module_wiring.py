from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTIONS = ROOT / ".github" / "actions" / "homio-backend-ci"
FINANCIAL = (
    ROOT
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial"
)


def read(path: Path) -> str:
    assert path.is_file(), (
        f"Required CI module is missing: {path.relative_to(ROOT)}"
    )
    return path.read_text(encoding="utf-8")


def test_orchestrator_calls_verification_and_t06_t07_t08_t09_transitions():
    main = read(WORKFLOWS / "backend-ci.yml")
    assert "uses: ./.github/workflows/reusable-backend-verification.yml" in main

    for task in ("t06", "t07", "t08", "t09"):
        assert (
            f"uses: ./.github/workflows/reusable-core008-{task}-transition.yml"
            in main
        )
        assert (
            f"[CONTROL-CENTER-COMPLETE-CORE-008-{task.upper()}]"
            in main
        )

    assert "needs: verification" in main
    assert "  control_center_transition:" not in main
    assert "  control_center_transition_t05:" not in main


def test_all_reusable_workflows_are_in_push_and_pr_trigger_filters():
    main = read(WORKFLOWS / "backend-ci.yml")

    for path in (
        '".github/workflows/backend-ci.yml"',
        '".github/workflows/reusable-backend-verification.yml"',
        '".github/workflows/reusable-core008-t06-transition.yml"',
        '".github/workflows/reusable-core008-t07-transition.yml"',
        '".github/workflows/reusable-core008-t08-transition.yml"',
        '".github/workflows/reusable-core008-t09-transition.yml"',
        '".github/actions/homio-backend-ci/**"',
    ):
        assert main.count(path) == 2, (
            f"Missing push/PR trigger path: {path}"
        )


def test_reusable_workflows_are_declared_with_workflow_call():
    for filename in (
        "reusable-backend-verification.yml",
        "reusable-core008-t06-transition.yml",
        "reusable-core008-t07-transition.yml",
        "reusable-core008-t08-transition.yml",
        "reusable-core008-t09-transition.yml",
    ):
        assert "workflow_call:" in read(WORKFLOWS / filename)


def test_verification_workflow_invokes_owned_verification_action():
    content = read(WORKFLOWS / "reusable-backend-verification.yml")
    assert (
        "uses: ./.github/actions/homio-backend-ci/verification"
    ) in content


def test_verification_action_references_existing_scripts():
    action = read(ACTIONS / "verification" / "action.yml")

    scripts = (
        "wiring_tests.sh",
        "compile_and_contracts.sh",
        "acrl_runtime_resume.sh",
        "acrl_security_git_evidence.sh",
        "financial_context_tenant.sh",
        "acrl_full_suite.sh",
    )

    for script in scripts:
        assert script in action
        assert (
            ACTIONS / "verification" / "scripts" / script
        ).is_file()


def test_t06_reusable_and_composite_actions_are_connected():
    content = read(WORKFLOWS / "reusable-core008-t06-transition.yml")
    assert (
        "uses: ./.github/actions/homio-backend-ci/transitions/core008-t06"
    ) in content

    action = read(ACTIONS / "transitions/core008-t06" / "action.yml")

    for script in (
        "preflight.py",
        "run_regressions.sh",
        "complete_and_evidence.py",
        "publish_and_readback.sh",
    ):
        assert script in action
        assert (
            ACTIONS / "transitions/core008-t06" / "scripts" / script
        ).is_file()


def test_t07_reusable_and_composite_actions_are_connected():
    content = read(WORKFLOWS / "reusable-core008-t07-transition.yml")
    assert (
        "uses: ./.github/actions/homio-backend-ci/transitions/core008-t07"
    ) in content

    action = read(ACTIONS / "transitions/core008-t07" / "action.yml")
    assert "guarded_transition.py" in action
    assert (
        ACTIONS / "transitions/core008-t07" / "scripts" / "guarded_transition.py"
    ).is_file()


def test_t08_reusable_and_composite_actions_are_connected():
    content = read(WORKFLOWS / "reusable-core008-t08-transition.yml")
    assert (
        "uses: ./.github/actions/homio-backend-ci/transitions/core008-t08"
    ) in content

    action = read(ACTIONS / "transitions/core008-t08" / "action.yml")
    assert "guarded_transition.py" in action
    assert (
        ACTIONS / "transitions/core008-t08" / "scripts" / "guarded_transition.py"
    ).is_file()


def test_t09_reusable_and_composite_actions_are_connected():
    content = read(WORKFLOWS / "reusable-core008-t09-transition.yml")
    assert (
        "uses: ./.github/actions/homio-backend-ci/transitions/core008-t09"
    ) in content

    action = read(ACTIONS / "transitions/core008-t09" / "action.yml")
    assert "guarded_transition.py" in action
    assert (
        ACTIONS / "transitions/core008-t09" / "scripts" / "guarded_transition.py"
    ).is_file()


def test_shared_transition_contract_remains_canonical():
    shared = read(ACTIONS / "shared" / "transition_contract.py")
    assert "require_core008_criteria_baseline" in shared

    t06_preflight = read(
        ACTIONS / "transitions/core008-t06/scripts/preflight.py"
    )
    t06_complete = read(
        ACTIONS / "transitions/core008-t06/scripts/complete_and_evidence.py"
    )
    t07_script = read(
        ACTIONS / "transitions/core008-t07/scripts/guarded_transition.py"
    )
    t08_script = read(
        ACTIONS / "transitions/core008-t08/scripts/guarded_transition.py"
    )
    t09_script = read(
        ACTIONS / "transitions/core008-t09/scripts/guarded_transition.py"
    )

    assert "from transition_contract import" in t06_preflight
    assert "from transition_contract import" in t06_complete

    for script in (t07_script, t08_script, t09_script):
        assert "require_core008_criteria_baseline" in script


def test_t06_completion_uses_controller_not_manual_state_edit():
    complete = read(
        ACTIONS / "transitions/core008-t06/scripts/complete_and_evidence.py"
    )

    assert '"complete-subtask"' in complete
    assert '"CORE-008-T06"' in complete
    assert "STATE_PATH.write_text" not in complete


def test_t06_publisher_has_allowlist_and_readback_guards():
    publish = read(
        ACTIONS / "transitions/core008-t06/scripts/publish_and_readback.sh"
    )

    assert "EXPECTED_TRACKED" in publish
    assert "git push origin HEAD:refs/heads/reos-development" in publish
    assert "--force" not in publish
    assert "CANONICAL READBACK PASS" in publish


def test_t07_completion_uses_controller_and_preserves_pending_criteria():
    script = read(
        ACTIONS / "transitions/core008-t07/scripts/guarded_transition.py"
    )

    assert '"complete-subtask"' in script
    assert '"CORE-008-T07"' in script
    assert "require_core008_criteria_baseline" in script
    assert "T07 TRANSITION AND CANONICAL READBACK: PASS" in script
    assert "STATE.write_text" not in script
    assert "--force" not in script


def test_t08_precision_concurrency_suite_reuses_existing_test_files():
    script = read(
        ACTIONS / "transitions/core008-t08/scripts/guarded_transition.py"
    )

    for name in (
        "test_core008_t01_financial_domain.py",
        "test_core008_t01_financial_ledger_boundary.py",
        "test_core008_t03_allocation_participants.py",
        "test_core008_t04_optimistic_concurrency.py",
        "test_core008_t04_reconciliation_replay.py",
        "test_core008_t13_concurrency_security_reos.py",
        "test_core008_t13_financial_regression.py",
    ):
        assert name in script
        assert (FINANCIAL / name).is_file()


def test_t08_completion_uses_controller_and_preserves_pending_criteria():
    script = read(
        ACTIONS / "transitions/core008-t08/scripts/guarded_transition.py"
    )

    assert '"complete-subtask"' in script
    assert '"CORE-008-T08"' in script
    assert "require_core008_criteria_baseline" in script
    assert "T08 TRANSITION AND CANONICAL READBACK: PASS" in script
    assert "STATE.write_text" not in script
    assert "STATE_PATH.write_text" not in script
    assert "--force" not in script

    for criterion in (
        "CORE-008-AC01",
        "CORE-008-AC04",
        "CORE-008-AC05",
        "CORE-008-AC06",
    ):
        assert criterion in script


def test_t08_transition_requires_exact_control_center_commit_prefix():
    main = read(WORKFLOWS / "backend-ci.yml")
    reusable = read(WORKFLOWS / "reusable-core008-t08-transition.yml")

    expected_guard = (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        "startsWith(github.event.head_commit.message, "
        "'[CONTROL-CENTER-COMPLETE-CORE-008-T08]') }}"
    )

    assert expected_guard in main
    assert expected_guard in reusable


def test_t09_completion_uses_controller_and_preserves_pending_criteria():
    script = read(
        ACTIONS / "transitions/core008-t09/scripts/guarded_transition.py"
    )

    assert '"complete-subtask"' in script
    assert '"CORE-008-T09"' in script
    assert 'os.environ["GITHUB_ACTOR"] != "prajaktaranjane80-sketch"' in script
    assert 'os.environ["GITHUB_REF"] != "refs/heads/reos-development"' in script
    assert 'os.environ["EXPECTED_SHA"] != os.environ["VERIFIED_CODE_SHA"]' in script
    assert "require_core008_criteria_baseline" in script
    assert "T09 TRANSITION AND CANONICAL READBACK: PASS" in script
    assert "STATE.write_text" not in script
    assert "STATE_PATH.write_text" not in script
    assert "--force" not in script

    for criterion in (
        "CORE-008-AC01",
        "CORE-008-AC04",
        "CORE-008-AC05",
        "CORE-008-AC06",
    ):
        assert criterion in script


def test_t09_transition_requires_exact_control_center_commit_prefix():
    main = read(WORKFLOWS / "backend-ci.yml")
    reusable = read(WORKFLOWS / "reusable-core008-t09-transition.yml")

    expected_guard = (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        "startsWith(github.event.head_commit.message, "
        "'[CONTROL-CENTER-COMPLETE-CORE-008-T09]') }}"
    )

    assert expected_guard in main
    assert expected_guard in reusable
