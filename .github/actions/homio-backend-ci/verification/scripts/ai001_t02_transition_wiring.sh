#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()

backend_path = root / ".github/workflows/backend-ci.yml"
workflow_path = root / ".github/workflows/reusable-ai001-t02-transition.yml"
action_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t02/action.yml"
)
script_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t02/scripts/"
    "guarded_transition.py"
)
compile_path = (
    root
    / ".github/actions/homio-backend-ci/verification/scripts/"
    "compile_and_contracts.sh"
)
registry_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_registry.py"
)

for path in (
    backend_path,
    workflow_path,
    action_path,
    script_path,
    compile_path,
    registry_path,
):
    if not path.is_file():
        raise SystemExit(f"Required T02 transition file is missing: {path}")

backend = backend_path.read_text(encoding="utf-8")
workflow = workflow_path.read_text(encoding="utf-8")
action = action_path.read_text(encoding="utf-8")
script = script_path.read_text(encoding="utf-8")
compile_script = compile_path.read_text(encoding="utf-8")
registry_source = registry_path.read_text(encoding="utf-8")

try:
    tree = ast.parse(script, filename=str(script_path))
except SyntaxError as exc:
    raise SystemExit(f"T02 transition script has invalid Python syntax: {exc}")

guard = (
    "if: ${{ github.event_name == 'push' && "
    "github.ref == 'refs/heads/reos-development' && "
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-COMPLETE-AI-001-T02]') }}"
)

if guard not in backend:
    raise SystemExit("Backend CI lacks the exact T02 transition guard.")

if guard not in workflow:
    raise SystemExit("Reusable T02 workflow lacks the exact commit guard.")

if backend.count(
    '".github/workflows/reusable-ai001-t02-transition.yml"'
) != 2:
    raise SystemExit(
        "T02 reusable workflow must be in push and PR path filters."
    )

for binding in (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
):
    if binding not in workflow:
        raise SystemExit(f"T02 reusable workflow lacks {binding}")

if "guarded_transition.py" not in action:
    raise SystemExit("T02 composite action does not invoke its guarded script.")

for safeguard in (
    '"AI-001-T02"',
    '"complete-subtask"',
    "APPROVAL: AUTHORIZE AI-001-T02 COMPLETION",
    "SCOPE: AI-001-T02 only",
    "AI-001-T01",
    "AI-001-T03",
    "AI-001-AC01",
    "AI-001-AC06",
    "GITHUB_ACTOR",
    "GITHUB_REF",
    "EXPECTED_SHA",
    "VERIFIED_CODE_SHA",
    "assert_exact_branch",
    "validate_state",
    "calculate_hash",
    "T02-transition-request.md",
    "T02-registry-evidence.md",
    "CANONICAL_BRANCH_HEAD",
    "AI-001-T02 TRANSITION AND CANONICAL READBACK: PASS",
    "refs/heads/reos-development",
    "clean_generated_bytecode",
    "compile_ai_package_sources",
):
    if safeguard not in script:
        raise SystemExit(f"T02 guarded script lacks safeguard: {safeguard}")

# Structurally reject an actual compileall command, without false positives
# from comments or explanatory text.
for node in ast.walk(tree):
    if not isinstance(node, ast.Call) or not node.args:
        continue

    command = node.args[0]
    if not isinstance(command, (ast.List, ast.Tuple)):
        continue

    values = {
        child.value
        for child in ast.walk(command)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }

    if "compileall" in values:
        raise SystemExit("T02 guarded script must not execute compileall.")

if "STATE.write_text" in script or "STATE_PATH.write_text" in script:
    raise SystemExit(
        "T02 must not write canonical state outside the controller."
    )

if "--force" in script:
    raise SystemExit("T02 transition must never force-push.")

# Verify test inventory in the canonical transition and backend test runner.
for test_name in (
    "test_contracts.py",
    "test_model_gateway.py",
    "test_model_registry.py",
    "test_public_contract_stability.py",
):
    test_path = (
        root
        / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests"
        / test_name
    )

    if not test_path.is_file():
        raise SystemExit(f"Canonical T02 test is missing: {test_path}")

    if test_name not in script:
        raise SystemExit(f"T02 transition omits focused test {test_name}")

    if test_name not in compile_script:
        raise SystemExit(f"Backend CI compile/test script omits {test_name}")

# Check registry classes against their actual source file.
# Do not search for class definitions only in the shell test runner.
for class_declaration in (
    "class ModelRegistry:",
    "class ProviderRegistry:",
):
    if class_declaration not in registry_source:
        raise SystemExit(
            f"Canonical model_registry.py lacks {class_declaration}"
        )

if "test_model_registry.py" not in compile_script + script:
    raise SystemExit(
        "T02 registry test is absent from the canonical test inventory."
    )

print(
    "AI-001-T02 transition wiring PASS: owner/branch/prefix guard, "
    "Python syntax, canonical registry source and test inventory, "
    "state safeguards, bytecode-safe transition compilation, "
    "and canonical readback protections."
)
PY
