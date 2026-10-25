from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTIONS = ROOT / ".github" / "actions" / "homio-backend-ci"


def read(path: Path) -> str:
    assert path.is_file(), (
        f"Required CI module is missing: {path.relative_to(ROOT)}"
    )
    return path.read_text(encoding="utf-8")


def test_orchestrator_calls_verified_workflows_and_has_t06_gate():
    main = read(WORKFLOWS / "backend-ci.yml")
    assert "uses: ./.github/workflows/reusable-backend-verification.yml" in main
    assert "uses: ./.github/workflows/reusable-core008-t06-transition.yml" in main
    assert "needs: verification" in main
    assert "[CONTROL-CENTER-COMPLETE-CORE-008-T06]" in main
    assert "  control_center_transition:" not in main
    assert "  control_center_transition_t05:" not in main


def test_all_reusable_workflows_and_actions_are_in_trigger_filters():
    main = read(WORKFLOWS / "backend-ci.yml")
    for path in (
        '".github/workflows/backend-ci.yml"',
        '".github/workflows/reusable-backend-verification.yml"',
        '".github/workflows/reusable-core008-t06-transition.yml"',
        '".github/actions/homio-backend-ci/**"',
    ):
        assert main.count(path) == 2, (
            f"Missing push/PR trigger path: {path}"
        )


def test_reusable_workflows_are_declared_with_workflow_call():
    for filename in (
        "reusable-backend-verification.yml",
        "reusable-core008-t06-transition.yml",
    ):
        content = read(WORKFLOWS / filename)
        assert "workflow_call:" in content


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


def test_t06_reusable_workflow_calls_owned_composite_action():
    content = read(WORKFLOWS / "reusable-core008-t06-transition.yml")
    assert (
        "uses: ./.github/actions/homio-backend-ci/transitions/core008-t06"
    ) in content
    assert "workflow_call:" in content


def test_t06_composite_action_references_existing_scripts():
    action = read(
        ACTIONS / "transitions" / "core008-t06" / "action.yml"
    )
    scripts = (
        "preflight.py",
        "run_regressions.sh",
        "complete_and_evidence.py",
        "publish_and_readback.sh",
    )
    for script in scripts:
        assert script in action
        assert (
            ACTIONS / "transitions" / "core008-t06"
            / "scripts" / script
        ).is_file()


def test_shared_transition_contract_is_in_one_canonical_location():
    shared = read(ACTIONS / "shared" / "transition_contract.py")
    preflight = read(
        ACTIONS / "transitions" / "core008-t06"
        / "scripts" / "preflight.py"
    )
    complete = read(
        ACTIONS / "transitions" / "core008-t06"
        / "scripts" / "complete_and_evidence.py"
    )
    assert "require_core008_criteria_baseline" in shared
    assert "from transition_contract import" in preflight
    assert "from transition_contract import" in complete


def test_t06_completion_uses_controller_not_manual_state_edit():
    complete = read(
        ACTIONS / "transitions" / "core008-t06"
        / "scripts" / "complete_and_evidence.py"
    )
    assert '"complete-subtask"' in complete
    assert '"CORE-008-T06"' in complete
    assert "STATE_PATH.write_text" not in complete
    assert "state.json` directly" not in complete


def test_t06_publish_has_allowlist_and_no_force_push():
    publish = read(
        ACTIONS / "transitions" / "core008-t06"
        / "scripts" / "publish_and_readback.sh"
    )
    assert "EXPECTED_TRACKED" in publish
    assert "git push origin HEAD:refs/heads/reos-development" in publish
    assert "--force" not in publish
    assert "CANONICAL READBACK PASS" in publish
