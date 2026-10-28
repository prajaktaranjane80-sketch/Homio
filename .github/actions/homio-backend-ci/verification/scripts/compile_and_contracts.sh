#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}/REOS_CONTROL_CENTER"

# Compile Python sources in memory so verification leaves no .pyc files.
python - <<'PY'
from pathlib import Path
import sys
import tokenize

targets = (
    Path("reos_control_center.py"),
    Path("AI_AGENT_ENTRYPOINT.py"),
    Path("context"),
    Path("AUTONOMY_ENGINE/ai_platform"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T17_Change_Impact_Dependency_Analysis"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T18_Safe_Execution_Authorization_Guard"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T20_Autonomous_Repair_Patch_Verification"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T21_Git_Repository_Read_Write_Coordination"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T22_Commit_Execution_Checkpoint_Coordination"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T23_Reference_Evidence_Resolution_Engine"),
    Path("AUTONOMY_ENGINE/continuity/acrl/T24_Cross_Chat_Continuity_Recovery_Engine"),
    Path("AUTONOMY_ENGINE/continuity/acrl/runtime_integration"),
)

source_files: set[Path] = set()

for target in targets:
    if target.is_symlink() or not target.exists():
        raise SystemExit(
            f"Required Python source target is missing or symlinked: {target}"
        )

    if target.is_file():
        if target.suffix != ".py":
            raise SystemExit(f"Expected a Python source file: {target}")
        source_files.add(target)
        continue

    if not target.is_dir():
        raise SystemExit(
            f"Expected a Python file or directory: {target}"
        )

    for source_path in target.rglob("*.py"):
        if source_path.is_file() and not source_path.is_symlink():
            source_files.add(source_path)

if not source_files:
    raise SystemExit("No Python source files were discovered.")

for source_path in sorted(source_files, key=lambda item: item.as_posix()):
    try:
        with tokenize.open(source_path) as handle:
            source = handle.read()

        compile(
            source,
            str(source_path),
            "exec",
            dont_inherit=True,
        )
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        print(
            f"PYTHON_SOURCE_COMPILE_FAIL={source_path}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

print(f"PYTHON_SOURCE_COMPILE_PASS={len(source_files)}")
PY

python -c "from pathlib import Path; p = Path('tets/test_ai_agent_entrypoint_contract.py'); assert p.is_file(), f'Required contract test is missing: {p}'"

python -m pytest -q -p no:cacheprovider \
  tets/test_ai_agent_entrypoint_contract.py

# AI-001 T01/T02: gateway and provider/model registry contracts.
# AI-001 T03: embeddings and tenant-scoped retrieval.
# AI-001 T04: versioned prompts, bounded context and RAG checks.
# AI-001 T05: bounded agent runtime, typed proposals and replay controls.
# AI-001 T06: trusted-context, resource authorization and tenant tests.
# AI-001 T07: cost reservations, quota concurrency and usage accounting.
# AI-001 T08: observability, safe fallback and failure handling.
# Provider adapter and composition tests use no live provider calls.
# Provider composition requires injected server-owned policy and usage ports.
# No production tool execution is enabled.
python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_model_registry.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_embeddings_retrieval.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_retrieval_and_rag.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_agent_tool_boundaries.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_authorization_tenant_isolation.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_cost_control.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_observability_fallback.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_provider_adapters.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_ai_platform_integration.py
