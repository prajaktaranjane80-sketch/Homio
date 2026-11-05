import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]

BACKEND_WORKFLOW = (
    ROOT / ".github/workflows/backend-ci.yml"
)

REUSABLE_WORKFLOW = (
    ROOT / ".github/workflows/reusable-backend-b1-completion.yml"
)

TRANSITION_ACTION = (
    ROOT
    / ".github/actions/homio-backend-ci/transitions/"
    "backend-b1-completion/action.yml"
)

TRANSITION_SCRIPT = (
    ROOT
    / ".github/actions/homio-backend-ci/transitions/"
    "backend-b1-completion/scripts/guarded_transition.py"
)

VERIFICATION_ACTION = (
    ROOT
    / ".github/actions/homio-backend-ci/verification/action.yml"
)

OWNER_REQUEST = (
    ROOT
    / "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B1-completion-request.md"
)


def read_required(path: Path) -> str:
    assert path.is_file(), (
        f"Required B1 completion file is missing: {path}"
    )
    return path.read_text(encoding="utf-8")


def git_command_prefixes(source: str) -> set[tuple[str, ...]]:
    """Inspect actual Git command argument vectors passed to run()."""
    tree = ast.parse(source)
    prefixes: set[tuple[str, ...]] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Name):
            continue

        if node.func.id != "run" or not node.args:
            continue

        command = node.args[0]

        if not isinstance(command, ast.List):
            continue

        values: list[str] = []

        for item in command.elts:
            if (
                not isinstance(item, ast.Constant)
                or not isinstance(item.value, str)
            ):
                break

            values.append(item.value)

        if len(values) >= 2 and values[0] == "git":
            prefixes.add((values[0], values[1]))

    return prefixes


def test_backend_ci_has_exact_owner_guarded_b1_completion():
    workflow = read_required(BACKEND_WORKFLOW)

    reusable_path = (
        '".github/workflows/'
        'reusable-backend-b1-completion.yml"'
    )

    assert workflow.count(reusable_path) == 2

    guard = (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        "startsWith(github.event.head_commit.message, "
        "'[CONTROL-CENTER-COMPLETE-BACKEND-001-B1]') }}"
    )

    assert guard in workflow
    assert "control_center_complete_backend_b1:" in workflow
    assert "needs: verification" in workflow
    assert (
        "uses: ./.github/workflows/"
        "reusable-backend-b1-completion.yml"
    ) in workflow


def test_reusable_workflow_checks_out_exact_verified_commit():
    workflow = read_required(REUSABLE_WORKFLOW)

    required = (
        "workflow_call:",
        "Owner-authorized BACKEND-001-B1 completion",
        "contents: write",
        "EXPECTED_SHA: ${{ github.sha }}",
        "VERIFIED_CODE_SHA: ${{ github.sha }}",
        "ACTIONS_RUN_ID: ${{ github.run_id }}",
        "fetch-depth: 0",
        "persist-credentials: true",
        'node-version: "24"',
        "qdrant-client==1.20.0",
        (
            "uses: ./.github/actions/homio-backend-ci/"
            "transitions/backend-b1-completion"
        ),
    )

    for value in required:
        assert value in workflow


def test_transition_uses_existing_control_center_and_remote_readback():
    script = read_required(TRANSITION_SCRIPT)

    required = (
        "BACKEND-001-B1",
        "BACKEND-001-B2",
        "complete-subtask",
        "controller.main()",
        "verify-state",
        "validate_state(",
        "assert_exact_branch(",
        "CANONICAL_BRANCH_HEAD",
        "BACKEND-001-AC01",
        "BACKEND-001-AC10",
        "APPROVAL: AUTHORIZE BACKEND-001-B1 COMPLETION",
        "SCOPE: BACKEND-001-B1 only",
    )

    for value in required:
        assert value in script

    # Verify actual Git command argument vectors, not source-code wording.
    commands = git_command_prefixes(script)

    assert ("git", "push") in commands
    assert ("git", "fetch") in commands

    # Canonical state must be changed through the Control Center only.
    assert "STATE.write_text(" not in script
    assert "json.dump(" not in script


def test_transition_action_invokes_the_guarded_script():
    action = read_required(TRANSITION_ACTION)

    assert "using: composite" in action
    assert "guarded_transition.py" in action


def test_verification_runs_the_b1_completion_contract_test():
    action = read_required(VERIFICATION_ACTION)

    assert (
        "test_backend_b1_completion_transition.py"
        in action
    )


def test_owner_request_is_explicitly_scoped_to_b1():
    request = read_required(OWNER_REQUEST)

    assert (
        "APPROVAL: AUTHORIZE BACKEND-001-B1 COMPLETION"
        in request
    )

    assert "SCOPE: BACKEND-001-B1 only" in request
    assert "BACKEND-001-AC01 through BACKEND-001-AC10" in request
