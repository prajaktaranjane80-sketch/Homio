#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python - <<'PY'
import ast
from pathlib import Path

root = Path.cwd()

complete_script = (
    root
    / ".github/actions/homio-backend-ci/transitions/core008-t06/scripts/complete_and_evidence.py"
)
publish_script = (
    root
    / ".github/actions/homio-backend-ci/transitions/core008-t06/scripts/publish_and_readback.sh"
)
workflow_path = (
    root
    / ".github/workflows/reusable-core008-t06-transition.yml"
)

for path in (complete_script, publish_script, workflow_path):
    if not path.is_file():
        raise SystemExit(f"Required T06 transition file is missing: {path}")

try:
    ast.parse(
        complete_script.read_text(encoding="utf-8"),
        filename=str(complete_script),
    )
except (OSError, UnicodeError, SyntaxError) as exc:
    raise SystemExit(f"T06 completion script is not valid Python: {exc}") from exc

workflow = workflow_path.read_text(encoding="utf-8")
required_bindings = (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
)

missing = [
    value
    for value in required_bindings
    if value not in workflow
]
if missing:
    raise SystemExit(
        "T06 transition workflow is missing required environment bindings: "
        + ", ".join(missing)
    )

print("T06 transition Python syntax and metadata wiring: PASS")
PY

bash -n \
  .github/actions/homio-backend-ci/transitions/core008-t06/scripts/publish_and_readback.sh

python -m pytest -q -p no:cacheprovider \
  .github/actions/homio-backend-ci/verification/tests/test_workflow_module_wiring.py \
  .github/actions/homio-backend-ci/shared/test_transition_contract.py
