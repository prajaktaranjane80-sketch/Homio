#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()
actions = root / ".github/actions/homio-backend-ci"
workflows = root / ".github/workflows"
control = root / "REOS_CONTROL_CENTER"

t17_root = (
    control
    / "AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis"
)


def require_file(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(
            f"Required file is missing: {path.relative_to(root)}"
        )
    return path.read_text(encoding="utf-8")


def require_contains(
    label: str,
    content: str,
    values: tuple[str, ...],
):
    for value in values:
        if value not in content:
            raise SystemExit(
                f"{label} is missing required contract: {value}"
            )


def parse_python(path: Path) -> ast.Module:
    try:
        return ast.parse(
            require_file(path),
            filename=str(path),
        )
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise SystemExit(
            f"Invalid Python in {path.relative_to(root)}: {exc}"
        ) from exc


transition_scripts = {
    "AI-001-T01": actions / "transitions/ai001-t01/scripts/guarded_transition.py",
    "T06": actions / "transitions/core008-t06/scripts/complete_and_evidence.py",
    "T07": actions / "transitions/core008-t07/scripts/guarded_transition.py",
    "T08": actions / "transitions/core008-t08/scripts/guarded_transition.py",
    "T09": actions / "transitions/core008-t09/scripts/guarded_transition.py",
}

transition_actions = {
    "AI-001-T01": actions / "transitions/ai001-t01/action.yml",
    "T06": actions / "transitions/core008-t06/action.yml",
    "T07": actions / "transitions/core008-t07/action.yml",
    "T08": actions / "transitions/core008-t08/action.yml",
    "T09": actions / "transitions/core008-t09/action.yml",
}

transition_workflows = {
    "AI-001-T01": workflows / "reusable-ai001-t01-transition.yml",
    "T06": workflows / "reusable-core008-t06-transition.yml",
    "T07": workflows / "reusable-core008-t07-transition.yml",
    "T08": workflows / "reusable-core008-t08-transition.yml",
    "T09": workflows / "reusable-core008-t09-transition.yml",
}

backend_path = workflows / "backend-ci.yml"

activation_workflow_path = (
    workflows / "reusable-backend-workstream-activation.yml"
)

activation_action_path = (
    actions / "transitions/backend-workstream-activation/action.yml"
)

activation_script_path = (
    actions
    / "transitions/backend-workstream-activation/scripts/"
    / "activate_backend_workstream.py"
)

activation_wrapper_path = (
    actions
    / "transitions/backend-workstream-activation/scripts/"
    / "activate_backend_workstream_wrapper.py"
)

identity_contract_path = control / "context/github_actions_identity.py"
identity_test_path = control / "context/test_github_actions_identity.py"
controller_test_path = control / "context/test_backend_control_projection.py"

bootstrap_test_path = (
    control / "context/test_backend_activation_import_bootstrap.py"
)

backend_transition_test_path = (
    control / "context/test_backend_workstream_transition.py"
)

phase_projection_path = control / "context/phase_projection.py"
phase_projection_test_path = control / "context/test_phase_projection.py"
backend_transition_path = control / "context/backend_workstream_transition.py"
controller_path = control / "reos_control_center.py"

impact_analysis_path = (
    t17_root / "change_impact_analysis.py"
)

impact_analysis_test_path = (
    t17_root / "test_change_impact_analysis.py"
)

t06_publish = (
    actions / "transitions/core008-t06/scripts/publish_and_readback.sh"
)

financial_runner_path = (
    actions / "verification/scripts/financial_context_tenant.sh"
)

shared_contract_path = actions / "shared/transition_contract.py"


# ---------------------------------------------------------------------------
# Required-file and Python-syntax inventory.
# ---------------------------------------------------------------------------

required_paths = (
    *transition_scripts.values(),
    *transition_actions.values(),
    *transition_workflows.values(),
    backend_path,
    activation_workflow_path,
    activation_action_path,
    activation_script_path,
    activation_wrapper_path,
    identity_contract_path,
    identity_test_path,
    controller_test_path,
    bootstrap_test_path,
    backend_transition_test_path,
    phase_projection_path,
    phase_projection_test_path,
    backend_transition_path,
    controller_path,
    impact_analysis_path,
    impact_analysis_test_path,
    t06_publish,
    financial_runner_path,
    shared_contract_path,
)

for path in required_paths:
    require_file(path)

parsed_scripts = {
    task: parse_python(path)
    for task, path in transition_scripts.items()
}

for path in (
    identity_contract_path,
    identity_test_path,
    controller_test_path,
    bootstrap_test_path,
    activation_script_path,
    activation_wrapper_path,
    backend_transition_path,
    controller_path,
    phase_projection_path,
    phase_projection_test_path,
    backend_transition_test_path,
    impact_analysis_path,
    impact_analysis_test_path,
):
    parse_python(path)

backend = require_file(backend_path)
shared = require_file(shared_contract_path)
t06_publish_text = require_file(t06_publish)
activation_workflow = require_file(activation_workflow_path)
activation_action = require_file(activation_action_path)
activation_script = require_file(activation_script_path)
activation_wrapper = require_file(activation_wrapper_path)

identity_contract = require_file(identity_contract_path)
identity_test = require_file(identity_test_path)
controller_test = require_file(controller_test_path)
bootstrap_test = require_file(bootstrap_test_path)
impact_analysis = require_file(impact_analysis_path)
impact_analysis_test = require_file(impact_analysis_test_path)
financial_runner = require_file(financial_runner_path)


# ---------------------------------------------------------------------------
# Backend CI triggers and required-check behavior.
# ---------------------------------------------------------------------------

if ".github/actions/homio-backend-ci/**" not in backend:
    raise SystemExit(
        "Backend CI path filters omit the owned action directory."
    )

push_trigger = backend.split("\n  pull_request:", 1)[0]

if '"REOS_CONTROL_CENTER/backend/**"' not in push_trigger:
    raise SystemExit(
        "Backend CI push paths omit the canonical Fastify backend root."
    )

if '"REOS_CONTROL_CENTER/Frontend/**"' in push_trigger:
    raise SystemExit(
        "Backend CI must not couple frontend-only changes to backend CI."
    )

if "\njobs:" not in backend:
    raise SystemExit("Backend CI jobs section is missing.")

workflow_triggers = backend.split("\njobs:", 1)[0]

if "\n  pull_request:" not in workflow_triggers:
    raise SystemExit(
        "Backend CI required pull-request trigger is missing."
    )

pull_request_trigger = workflow_triggers.split(
    "\n  pull_request:", 1
)[1]

if '"**"' not in pull_request_trigger:
    raise SystemExit(
        "Backend CI must retain the all-PR required-check safety path."
    )


# ---------------------------------------------------------------------------
# BACKEND-001 exact owner-approved trigger.
# ---------------------------------------------------------------------------

backend_activation_guard = (
    "if: ${{ github.event_name == 'push' && "
    "github.ref == 'refs/heads/reos-development' && "
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-ACTIVATE-BACKEND-001]') }}"
)

require_contains(
    "BACKEND-001 backend workflow",
    backend,
    (backend_activation_guard,),
)

if backend.count(
    '".github/workflows/reusable-backend-workstream-activation.yml"'
) != 2:
    raise SystemExit(
        "BACKEND-001 reusable workflow must remain in push and PR path filters."
    )

require_contains(
    "BACKEND-001 reusable workflow",
    activation_workflow,
    (
        "workflow_call:",
        "Owner-authorized BACKEND-001 activation",
        "contents: write",
        "id-token: write",
        "EXPECTED_SHA: ${{ github.sha }}",
        "ACTIONS_RUN_ID: ${{ github.run_id }}",
        "ACTIONS_REPOSITORY: ${{ github.repository }}",
        (
            "uses: ./.github/actions/homio-backend-ci/"
            "transitions/backend-workstream-activation"
        ),
    ),
)

require_contains(
    "BACKEND-001 composite action",
    activation_action,
    ("activate_backend_workstream_wrapper.py",),
)

require_contains(
    "BACKEND-001 activation wrapper",
    activation_wrapper,
    (
        "REPAIRED_ACTIVATION_PATHS",
        "EVIDENCE_ONLY_ACTIVATION_PATHS",
        "source_paths_for_t17",
        "load_guarded_activation",
        "module.EXPECTED_ACTIVATION_PATHS",
        "original_authorize",
        "write_activation_evidence_with_scope_note",
        "REOS_CONTROL_CENTER/PS Output",
    ),
)


# ---------------------------------------------------------------------------
# GitHub immutable OIDC identity contract.
#
# Claim names belong to github_actions_identity.py.
# The activation script imports and invokes that validator.
# ---------------------------------------------------------------------------

require_contains(
    "HOMIO GitHub identity contract",
    identity_contract,
    (
        'OWNER: Final = "prajaktaranjane80-sketch"',
        'REPOSITORY: Final = "prajaktaranjane80-sketch/Homio"',
        'OWNER_ID: Final = "320960487"',
        'REPOSITORY_ID: Final = "1346051793"',
        'BRANCH: Final = "reos-development"',
        "EXPECTED_OIDC_SUBJECT",
        "EXPECTED_GITHUB_ACTIONS_CLAIMS",
        "validate_github_actions_identity_claims",
        "GitHubActionsIdentityError",
        '"iss"',
        '"sub"',
        '"repository"',
        '"repository_owner"',
        '"repository_id"',
        '"repository_owner_id"',
        '"actor"',
        '"actor_id"',
        '"ref"',
        '"ref_type"',
        '"event_name"',
        '"sha"',
    ),
)

require_contains(
    "BACKEND-001 activation OIDC integration",
    activation_script,
    (
        "EXPECTED_OIDC_SUBJECT",
        "OIDC_ISSUER",
        "OWNER_ID",
        "REPOSITORY_ID",
        "GitHubActionsIdentityError",
        "validate_github_actions_identity_claims",
        "principal = self.verifier.verify_access_token(token)",
        "trusted_approver_principals",
        "OIDC: IMMUTABLE OWNER/REPOSITORY IDENTITY VERIFIED",
    ),
)

require_contains(
    "HOMIO identity regression tests",
    identity_test,
    (
        "test_expected_subject_uses_immutable_repository_identity",
        "test_valid_owner_push_identity_is_accepted",
        "test_wrong_identity_claim_is_rejected",
        "test_missing_identity_claim_is_rejected",
        "test_invalid_expected_sha_is_rejected",
        "test_legacy_subject_is_never_accepted",
        "repository_owner_id",
        "repository_id",
        "actor_id",
    ),
)


# ---------------------------------------------------------------------------
# Wrapper-owned exact activation source-path allowlist.
# ---------------------------------------------------------------------------

wrapper_tree = parse_python(activation_wrapper_path)
module_constants: dict[str, object] = {}
allowlist_node: ast.Set | None = None

for node in wrapper_tree.body:
    if not isinstance(node, ast.Assign):
        continue

    if len(node.targets) != 1:
        continue

    target = node.targets[0]
    if not isinstance(target, ast.Name):
        continue

    if target.id == "REPAIRED_ACTIVATION_PATHS":
        if not isinstance(node.value, ast.Set):
            raise SystemExit(
                "REPAIRED_ACTIVATION_PATHS must be a literal set."
            )
        allowlist_node = node.value
        continue

    if isinstance(node.value, ast.Constant):
        module_constants[target.id] = node.value.value

if allowlist_node is None:
    raise SystemExit(
        "Activation wrapper has no REPAIRED_ACTIVATION_PATHS set."
    )

actual_allowlist: set[str] = set()

for item in allowlist_node.elts:
    if isinstance(item, ast.Constant) and isinstance(item.value, str):
        actual_allowlist.add(item.value)

    elif isinstance(item, ast.Name):
        value = module_constants.get(item.id)

        if not isinstance(value, str):
            raise SystemExit(
                "Activation path allowlist contains an unknown constant: "
                f"{item.id}"
            )

        actual_allowlist.add(value)

    else:
        raise SystemExit(
            "Activation path allowlist contains an unsupported expression."
        )

expected_activation_paths = {
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/action.yml",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream.py",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream_wrapper.py",
    ".github/workflows/backend-ci.yml",
    ".github/workflows/reusable-backend-workstream-activation.yml",
    "REOS_CONTROL_CENTER/context/phase_projection.py",
    "REOS_CONTROL_CENTER/context/test_phase_projection.py",
    "REOS_CONTROL_CENTER/context/backend_workstream_transition.py",
    "REOS_CONTROL_CENTER/context/test_backend_workstream_transition.py",
    "REOS_CONTROL_CENTER/context/github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_backend_control_projection.py",
    "REOS_CONTROL_CENTER/evidence/BACKEND-001/"
    "B0-live-repository-audit.md",
    ".github/actions/homio-backend-ci/verification/scripts/"
    "financial_context_tenant.sh",
    ".github/actions/homio-backend-ci/verification/scripts/"
    "wiring_tests.sh",
    "REOS_CONTROL_CENTER/context/"
    "test_backend_activation_import_bootstrap.py",
    "REOS_CONTROL_CENTER/reos_control_center.py",
    "REOS_CONTROL_CENTER/PS Output",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis/test_change_impact_analysis.py",
}

if actual_allowlist != expected_activation_paths:
    missing = sorted(expected_activation_paths - actual_allowlist)
    unexpected = sorted(actual_allowlist - expected_activation_paths)

    raise SystemExit(
        "BACKEND-001 activation path allowlist mismatch; "
        f"missing={missing}; unexpected={unexpected}"
    )

for path in expected_activation_paths:
    if not (root / path).is_file():
        raise SystemExit(
            f"Activation allowlist path is missing from repository: {path}"
        )


# ---------------------------------------------------------------------------
# T17 fail-closed classification and regression checks.
# ---------------------------------------------------------------------------

require_contains(
    "T17 fail-closed analyzer",
    impact_analysis,
    (
        "_has_untrusted_classification",
        "SourceKind.UNKNOWN",
        "FileAuthority.UNKNOWN",
        "FileRisk.UNKNOWN",
        "FileRisk.SENSITIVE",
        "item.is_symlink",
        "ImpactLevel.UNKNOWN",
        "T17Decision.FAIL_CLOSED",
        "T17Decision.BLOCKED",
    ),
)

require_contains(
    "T17 regression tests",
    impact_analysis_test,
    (
        "test_unknown_missing_path_blocks",
        "test_existing_unknown_classification_blocks",
        "test_protected_detected_and_handoff_blocked",
        "report.ready_for_handoff is False",
    ),
)


# ---------------------------------------------------------------------------
# Existing modular regression runner must include every backend regression.
# ---------------------------------------------------------------------------

for test_path in (
    "context/test_phase_projection.py",
    "context/test_backend_workstream_transition.py",
    "context/test_backend_control_projection.py",
    "context/test_github_actions_identity.py",
    "context/test_backend_activation_import_bootstrap.py",
    (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T17_Change_Impact_Dependency_Analysis/"
        "test_change_impact_analysis.py"
    ),
):
    if test_path not in financial_runner:
        raise SystemExit(
            "Existing modular regression runner omits: "
            f"{test_path}"
        )


# ---------------------------------------------------------------------------
# Verify bootstrap test covers the wrapper, identity, exact path and ACRL.
# ---------------------------------------------------------------------------

require_contains(
    "Activation import/bootstrap regression test",
    bootstrap_test,
    (
        "activate_backend_workstream_wrapper.py",
        "REPAIRED_ACTIVATION_PATHS",
        "source_paths_for_t17",
        "EVIDENCE_ONLY_ACTIVATION_PATHS",
        "REOS_CONTROL_CENTER/PS Output",
        "REOS_CONTROL_CENTER/reos_control_center.py",
        "AUTONOMY_ENGINE.continuity.acrl.repository_context",
        "duplicate package namespace",
    ),
)


# ---------------------------------------------------------------------------
# AI-001-T01 guarded transition contract.
# ---------------------------------------------------------------------------

t01_script = require_file(transition_scripts["AI-001-T01"])
t01_workflow = require_file(transition_workflows["AI-001-T01"])
t01_tree = parsed_scripts["AI-001-T01"]

t01_guard = (
    "if: ${{ github.event_name == 'push' && "
    "github.ref == 'refs/heads/reos-development' && "
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-COMPLETE-AI-001-T01]') }}"
)

for name, content in (
    ("AI-001-T01 backend", backend),
    ("AI-001-T01 reusable workflow", t01_workflow),
):
    require_contains(name, content, (t01_guard,))

for binding in (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
):
    require_contains(
        "AI-001-T01 reusable workflow",
        t01_workflow,
        (binding,),
    )

require_contains(
    "AI-001-T01 guarded script",
    t01_script,
    (
        '"AI-001-T01"',
        '"complete-subtask"',
        "APPROVAL: AUTHORIZE AI-001-T01 COMPLETION",
        "SCOPE: AI-001-T01 only",
        "AI-001-AC01",
        "AI-001-AC06",
        "AI-001-T01 TRANSITION AND CANONICAL READBACK: PASS",
        "GITHUB_ACTOR",
        "GITHUB_REF",
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "assert_exact_branch",
        "validate_state",
        "calculate_hash",
        '"git",\n            "push"',
        "CANONICAL_BRANCH_HEAD",
        "refs/heads/reos-development",
        "compile_ai_package_sources",
        "clean_generated_bytecode",
        'os.environ["PYTHONDONTWRITEBYTECODE"] = "1"',
        "sys.dont_write_bytecode = True",
        "AI_PACKAGE_SOURCE_COMPILE_PASS",
        "AI_PACKAGE_BYTECODE_CLEANUP_REMOVED_DIRS",
    ),
)

# Detect actual compileall commands structurally.
for node in ast.walk(t01_tree):
    if not isinstance(node, ast.Call) or not node.args:
        continue

    command_argument = node.args[0]
    if not isinstance(command_argument, (ast.List, ast.Tuple)):
        continue

    command_values = {
        child.value
        for child in ast.walk(command_argument)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
    }

    if "compileall" in command_values:
        raise SystemExit(
            "AI-001-T01 must not execute compileall because it creates "
            "bytecode files."
        )

cleanup_position = t01_script.rfind("clean_generated_bytecode()")
snapshot_position = t01_script.find(
    '["git", "ls-files", "--others", "--exclude-standard"]'
)

if (
    cleanup_position < 0
    or snapshot_position < 0
    or cleanup_position > snapshot_position
):
    raise SystemExit(
        "AI-001-T01 must clean generated bytecode before snapshot inventory."
    )

if "STATE.write_text" in t01_script or "STATE_PATH.write_text" in t01_script:
    raise SystemExit(
        "AI-001-T01 must not edit canonical state outside the controller."
    )

if "--force" in t01_script:
    raise SystemExit("AI-001-T01 transition must never force-push.")

for test_name in (
    "test_contracts.py",
    "test_model_gateway.py",
    "test_public_contract_stability.py",
):
    test_path = (
        root
        / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests"
        / test_name
    )

    if not test_path.is_file():
        raise SystemExit(
            f"Canonical AI package test is missing: {test_path.relative_to(root)}"
        )

    if test_name not in t01_script:
        raise SystemExit(
            f"AI-001-T01 transition omits canonical test: {test_name}"
        )

t01_composite = require_file(transition_actions["AI-001-T01"])

if transition_scripts["AI-001-T01"].name not in t01_composite:
    raise SystemExit(
        "AI-001-T01 composite action does not invoke guarded_transition.py."
    )


# ---------------------------------------------------------------------------
# CORE-008 T06/T07/T08/T09 existing transition guards and SHA bindings.
# ---------------------------------------------------------------------------

for task in ("T06", "T07", "T08", "T09"):
    prefix = f"[CONTROL-CENTER-COMPLETE-CORE-008-{task}]"

    guard = (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        f"startsWith(github.event.head_commit.message, '{prefix}') }}"
    )

    workflow = require_file(transition_workflows[task])

    for name, content in (
        (f"{task} backend workflow", backend),
        (f"{task} reusable workflow", workflow),
    ):
        require_contains(name, content, (guard,))

    for binding in (
        "EXPECTED_SHA: ${{ github.sha }}",
        "VERIFIED_CODE_SHA: ${{ github.sha }}",
        "ACTIONS_RUN_ID: ${{ github.run_id }}",
        "ACTIONS_SERVER_URL: ${{ github.server_url }}",
        "ACTIONS_REPOSITORY: ${{ github.repository }}",
    ):
        require_contains(
            f"{task} reusable workflow",
            workflow,
            (binding,),
        )

    composite = require_file(transition_actions[task])

    if transition_scripts[task].name not in composite:
        raise SystemExit(
            f"{task} composite action does not invoke "
            f"{transition_scripts[task].name}."
        )


# Every reusable workflow must remain in push and PR path filters.
for path in (
    '".github/workflows/backend-ci.yml"',
    '".github/workflows/reusable-backend-verification.yml"',
    '".github/workflows/reusable-ai001-t01-transition.yml"',
    '".github/workflows/reusable-core008-t06-transition.yml"',
    '".github/workflows/reusable-core008-t07-transition.yml"',
    '".github/workflows/reusable-core008-t08-transition.yml"',
    '".github/workflows/reusable-core008-t09-transition.yml"',
):
    if backend.count(path) != 2:
        raise SystemExit(
            f"Workflow push/PR path filter count must be 2: {path}"
        )


# ---------------------------------------------------------------------------
# CORE-008 criteria-preservation and no-force safeguards.
# ---------------------------------------------------------------------------

for task in ("T07", "T08", "T09"):
    script = require_file(transition_scripts[task])

    require_contains(
        f"CORE-008-{task} guarded script",
        script,
        (
            "require_core008_criteria_baseline",
            '"complete-subtask"',
            f'"CORE-008-{task}"',
            "return output.strip()",
            "git",
            "CORE-008-AC01",
            "CORE-008-AC04",
            "CORE-008-AC05",
            "CORE-008-AC06",
            "CANONICAL_BRANCH_HEAD",
        ),
    )

    if "STATE.write_text" in script or "STATE_PATH.write_text" in script:
        raise SystemExit(
            f"{task} must not edit canonical state outside the controller."
        )

    if "--force" in script:
        raise SystemExit(
            f"{task} transition must never force-push."
        )


# Verify existing T08 financial test inventory.
t08_script = require_file(transition_scripts["T08"])

for test_name in (
    "test_core008_t01_financial_domain.py",
    "test_core008_t01_financial_ledger_boundary.py",
    "test_core008_t03_allocation_participants.py",
    "test_core008_t04_optimistic_concurrency.py",
    "test_core008_t04_reconciliation_replay.py",
    "test_core008_t13_concurrency_security_reos.py",
    "test_core008_t13_financial_regression.py",
):
    if test_name not in t08_script:
        raise SystemExit(
            f"T08 does not include expected test file: {test_name}"
        )

    path = (
        root
        / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial"
        / test_name
    )

    if not path.is_file():
        raise SystemExit(
            f"T08 focused test file is missing: {path.relative_to(root)}"
        )


# Verify the existing T09 security test.
t09_script = require_file(transition_scripts["T09"])

t09_test = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial"
    / "test_core008_t09_security_approval_review.py"
)

if "test_core008_t09_security_approval_review.py" not in t09_script:
    raise SystemExit("T09 does not include its focused security test.")

if not t09_test.is_file():
    raise SystemExit(
        f"T09 focused test is missing: {t09_test.relative_to(root)}"
    )

require_contains(
    "Shared transition contract",
    shared,
    ("require_core008_criteria_baseline",),
)

require_contains(
    "CORE-008-T06 publisher",
    t06_publish_text,
    (
        "EXPECTED_TRACKED",
        "git push origin HEAD:refs/heads/reos-development",
        "CANONICAL READBACK PASS",
    ),
)

if "--force" in t06_publish_text:
    raise SystemExit("T06 publisher must never force-push.")


print(
    "Transition wiring PASS: AI-001-T01 bytecode-safe compilation and "
    "cleanup, AI-001-T01 and CORE-008 T06/T07/T08/T09 authorization guards, "
    "BACKEND-001 owner authorization, immutable OIDC identity contract, "
    "guarded activation wrapper, exact activation source-path allowlist, "
    "T17 unknown/protected fail-closed analysis, regression-test wiring, "
    "Python syntax, SHA bindings, canonical-state safeguards, and "
    "readback protections."
)
PY

bash -n \
  .github/actions/homio-backend-ci/transitions/core008-t06/scripts/publish_and_readback.sh

python -m pytest -q -p no:cacheprovider \
  .github/actions/homio-backend-ci/verification/tests/test_workflow_module_wiring.py \
  .github/actions/homio-backend-ci/shared/test_transition_contract.py \
  REOS_CONTROL_CENTER/context/test_github_actions_identity.py \
  REOS_CONTROL_CENTER/context/test_backend_control_projection.py
