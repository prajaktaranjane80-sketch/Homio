#!/usr/bin/env bash
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}/REOS_CONTROL_CENTER"

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T18_Safe_Execution_Authorization_Guard

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery \
  AUTONOMY_ENGINE/continuity/acrl/T17_Change_Impact_Dependency_Analysis

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T20_Autonomous_Repair_Patch_Verification

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T21_Git_Repository_Read_Write_Coordination

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T22_Commit_Execution_Checkpoint_Coordination

python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/continuity/acrl/T23_Reference_Evidence_Resolution_Engine \
  AUTONOMY_ENGINE/continuity/acrl/T24_Cross_Chat_Continuity_Recovery_Engine
