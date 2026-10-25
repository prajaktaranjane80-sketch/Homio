#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()
actions = root / ".github/actions/homio-backend-ci"
workflows = root / ".github/workflows"

transition_scripts = {
    "T06": actions / "transitions/core008-t06/scripts/complete_and_evidence.py",
    "T07": actions / "transitions/core008-t07/scripts/guarded_transition.py",
    "T08": actions / "transitions/core008-t08/scripts/guarded_transition.py",
    "T09": actions / "transitions/core008-t09/scripts/guarded_transition.py",
}
transition_actions = {
    "T06": actions / "transitions/core008-t06/action.yml",
    "T07": actions / "transitions/core008-t07/action.yml",
    "T08": actions / "transitions/core008-t08/action.yml",
    "T09": actions / "transitions/core008-t09/action.yml",
}
transition_workflows = {
    "T06": workflows / "reusable-core008-t06-transition.yml",
    "T07": workflows / "reusable-core008-t07-transition.yml",
    "T08": workflows / "reusable-core008-t08-transition.yml",
    "T09": workflows / "reusable-core008-t09-transition.yml",
}
backend_path = workflows / "backend-ci.yml"
t06_publish = actions / "transitions/core008-t06/scripts/publish_and_readback.sh"

required_files = (
    *transition_scripts.values(),
    *transition_actions.values(),
    *transition_workflows.values(),
    t06_publish,
    backend_path,
)

for path in required_files:
    if not path.is_file():
        raise SystemExit(
            f"Required transition file is missing: {path.relative_to(root)}"
        )

for path in transition_scripts.values():
    try:
        ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise SystemExit(f"Invalid Python in {path}: {exc}") from exc

backend = backend_path.read_text(encoding="utf-8")
shared = (actions / "shared/transition_contract.py").read_text(
    encoding="utf-8"
)
t06_publish_text = t06_publish.read_text(encoding="utf-8")

if ".github/actions/homio-backend-ci/**" not in backend:
    raise SystemExit(
        "Backend CI path filters omit the owned action directory."
    )

for task in ("T06", "T07", "T08", "T09"):
    prefix = f"[CONTROL-CENTER-COMPLETE-CORE-008-{task}]"
    guard = (
        "if: ${{ github.event_name == 'push' && "
        "github.ref == 'refs/heads/reos-development' && "
        f"startsWith(github.event.head_commit.message, '{prefix}') }}"
    )
    workflow = transition_workflows[task].read_text(
        encoding="utf-8"
    )

    for name, content in (
        (f"{task} backend", backend),
        (f"{task} reusable", workflow),
    ):
        if guard not in content:
            raise SystemExit(
                f"{name} lacks its exact owner/branch/commit-prefix guard."
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
                f"{task} reusable workflow lacks: {binding}"
            )

    composite = transition_actions[task].read_text(
        encoding="utf-8"
    )
    script_name = transition_scripts[task].name
    if script_name not in composite:
        raise SystemExit(
            f"{task} composite action does not invoke {script_name}."
        )

for path in (
    '".github/workflows/backend-ci.yml"',
    '".github/workflows/reusable-backend-verification.yml"',
    '".github/workflows/reusable-core008-t06-transition.yml"',
    '".github/workflows/reusable-core008-t07-transition.yml"',
    '".github/workflows/reusable-core008-t08-transition.yml"',
    '".github/workflows/reusable-core008-t09-transition.yml"',
):
    if backend.count(path) != 2:
        raise SystemExit(
            f"Workflow push/PR path filter count must be 2: {path}"
        )

for task in ("T07", "T08", "T09"):
    script = transition_scripts[task].read_text(
        encoding="utf-8"
    )
    for safeguard in (
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
    ):
        if safeguard not in script:
            raise SystemExit(
                f"{task} guarded script lacks safeguard: {safeguard}"
            )

    if "STATE.write_text" in script or "STATE_PATH.write_text" in script:
        raise SystemExit(
            f"{task} must not edit canonical state outside the controller."
        )
    if "--force" in script:
        raise SystemExit(
            f"{task} transition must never force-push."
        )

t08_script = transition_scripts["T08"].read_text(encoding="utf-8")
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
            f"T08 does not include expected existing test file: {test_name}"
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

t09_script = transition_scripts["T09"].read_text(encoding="utf-8")
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

if "require_core008_criteria_baseline" not in shared:
    raise SystemExit(
        "Shared transition contract lacks the CORE-008 criteria baseline."
    )

for required in (
    "EXPECTED_TRACKED",
    "git push origin HEAD:refs/heads/reos-development",
    "CANONICAL READBACK PASS",
):
    if required not in t06_publish_text:
        raise SystemExit(
            f"Existing T06 publisher is missing safeguard: {required}"
        )
if "--force" in t06_publish_text:
    raise SystemExit("T06 publisher must never force-push.")

print(
    "Transition wiring PASS: T06/T07/T08/T09 authorization guards, "
    "SHA bindings, focus-test inventory, canonical-state safeguards, "
    "and readback protections."
)
PY

bash -n \
  .github/actions/homio-backend-ci/transitions/core008-t06/scripts/publish_and_readback.sh

python -m pytest -q -p no:cacheprovider \
  .github/actions/homio-backend-ci/verification/tests/test_workflow_module_wiring.py \
  .github/actions/homio-backend-ci/shared/test_transition_contract.py
