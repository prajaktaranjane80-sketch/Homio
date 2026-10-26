#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()

backend_path = root / ".github/workflows/backend-ci.yml"
workflow_path = root / ".github/workflows/reusable-ai001-t03-transition.yml"
action_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t03/action.yml"
)
script_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t03/scripts/"
    "guarded_transition.py"
)
compile_path = (
    root
    / ".github/actions/homio-backend-ci/verification/scripts/"
    "compile_and_contracts.sh"
)
test_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/"
    "test_embeddings_retrieval.py"
)

for path in (
    backend_path,
    workflow_path,
    action_path,
    script_path,
    compile_path,
    test_path,
):
    if not path.is_file():
        raise SystemExit(
            f"Required T03 transition file is missing: {path}"
        )

backend = backend_path.read_text(encoding="utf-8")
workflow = workflow_path.read_text(encoding="utf-8")
action = action_path.read_text(encoding="utf-8")
script = script_path.read_text(encoding="utf-8")
compile_script = compile_path.read_text(encoding="utf-8")

try:
    tree = ast.parse(script, filename=str(script_path))
except SyntaxError as exc:
    raise SystemExit(
        f"T03 transition script has invalid Python syntax: {exc}"
    )

guard = (
    "if: ${{ github.event_name == 'push' && "
    "github.ref == 'refs/heads/reos-development' && "
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-COMPLETE-AI-001-T03]') }}"
)

if guard not in backend:
    raise SystemExit("Backend CI lacks the exact T03 transition guard.")

if guard not in workflow:
    raise SystemExit("Reusable T03 workflow lacks the exact commit guard.")

if backend.count(
    '".github/workflows/reusable-ai001-t03-transition.yml"'
) != 2:
    raise SystemExit(
        "T03 reusable workflow must be in both push and PR path filters."
    )

for binding in (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
):
    if binding not in workflow:
        raise SystemExit(
            f"T03 reusable workflow lacks {binding}"
        )

if '"qdrant-client==1.20.0"' not in workflow:
    raise SystemExit("T03 workflow lacks the pinned Qdrant dependency.")

if "guarded_transition.py" not in action:
    raise SystemExit(
        "T03 composite action does not invoke its guarded script."
    )

for safeguard in (
    '"AI-001-T03"',
    '"AI-001-T02": "DONE"',
    '"AI-001-T04": "CURRENT"',
    '"complete-subtask"',
    "APPROVAL: AUTHORIZE AI-001-T03 COMPLETION",
    "SCOPE: AI-001-T03 only",
    "AI-001-AC01",
    "AI-001-AC06",
    "GITHUB_ACTOR",
    "GITHUB_REF",
    "EXPECTED_SHA",
    "VERIFIED_CODE_SHA",
    "assert_exact_branch",
    "validate_state",
    "calculate_hash",
    "T03-transition-request.md",
    "T03-retrieval-evidence.md",
    "CANONICAL_BRANCH_HEAD",
    "AI-001-T03 TRANSITION AND CANONICAL READBACK: PASS",
    "refs/heads/reos-development",
    "clean_generated_bytecode",
    "compile_ai_package_sources",
    "test_embeddings_retrieval.py",
):
    if safeguard not in script:
        raise SystemExit(
            f"T03 guarded script lacks safeguard: {safeguard}"
        )

if "test_embeddings_retrieval.py" not in compile_script:
    raise SystemExit(
        "Backend CI compile/test script omits the canonical T03 test."
    )

if (
    "STATE.write_text" in script
    or "STATE_PATH.write_text" in script
):
    raise SystemExit(
        "T03 must not write canonical state outside the Control Center."
    )

if "--force" in script:
    raise SystemExit("T03 transition must never force-push.")

for node in ast.walk(tree):
    if not isinstance(node, ast.Call) or not node.args:
        continue

    command = node.args[0]
    if not isinstance(command, (ast.List, ast.Tuple)):
        continue

    values = {
        child.value
        for child in ast.walk(command)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
    }

    if "compileall" in values:
        raise SystemExit(
            "T03 must compile sources in memory, not use compileall."
        )

print(
    "AI-001-T03 transition wiring PASS: exact owner/branch/commit guard, "
    "pinned Qdrant dependency, canonical T03 test, Python syntax, state "
    "safeguards, no force-push, and remote readback protections."
)
PY
