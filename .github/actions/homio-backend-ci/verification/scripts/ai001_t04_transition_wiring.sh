#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()

backend_path = root / ".github/workflows/backend-ci.yml"
workflow_path = root / ".github/workflows/reusable-ai001-t04-transition.yml"
action_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t04/action.yml"
)
script_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/ai001-t04/scripts/"
    "guarded_transition.py"
)
compile_path = (
    root
    / ".github/actions/homio-backend-ci/verification/scripts/"
    "compile_and_contracts.sh"
)
request_path = (
    root / "REOS_CONTROL_CENTER/evidence/AI-001/T04-transition-request.md"
)
prompt_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/prompt_templates.py"
)
rag_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/rag_pipeline.py"
)
retrieval_test_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/"
    "test_embeddings_retrieval.py"
)
rag_test_path = (
    root
    / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/"
    "test_retrieval_and_rag.py"
)

for path in (
    backend_path,
    workflow_path,
    action_path,
    script_path,
    compile_path,
    request_path,
    prompt_path,
    rag_path,
    retrieval_test_path,
    rag_test_path,
):
    if not path.is_file():
        raise SystemExit(
            f"Required AI-001-T04 file is missing: {path.relative_to(root)}"
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
    raise SystemExit(
        f"T04 transition script has invalid Python syntax: {exc}"
    ) from exc

guard = (
    "if: ${{ github.event_name == 'push' && "
    "github.ref == 'refs/heads/reos-development' && "
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-COMPLETE-AI-001-T04]') }}"
)

if guard not in backend:
    raise SystemExit("Backend CI lacks the exact T04 transition guard.")

if guard not in workflow:
    raise SystemExit("Reusable T04 workflow lacks the exact commit guard.")

if backend.count(
    '".github/workflows/reusable-ai001-t04-transition.yml"'
) != 2:
    raise SystemExit(
        "T04 reusable workflow must appear in both push and PR path filters."
    )

for binding in (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
):
    if binding not in workflow:
        raise SystemExit(f"T04 reusable workflow lacks {binding}")

if '"qdrant-client==1.20.0"' not in workflow:
    raise SystemExit("T04 workflow lacks the pinned Qdrant dependency.")

if "guarded_transition.py" not in action:
    raise SystemExit("T04 composite action does not invoke its guarded script.")

for safeguard in (
    '"AI-001-T04"',
    '"AI-001-T03": "DONE"',
    '"AI-001-T04": "DONE" if transitioned else "CURRENT"',
    '"AI-001-T05": "CURRENT" if transitioned else "PENDING"',
    '"complete-subtask"',
    "APPROVAL: AUTHORIZE AI-001-T04 COMPLETION",
    "SCOPE: AI-001-T04 only",
    "AI-001-AC01",
    "AI-001-AC06",
    "GITHUB_ACTOR",
    "GITHUB_REF",
    "EXPECTED_SHA",
    "VERIFIED_CODE_SHA",
    "assert_exact_branch",
    "validate_state",
    "calculate_hash",
    "T04-transition-request.md",
    "T04-rag-evidence.md",
    "CANONICAL_BRANCH_HEAD",
    "AI-001-T04 TRANSITION AND CANONICAL READBACK: PASS",
    "refs/heads/reos-development",
    "clean_generated_bytecode",
    "compile_ai_package_sources",
    "test_embeddings_retrieval.py",
    "test_retrieval_and_rag.py",
    "prompt_templates.py",
    "rag_pipeline.py",
    "CURRENT_SUBTASK=AI-001-T05",
    "AI-001-T05|CURRENT|Implement agent runtime and tools",
):
    if safeguard not in script:
        raise SystemExit(
            f"T04 guarded script lacks safeguard: {safeguard}"
        )

for test_name in (
    "test_embeddings_retrieval.py",
    "test_retrieval_and_rag.py",
):
    if test_name not in compile_script:
        raise SystemExit(
            f"Backend CI omits the canonical test: {test_name}"
        )

if "APPROVAL: AUTHORIZE AI-001-T04 COMPLETION" not in request:
    raise SystemExit("T04 transition request lacks explicit authorization.")

if "SCOPE: AI-001-T04 only" not in request:
    raise SystemExit("T04 transition request is not restricted to T04.")

if "STATE.write_text" in script or "STATE_PATH.write_text" in script:
    raise SystemExit(
        "T04 must not edit canonical state outside the Control Center."
    )

if "--force" in script:
    raise SystemExit("T04 transition must never force-push.")

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
            "T04 transition must compile source in memory, not use compileall."
        )

print(
    "AI-001-T04 wiring PASS: required files, exact guards, Qdrant pin, "
    "authorization request, canonical RAG tests, state protections, "
    "and guarded readback checks."
)
PY
