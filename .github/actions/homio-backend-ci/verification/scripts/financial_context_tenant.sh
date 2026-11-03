#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}/REOS_CONTROL_CENTER"

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/canonical_truth/STAGE0_Canonical_Truth_Sync_Engine \
  AUTONOMY_ENGINE/security/authentication \
  AUTONOMY_ENGINE/core/commission_financial \
  tets/test_l3_canonical_authority.py \
  context/test_phase_projection.py \
  context/test_backend_workstream_transition.py \
  context/test_backend_control_projection.py \
  context/test_github_actions_identity.py \
  context/test_backend_activation_import_bootstrap.py \
  AUTONOMY_ENGINE/continuity/acrl/T17_Change_Impact_Dependency_Analysis/test_change_impact_analysis.py \
  AUTONOMY_ENGINE/core/identity_tenant
