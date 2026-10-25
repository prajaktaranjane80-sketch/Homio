#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}/REOS_CONTROL_CENTER"

python -m compileall -q \
  reos_control_center.py \
  AI_AGENT_ENTRYPOINT.py \
  context \
  AUTONOMY_ENGINE/ai_platform \
  AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap \
  AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context \
  AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery \
  AUTONOMY_ENGINE/continuity/acrl/T17_Change_Impact_Dependency_Analysis \
  AUTONOMY_ENGINE/continuity/acrl/T18_Safe_Execution_Authorization_Guard \
  AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis \
  AUTONOMY_ENGINE/continuity/acrl/T20_Autonomous_Repair_Patch_Verification \
  AUTONOMY_ENGINE/continuity/acrl/T21_Git_Repository_Read_Write_Coordination \
  AUTONOMY_ENGINE/continuity/acrl/T22_Commit_Execution_Checkpoint_Coordination \
  AUTONOMY_ENGINE/continuity/acrl/T23_Reference_Evidence_Resolution_Engine \
  AUTONOMY_ENGINE/continuity/acrl/T24_Cross_Chat_Continuity_Recovery_Engine \
  AUTONOMY_ENGINE/continuity/acrl/runtime_integration

python -c "from pathlib import Path; p = Path('tets/test_ai_agent_entrypoint_contract.py'); assert p.is_file(), f'Required contract test is missing: {p}'"

python -m pytest -q -p no:cacheprovider \
  tets/test_ai_agent_entrypoint_contract.py

# AI-001-T01: explicitly compile and test the provider-independent AI package.
# Run only the canonical package-owned test paths; no live provider is enabled.
python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py
