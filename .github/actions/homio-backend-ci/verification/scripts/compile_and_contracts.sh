
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

# AI-001 T01/T02: canonical gateway and provider/model registry contracts.
# AI-001 T03: embedding compatibility and tenant/resource-scoped retrieval.
# AI-001 T04: versioned prompts, evidence-bounded context and RAG output checks.
# AI-001 T05: bounded agent runtime, typed proposals, allowlist and replay controls.
# These tests use deterministic fakes and in-memory fixtures.
# No live provider or production tool execution is enabled.
python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_model_registry.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_embeddings_retrieval.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_retrieval_and_rag.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_agent_tool_boundaries.py
