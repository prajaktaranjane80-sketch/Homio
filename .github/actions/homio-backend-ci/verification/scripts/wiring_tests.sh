
#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()
actions = root / ".github/actions/homio-backend-ci"
workflows = root / ".github/workflows"

t06_complete = actions / "transitions/core008-t06/scripts/complete_and_evidence.py"
t06_publish = actions / "transitions/core008-t06/scripts/publish_and_readback.sh"
t06_action = actions / "transitions/core008-t06/action.yml"
t06_reusable = workflows / "reusable-core008-t06-transition.yml"

t07_script = actions / "transitions/core008-t07/scripts/guarded_transition.py"
t07_action = actions / "transitions/core008-t07/action.yml"
t07_reusable = workflows / "reusable-core008-t07-transition.yml"

backend_path = workflows / "backend-ci.yml"
required_files = (
    t06_complete,
    t06_publish,
    t06_action,
    t06_reusable,
    t07_script,
    t07_action,
    t07_reusable,
    backend_path,
)

for path in required_files:
    if not path.is_file():
        raise SystemExit(
            f"Required transition file is missing: {path.relative_to(root)}"
        )

for path in (t06_complete, t07_script):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise SystemExit(f"Invalid Python in {path}: {exc}") from exc

backend = backend_path.read_text(encoding="utf-8")
t06_workflow = t06_reusable.read_text(encoding="utf-8")
t07_workflow = t07_reusable.read_text(encoding="utf-8")
t06_composite = t06_action.read_text(encoding="utf-8")
t07_composite = t07_action.read_text(encoding="utf-8")
t06_publisher = t06_publish.read_text(encoding="utf-8")
t07_source = t07_script.read_text(encoding="utf-8")

if ".github/actions/homio-backend-ci/**" not in backend:
    raise SystemExit("Backend CI path filters omit the owned action directory.")

guards = {
    "T06": (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        "startsWith(github.event.head_commit.message, "
        "'[CONTROL-CENTER-COMPLETE-CORE-008-T06]') }}"
    ),
    "T07": (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        "startsWith(github.event.head_commit.message, "
        "'[CONTROL-CENTER-COMPLETE-CORE-008-T07]') }}"
    ),
}

for label, workflow, guard in (
    ("T06 backend", backend, guards["T06"]),
    ("T06 reusable", t06_workflow, guards["T06"]),
    ("T07 backend", backend, guards["T07"]),
    ("T07 reusable", t07_workflow, guards["T07"]),
):
    if guard not in workflow:
        raise SystemExit(
            f"{label} workflow lacks its exact authorization guard."
        )

for label, workflow in (("T06", t06_workflow), ("T07", t07_workflow)):
    for binding in (
        "EXPECTED_SHA: ${{ github.sha }}",
        "VERIFIED_CODE_SHA: ${{ github.sha }}",
        "ACTIONS_RUN_ID: ${{ github.run_id }}",
        "ACTIONS_SERVER_URL: ${{ github.server_url }}",
        "ACTIONS_REPOSITORY: ${{ github.repository }}",
    ):
        if binding not in workflow:
            raise SystemExit(f"{label} reusable workflow lacks: {binding}")

for required in (
    '"complete-subtask"',
    '"CORE-008-T07"',
    "require_core008_criteria_baseline",
    '"git", "push", "origin", "HEAD:refs/heads/reos-development"',
    "CANONICAL_BRANCH_HEAD",
    "return output.strip()",
    "CORE-008-AC01",
    "CORE-008-AC04",
    "CORE-008-AC05",
    "CORE-008-AC06",
):
    if required not in t07_source:
        raise SystemExit(
            f"T07 guarded script lacks required safeguard: {required}"
        )

if "STATE_PATH.write_text" in t07_source or "STATE.write_text" in t07_source:
    raise SystemExit(
        "T07 must use the Control Center, not manually edit state.json."
    )

if "--force" in t07_source:
    raise SystemExit("T07 transition must never force-push.")

if "guarded_transition.py" not in t07_composite:
    raise SystemExit("T07 composite action does not invoke its guarded script.")

if "publish_and_readback.sh" not in t06_composite:
    raise SystemExit("T06 composite action no longer invokes its publisher.")

t07_path = '".github/workflows/reusable-core008-t07-transition.yml"'
if backend.count(t07_path) != 2:
    raise SystemExit(
        "T07 reusable workflow must be in both push and pull_request path filters."
    )

print(
    "Transition wiring PASS: T06/T07 owner, branch, commit-prefix, "
    "SHA bindings, state baseline, no-manual-state-edit guard, "
    "and workflow trigger filters."
)
PY

bash -n \
  .github/actions/homio-backend-ci/transitions/core008-t06/scripts/publish_and_readback.sh

python -m pytest -q -p no:cacheprovider \
  .github/actions/homio-backend-ci/verification/tests/test_workflow_module_wiring.py \
  .github/actions/homio-backend-ci/shared/test_transition_contract.py
