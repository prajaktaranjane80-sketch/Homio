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
composite_path = (
    root
    / ".github/actions/homio-backend-ci/transitions/core008-t06/action.yml"
)
backend_path = root / ".github/workflows/backend-ci.yml"
reusable_path = (
    root
    / ".github/workflows/reusable-core008-t06-transition.yml"
)

required_files = (
    complete_script,
    publish_script,
    composite_path,
    backend_path,
    reusable_path,
)

for path in required_files:
    if not path.is_file():
        raise SystemExit(
            f"Required T06 transition file is missing: {path.relative_to(root)}"
        )

try:
    ast.parse(
        complete_script.read_text(encoding="utf-8"),
        filename=str(complete_script),
    )
except (OSError, UnicodeError, SyntaxError) as exc:
    raise SystemExit(
        f"T06 completion script is not valid Python: {exc}"
    ) from exc

backend = backend_path.read_text(encoding="utf-8")
reusable = reusable_path.read_text(encoding="utf-8")
composite = composite_path.read_text(encoding="utf-8")
publisher = publish_script.read_text(encoding="utf-8")

authorization_guard = (
    "startsWith(github.event.head_commit.message, "
    "'[CONTROL-CENTER-COMPLETE-CORE-008-T06]')"
)

for name, workflow in (
    ("backend orchestrator", backend),
    ("reusable transition workflow", reusable),
):
    if authorization_guard not in workflow:
        raise SystemExit(
            f"{name} is missing the exact T06 authorization prefix guard."
        )

required_bindings = (
    "EXPECTED_SHA: ${{ github.sha }}",
    "VERIFIED_CODE_SHA: ${{ github.sha }}",
    "ACTIONS_RUN_ID: ${{ github.run_id }}",
    "ACTIONS_SERVER_URL: ${{ github.server_url }}",
    "ACTIONS_REPOSITORY: ${{ github.repository }}",
)

missing_bindings = [
    value for value in required_bindings if value not in reusable
]
if missing_bindings:
    raise SystemExit(
        "T06 transition workflow lacks environment bindings: "
        + ", ".join(missing_bindings)
    )

required_publish_guards = (
    "EXPECTED_TRACKED",
    "git push origin HEAD:refs/heads/reos-development",
    "CANONICAL READBACK PASS",
)

missing_publish_guards = [
    value for value in required_publish_guards if value not in publisher
]
if missing_publish_guards:
    raise SystemExit(
        "T06 publisher lacks required safeguards: "
        + ", ".join(missing_publish_guards)
    )

if "--force" in publisher:
    raise SystemExit(
        "T06 publisher must never use a force-push option."
    )

if "publish_and_readback.sh" not in composite:
    raise SystemExit(
        "T06 composite action does not invoke the publisher."
    )

print(
    "T06 guard verification PASS: authorization, SHA bindings, "
    "allowlist, non-force push, and canonical readback."
)
PY

bash -n \
  .github/actions/homio-backend-ci/transitions/core008-t06/scripts/publish_and_readback.sh

python -m pytest -q -p no:cacheprovider \
  .github/actions/homio-backend-ci/verification/tests/test_workflow_module_wiring.py \
  .github/actions/homio-backend-ci/shared/test_transition_contract.py
