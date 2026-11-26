#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

cd "$ROOT/REOS_CONTROL_CENTER"

# Keep the EntryPoint contract regression inside the existing ACRL
# verification workflow. A missing or failing contract test fails CI.
python -m pytest -q -p no:cacheprovider \
  tets/test_ai_agent_entrypoint_contract.py

# Existing ACRL runtime integration regression.
python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/runtime_integration

# Existing bootstrap, T14 resume and derived-cache regression tests.
python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context/test_audit_resume_manifest.py \
  AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context/test_repository_context.py \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/test_fast_resume_and_stale_manifest.py \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/test_new_chat_bootstrap.py \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/test_checkpoint_state_coherence.py \
  tets/test_audit_resume_manifest_cache.py

# Existing GitHub Actions runtime pin verification.
python -m pytest -q -p no:cacheprovider \
  "$ROOT/.github/actions/homio-backend-ci/verification/tests/test_github_actions_runtime_pins.py"
