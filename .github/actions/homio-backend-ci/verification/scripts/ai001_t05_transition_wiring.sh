#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()

backend_path = root / ".github/workflows/backend-ci.yml"
workflow_path = root / ".github/workflows/reusable-ai001-t05-transition.yml"
action_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t05/action.yml"
)
script_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t05/scripts/"
    "guarded_transition.py"
)
compile_path = (
    root
    / ".github/actions/homio-backend-ci/verification/scripts/"
    "compile_and_contracts.sh"
)
request_path = (
    root / "REOS_CONTROL_CENTER/evidence/AI-001/T05-transition-request.md"
)
runtime_path = (
    root / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/agent_runtime.py"
)
bridge_path = (
    root / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tool_bridge.py"
)
test_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/"
    "test_agent_tool_boundaries.py"
)

required = (
    backend_path,
    workflow_path,
    action_path,
    script_path,
    compile_path,
    request_path,
    runtime_path,
    bridge_path,
    test_path,
)

for path in required:
    if not path.is_file():
        raise SystemExit(
            f"Required T05 transition file is missing: {path.relative_to(root)}"
        )

backend = backend_path.read_text(encoding="utf-8")
workflow = workflow_path.read_text(encoding="utf-8")
action = action_path.read_text(encoding="utf-8")
script = script_path.read_text(encoding="utf-8")
compile_script = compile_path.read_text(encoding="utf-8")
request = request_path.read_text(encoding="utf-8")

try:
    tree = ast.parse(script, filename=str(script_path))
except SyntaxError as exc:
    raise SystemExit(f"T05 guarded script has invalid Python syntax: {exc}") from exc

guard = (
    "if: ${{ github.event_name == 'push' && "
    "github.ref == 'refs/heads/reos-development' && "
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-COMPLETE-AI-001-T05]') }}"
)

if guard not in backend:
    raise SystemExit("Backend CI lacks the exact T05 transition guard.")

if guard not in workflow:
    raise SystemExit("Reusable T05 workflow lacks the exact commit guard.")

if backend.count(
    '".github/workflows/reusable-ai001-t05-transition.yml"'
) != 2:
    raise SystemExit(
        "T05 reusable workflow must be present in push and PR path filters."
    )

for binding in (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
):
    if binding not in workflow:
        raise SystemExit(f"T05 reusable workflow lacks {binding}")

if '"qdrant-client==1.20.0"' not in workflow:
    raise SystemExit("T05 workflow lacks the pinned retrieval dependency.")

if "guarded_transition.py" not in action:
    raise SystemExit("T05 composite action does not invoke its guarded script.")

for safeguard in (
    '"AI-001-T05"',
    '"AI-001-T04": "DONE"',
    '"AI-001-T05": "DONE" if transitioned else "CURRENT"',
    '"AI-001-T06": "CURRENT" if transitioned else "PENDING"',
    '"complete-subtask"',
    "APPROVAL: AUTHORIZE AI-001-T05 COMPLETION",
    "SCOPE: AI-001-T05 only",
    "AI-001-AC01",
    "AI-001-AC06",
    "GITHUB_ACTOR",
    "GITHUB_REF",
    "EXPECTED_SHA",
    "VERIFIED_CODE_SHA",
    "assert_exact_branch",
    "validate_state",
    "calculate_hash",
    "T05-transition-request.md",
    "T05-agent-runtime-evidence.md",
    "CANONICAL_BRANCH_HEAD",
    "AI-001-T05 TRANSITION AND CANONICAL READBACK: PASS",
    "refs/heads/reos-development",
    "clean_generated_bytecode",
    "compile_ai_package_sources",
    "test_retrieval_and_rag.py",
    "test_agent_tool_boundaries.py",
    "agent_runtime.py",
    "tool_bridge.py",
    "CURRENT_SUBTASK=AI-001-T06",
    "AI-001-T05|DONE|Implement agent runtime and tools",
    "AI-001-T06|CURRENT|Implement AI authorization and tenant isolation",
):
    if safeguard not in script:
        raise SystemExit(f"T05 guarded script lacks safeguard: {safeguard}")

for test_name in (
    "test_retrieval_and_rag.py",
    "test_agent_tool_boundaries.py",
):
    if test_name not in compile_script:
        raise SystemExit(f"Backend CI omits the canonical test: {test_name}")

if "APPROVAL: AUTHORIZE AI-001-T05 COMPLETION" not in request:
    raise SystemExit("T05 request lacks explicit authorization.")

if "SCOPE: AI-001-T05 only" not in request:
    raise SystemExit("T05 request is not restricted to T05.")

if "STATE.write_text" in script or "STATE_PATH.write_text" in script:
    raise SystemExit(
        "T05 must not edit canonical state outside the Control Center."
    )

if "--force" in script:
    raise SystemExit("T05 transition must never force-push.")

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
            "T05 must compile AI source in memory, not invoke compileall."
        )

print(
    "AI-001-T05 wiring PASS: exact owner/branch/prefix guards, "
    "SHA bindings, T05 source/test inventory, explicit authorization, "
    "state protections and remote readback safeguards."
)
PY
