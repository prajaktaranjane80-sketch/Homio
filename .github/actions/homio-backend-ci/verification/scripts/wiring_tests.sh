#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

python -m pytest -q -p no:cacheprovider \
  .github/actions/homio-backend-ci/verification/tests/test_workflow_module_wiring.py \
  .github/actions/homio-backend-ci/shared/test_transition_contract.py
