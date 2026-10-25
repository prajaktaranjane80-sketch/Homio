#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}/REOS_CONTROL_CENTER"

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/runtime_integration

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context/test_audit_resume_manifest.py \
  AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context/test_repository_context.py \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/test_fast_resume_and_stale_manifest.py \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/test_new_chat_bootstrap.py \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/test_checkpoint_state_coherence.py
