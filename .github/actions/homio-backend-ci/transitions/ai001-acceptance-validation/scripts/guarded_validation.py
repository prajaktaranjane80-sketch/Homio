from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data/state.json"
PACKET = CONTROL / "packets/NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"
AI_ROOT = CONTROL / "AUTONOMY_ENGINE/ai_platform"
AI_TESTS = AI_ROOT / "tests"
SEARCH_ROOT = CONTROL / "AUTONOMY_ENGINE/core/search_matching"
ACRL_ROOT = CONTROL / "AUTONOMY_ENGINE/continuity/acrl"
REQUEST = CONTROL / "evidence/AI-001/acceptance-validation-request.md"
EVIDENCE = CONTROL / "evidence/AI-001/acceptance-criteria-validation-ci-evidence.md"

AI_TEST_NAMES = (
    "test_contracts.py",
    "test_model_gateway.py",
    "test_model_registry.py",
    "test_public_contract_stability.py",
    "test_embeddings_retrieval.py",
    "test_retrieval_and_rag.py",
    "test_agent_tool_boundaries.py",
    "test_authorization_tenant_isolation.py",
    "test_cost_control.py",
    "test_observability_fallback.py",
)

SEARCH_TEST_NAMES = (
    "test_qdrant_indexing.py",
    "test_qdrant_indexing_adversarial.py",
    "test_hybrid_retrieval.py",
    "test_core005_regression.py",
)

AI_TEST_PREFIX = "AUTONOMY_ENGINE/ai_platform/tests"
SEARCH_TEST_PREFIX = "AUTONOMY_ENGINE/core/search_matching"

CRITERION_TESTS: dict[str, tuple[str, ...]] = {
    "AI-001-AC01": (
        f"{AI_TEST_PREFIX}/test_model_gateway.py",
        f"{AI_TEST_PREFIX}/test_model_registry.py",
        f"{AI_TEST_PREFIX}/test_public_contract_stability.py",
    ),
    "AI-001-AC02": (
        f"{AI_TEST_PREFIX}/test_contracts.py",
        f"{AI_TEST_PREFIX}/test_agent_tool_boundaries.py",
        f"{AI_TEST_PREFIX}/test_authorization_tenant_isolation.py",
    ),
    "AI-001-AC03": (
        f"{AI_TEST_PREFIX}/test_embeddings_retrieval.py",
        f"{AI_TEST_PREFIX}/test_retrieval_and_rag.py",
        f"{SEARCH_TEST_PREFIX}/test_qdrant_indexing.py",
        f"{SEARCH_TEST_PREFIX}/test_qdrant_indexing_adversarial.py",
        f"{SEARCH_TEST_PREFIX}/test_hybrid_retrieval.py",
        f"{SEARCH_TEST_PREFIX}/test_core005_regression.py",
    ),
    "AI-001-AC04": (
        f"{AI_TEST_PREFIX}/test_model_gateway.py",
        f"{AI_TEST_PREFIX}/test_model_registry.py",
        f"{AI_TEST_PREFIX}/test_cost_control.py",
    ),
    "AI-001-AC05": (
        f"{AI_TEST_PREFIX}/test_agent_tool_boundaries.py",
        f"{AI_TEST_PREFIX}/test_authorization_tenant_isolation.py",
    ),
    "AI-001-AC06": (
        f"{AI_TEST_PREFIX}/test_observability_fallback.py",
        f"{AI_TEST_PREFIX}/test_model_gateway.py",
    ),
}

MIN_FOCUSED_COUNTS = {
    "AI-001-AC01": 30,
    "AI-001-AC02": 45,
    "AI-001-AC03": 85,
    "AI-001-AC04": 45,
    "AI-001-AC05": 45,
    "AI-001-AC06": 20,
}

SOURCE_PATHS = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/__init__.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/contracts.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/errors.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/ports.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_registry.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_gateway.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/embeddings.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/retrieval_adapter.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/prompt_templates.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/rag_pipeline.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/agent_runtime.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tool_bridge.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/authorization.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/cost_control.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/settings.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/observability.py",
    *(
        f"REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/{name}"
        for name in AI_TEST_NAMES
    ),
    "REOS_CONTROL_CENTER/tets/test_ai_agent_entrypoint_contract.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/qdrant_indexing.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/search_index_contract.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/hybrid_retrieval.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/projection_sync.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/runtime_adapter.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/search_consistency.py",
    *(
        f"REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/{name}"
        for name in SEARCH_TEST_NAMES
    ),
)


def fail(message: str) -> None:
    raise SystemExit(f"AI-001 ACCEPTANCE VALIDATION BLOCKED: {message}")


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = True,
    display: bool = True,
) -> str:
    result = subprocess.run(
        command,
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    output = (result.stdout or "") if capture else ""
    if output and display:
        print(output, end="" if output.endswith("\n") else "\n")
    if result.returncode:
        fail(f"command failed ({result.returncode}): {' '.join(command)}")
    return output.strip()


def read_state() -> dict:
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"canonical state cannot be read: {exc}")
    if not isinstance(state, dict):
        fail("canonical state root is not an object")
    return state


def verify_integrity() -> None:
    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )
    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    state = read_state()
    if state.get("integrity", {}).get("sha256") != calculate_hash(state):
        fail("state integrity digest does not match canonical contents")


def state_indexes(
    state: dict,
) -> tuple[dict, dict[str, dict], dict[str, dict]]:
    gate = state.get("gate_plans", {}).get("AI-001")
    if not isinstance(gate, dict):
        fail("canonical AI-001 gate is missing")
    subtasks = {
        item.get("id"): item
        for item in gate.get("subtasks", [])
        if isinstance(item, dict)
    }
    criteria = {
        item.get("id"): item
        for item in gate.get("criteria_state", [])
        if isinstance(item, dict)
    }
    return gate, subtasks, criteria


def require_prevalidation_state(state: dict) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if execution.get("current_gate") != "AI-001":
        fail("canonical current gate is not AI-001")
    if execution.get("current_subtask") != "AI-001-T10":
        fail("execution pointer is not AI-001-T10")
    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution status is not CONTROL_CENTER_DRIVEN")
    if gate.get("status") != "READY_FOR_VALIDATION":
        fail(
            "gate must be READY_FOR_VALIDATION; "
            f"found {gate.get('status')!r}"
        )
    if gate.get("current_subtask") != "AI-001-T10":
        fail("gate current_subtask is not AI-001-T10")

    expected_tasks = {
        **{f"AI-001-T{i:02d}": "DONE" for i in range(1, 10)},
        "AI-001-T10": "PENDING",
    }
    if set(subtasks) != set(expected_tasks):
        fail("AI-001 subtask inventory differs from T01-T10")
    for task_id, expected in expected_tasks.items():
        actual = subtasks[task_id].get("status")
        if actual != expected:
            fail(f"{task_id} must be {expected}; found {actual!r}")

    expected_criteria = {f"AI-001-AC{i:02d}" for i in range(1, 7)}
    if set(criteria) != expected_criteria:
        fail("AI-001 acceptance-criteria inventory differs from AC01-AC06")
    for criterion_id, criterion in criteria.items():
        if criterion.get("status") != "PENDING":
            fail(
                f"{criterion_id} is not PENDING at validation start; "
                "refusing a partial or duplicate validation transition"
            )
        if criterion.get("evidence") is not None:
            fail(f"{criterion_id} already contains evidence")
        if criterion.get("verified_at") is not None:
            fail(f"{criterion_id} already contains a verification timestamp")


def require_validated_state(
    state: dict,
    evidence_notes: dict[str, str],
) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if execution.get("current_gate") != "AI-001":
        fail("readback current gate is not AI-001")
    if execution.get("current_subtask") != "AI-001-T10":
        fail("readback execution pointer is not AI-001-T10")
    if execution.get("status") != "READY_FOR_APPROVAL":
        fail(
            "execution status is not READY_FOR_APPROVAL: "
            f"{execution.get('status')!r}"
        )
    if gate.get("status") != "VALIDATED":
        fail("AI-001 gate is not VALIDATED")
    if gate.get("current_subtask") != "AI-001-T10":
        fail("gate current_subtask is not AI-001-T10")

    for index in range(1, 10):
        task_id = f"AI-001-T{index:02d}"
        if subtasks.get(task_id, {}).get("status") != "DONE":
            fail(f"{task_id} changed or is not DONE")
    if subtasks.get("AI-001-T10", {}).get("status") != "READY_FOR_APPROVAL":
        fail("T10 must be READY_FOR_APPROVAL; it must not be auto-approved")

    expected_criteria = {f"AI-001-AC{i:02d}" for i in range(1, 7)}
    if set(criteria) != expected_criteria:
        fail("readback acceptance-criteria inventory differs from AC01-AC06")
    for criterion_id, expected_evidence in evidence_notes.items():
        criterion = criteria[criterion_id]
        if criterion.get("status") != "VERIFIED":
            fail(f"{criterion_id} is not VERIFIED")
        if criterion.get("evidence") != expected_evidence:
            fail(f"canonical evidence mismatch for {criterion_id}")
        if not criterion.get("verified_at"):
            fail(f"{criterion_id} lacks verified_at timestamp")

    if gate.get("completion_policy") != (
        "All blocking subtasks DONE + all criteria VERIFIED + explicit approval."
    ):
        fail("canonical AI-001 completion policy has changed")
    if state.get("session", {}).get("last_handoff") != (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is not repository-relative")


def assert_exact_branch(expected_sha: str) -> None:
    if run(["git", "rev-parse", "HEAD"], display=False) != expected_sha:
        fail("checked-out HEAD differs from the verified source SHA")
    run(
        ["git", "fetch", "--no-tags", "origin", "refs/heads/reos-development"],
        capture=False,
    )
    if run(["git", "rev-parse", "FETCH_HEAD"], display=False) != expected_sha:
        fail("canonical reos-development branch changed; refusing stale validation")


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
    )
    if (
        original.count(b"\n") > 0
        and original.count(b"\n") == original.count(b"\r\n")
    ):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def controller_command(arguments: list[str]) -> str:
    import REOS_CONTROL_CENTER.reos_control_center as controller

    previous_packets = controller.PACKETS
    previous_argv = sys.argv[:]
    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")
    captured = io.StringIO()
    try:
        sys.argv = ["reos_control_center.py", *arguments]
        with contextlib.redirect_stdout(captured):
            try:
                controller.main()
            except SystemExit as exc:
                if exc.code not in (None, 0):
                    fail(f"Control Center command failed: {exc}")
        output = captured.getvalue()
        if output:
            print(output, end="" if output.endswith("\n") else "\n")
        return output.strip()
    finally:
        sys.argv = previous_argv
        controller.PACKETS = previous_packets


def pytest_count(
    output: str,
    label: str,
    minimum: int = 1,
) -> int:
    matches = re.findall(r"(\d+)\s+passed(?:\s|,|$)", output)
    if not matches:
        fail(f"{label}: no positive pytest pass count found")
    if re.search(r"\b\d+\s+failed\b", output):
        fail(f"{label}: pytest reported failures")
    if re.search(r"\b\d+\s+errors?\b", output):
        fail(f"{label}: pytest reported errors")
    count = int(matches[-1])
    if count < minimum:
        fail(f"{label}: {count} passed is below required minimum {minimum}")
    return count


def run_pytest_paths(
    label: str,
    paths: tuple[str, ...] | list[str],
    minimum: int = 1,
) -> int:
    output = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *paths,
        ],
        cwd=CONTROL,
    )
    count = pytest_count(output, label, minimum)
    print(
        f"{label.upper().replace(' ', '_').replace('-', '_')}_PASSED={count}"
    )
    return count


def compile_project_sources() -> int:
    sources = {
        path for path in AI_ROOT.rglob("*.py") if path.is_file()
    }
    sources.update(
        {
            SEARCH_ROOT / "qdrant_indexing.py",
            SEARCH_ROOT / "search_index_contract.py",
            SEARCH_ROOT / "hybrid_retrieval.py",
            SEARCH_ROOT / "projection_sync.py",
            SEARCH_ROOT / "runtime_adapter.py",
            SEARCH_ROOT / "search_consistency.py",
        }
    )
    if not sources:
        fail("AI platform and retrieval source inventory is empty")
    for source in sorted(sources):
        try:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            fail(f"in-memory source compilation failed for {source}: {exc}")
    print(f"AI_AND_RETRIEVAL_SOURCE_COMPILE_PASS={len(sources)}")
    return len(sources)


def assert_inventory() -> None:
    required = [ROOT / relative for relative in SOURCE_PATHS]
    required.extend(
        [
            AI_ROOT / "__init__.py",
            ROOT / ".github/actions/homio-backend-ci/verification/scripts/compile_and_contracts.sh",
        ]
    )
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in required
        if not path.is_file()
    ]
    if missing:
        fail(f"required source or test files are missing: {missing}")

    for duplicate in (
        AI_ROOT / "test_contracts.py",
        AI_ROOT / "test_model_gateway.py",
    ):
        if duplicate.exists():
            fail(
                "obsolete duplicate AI test path exists: "
                f"{duplicate.relative_to(ROOT)}"
            )


def preflight(expected_sha: str) -> None:
    required_env = (
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_SERVER_URL",
        "ACTIONS_REPOSITORY",
        "GITHUB_ACTOR",
        "GITHUB_REF",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "RUNNER_TEMP",
    )
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        fail(f"missing required environment values: {missing}")
    if os.environ["GITHUB_ACTOR"] != "prajaktaranjane80-sketch":
        fail("only the repository owner may authorize acceptance validation")
    if os.environ["GITHUB_EVENT_NAME"] != "push":
        fail("acceptance validation is allowed only on a guarded owner push")
    if os.environ["GITHUB_REF"] != "refs/heads/reos-development":
        fail("only reos-development is permitted")
    if expected_sha != os.environ["VERIFIED_CODE_SHA"]:
        fail("expected and verified code SHAs differ")

    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    if not event_path.is_file():
        fail("GitHub push event payload is missing")
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read GitHub push event payload: {exc}")
    event_message = event.get("head_commit", {}).get("message", "")
    if not event_message.startswith("[CONTROL-CENTER-VALIDATE-AI-001-ACCEPTANCE]"):
        fail("triggering commit lacks the exact AI-001 acceptance validation prefix")

    assert_exact_branch(expected_sha)
    if run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        display=False,
    ):
        fail("checkout is not clean before validation")

    verify_integrity()
    require_prevalidation_state(read_state())
    assert_inventory()

    if not REQUEST.is_file():
        fail("explicit owner acceptance-validation request is missing")
    request = REQUEST.read_text(encoding="utf-8")
    for marker in (
        "APPROVAL: AUTHORIZE AI-001 ACCEPTANCE VALIDATION",
        "SCOPE: AI-001-AC01 through AI-001-AC06 only",
        "AI-001-T10 approval and freeze are NOT authorized by this request",
    ):
        if marker not in request:
            fail(f"acceptance-validation request is missing {marker!r}")
    if EVIDENCE.exists():
        fail(
            "AI-001 acceptance-validation evidence already exists; "
            "refusing duplicate validation"
        )


def verify_criterion(
    criterion_id: str,
    evidence: str,
    already_verified: set[str],
) -> None:
    output = controller_command(
        ["verify-criterion", criterion_id, "--evidence", evidence]
    )
    if f"VERIFIED: {criterion_id}" not in output:
        fail(f"Control Center did not verify {criterion_id}")
    verify_integrity()
    state = read_state()
    gate, _subtasks, criteria = state_indexes(state)
    if gate.get("status") != "READY_FOR_VALIDATION":
        fail(
            "gate status changed before the acceptance criteria "
            "were fully validated"
        )
    if gate.get("current_subtask") != "AI-001-T10":
        fail("current gate subtask pointer changed during criterion verification")
    for item_id, item in criteria.items():
        expected_status = (
            "VERIFIED"
            if item_id in already_verified | {criterion_id}
            else "PENDING"
        )
        if item.get("status") != expected_status:
            fail(
                f"unexpected status for {item_id} during "
                "sequential validation"
            )
        if item_id == criterion_id and item.get("evidence") != evidence:
            fail(f"controller persisted unexpected evidence for {criterion_id}")


def assert_snapshot(path: Path) -> None:
    if not re.fullmatch(
        r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json",
        path.as_posix(),
    ):
        fail(f"unexpected controller snapshot path: {path.as_posix()}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read controller snapshot {path}: {exc}")
    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    if data.get("integrity", {}).get("sha256") != calculate_hash(data):
        fail(f"controller snapshot integrity failed: {path.relative_to(ROOT)}")


def main() -> None:
    expected_sha = os.environ.get("EXPECTED_SHA", "")
    preflight(expected_sha)

    compile_count = compile_project_sources()
    focused_counts: dict[str, int] = {}
    for criterion_id, paths in CRITERION_TESTS.items():
        focused_counts[criterion_id] = run_pytest_paths(
            criterion_id,
            paths,
            MIN_FOCUSED_COUNTS[criterion_id],
        )

    entrypoint_count = run_pytest_paths(
        "AI entrypoint contract",
        ["tets/test_ai_agent_entrypoint_contract.py"],
        15,
    )
    ai_count = run_pytest_paths(
        "complete AI platform suite",
        [f"{AI_TEST_PREFIX}/{name}" for name in AI_TEST_NAMES],
        157,
    )
    acrl_count = run_pytest_paths(
        "complete ACRL suite",
        ["AUTONOMY_ENGINE/continuity/acrl"],
        1444,
    )

    # Do not mutate canonical task state until every criterion-specific and
    # full regression suite has passed against the exact triggering commit.
    assert_exact_branch(expected_sha)

    run_id = os.environ["ACTIONS_RUN_ID"]
    evidence_notes = {
        "AI-001-AC01": (
            "Provider abstraction validated through the existing ModelGateway, "
            "explicit provider/model registries, stable public exports and disabled-by-default "
            "provider behavior. Focused tests: "
            f"{focused_counts['AI-001-AC01']} passed. "
            f"Full AI suite: {ai_count}; entrypoint: {entrypoint_count}; "
            f"ACRL: {acrl_count}. In-memory compilation: {compile_count} files. "
            f"Source SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "AI-001-AC02": (
            "Authorization boundary validated through trusted-context requirements, "
            "domain-policy delegation, cross-tenant resource denial, fail-closed dependency "
            "errors and tool-call authorization. Focused tests: "
            f"{focused_counts['AI-001-AC02']} passed. "
            f"Full AI suite: {ai_count}; entrypoint: {entrypoint_count}; "
            f"ACRL: {acrl_count}. Source SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "AI-001-AC03": (
            "Tenant-scoped retrieval and rebuildable indexing primitives validated "
            "through source/request provenance, cross-tenant candidate rejection, stale-version "
            "rejection, deterministic Qdrant point IDs, idempotent upsert, version-aware "
            "replacement, tenant-boundary search and adversarial indexing regressions. "
            f"Focused tests: {focused_counts['AI-001-AC03']} passed. "
            f"Full AI suite: {ai_count}; entrypoint: {entrypoint_count}; "
            f"ACRL: {acrl_count}. Source SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "AI-001-AC04": (
            "Model-selection and cost-control behavior validated through explicit model "
            "allowlists, deterministic aliases, provider/model capability checks, durable tenant "
            "budgets, idempotent usage settlement, concurrent reservation limits, UTC quota "
            "windows and fail-closed missing pricing. "
            f"Focused tests: {focused_counts['AI-001-AC04']} passed. "
            f"Full AI suite: {ai_count}; entrypoint: {entrypoint_count}; "
            f"ACRL: {acrl_count}. Source SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "AI-001-AC05": (
            "Agent/tool execution boundary validated through registered-tool allowlists, "
            "server-side argument checks, trusted domain-policy decisions, replay protection, "
            "sensitive-mutation denial, shell/database/repository action rejection, bounded "
            "execution and disabled-by-default tool bridge. "
            f"Focused tests: {focused_counts['AI-001-AC05']} passed. "
            f"Full AI suite: {ai_count}; entrypoint: {entrypoint_count}; "
            f"ACRL: {acrl_count}. Source SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "AI-001-AC06": (
            "Fallback and observability behavior validated through configured fallback selection, "
            "explicit model-choice preservation, ambiguous primary-failure no-retry behavior, "
            "required telemetry failure handling, typed structured events and allowlisted/redacted "
            "logging. Focused tests: "
            f"{focused_counts['AI-001-AC06']} passed. "
            f"Full AI suite: {ai_count}; entrypoint: {entrypoint_count}; "
            f"ACRL: {acrl_count}. Source SHA: {expected_sha}; Actions run: {run_id}."
        ),
    }

    already_verified: set[str] = set()
    for criterion_id, evidence in evidence_notes.items():
        verify_criterion(criterion_id, evidence, already_verified)
        already_verified.add(criterion_id)

    validation_output = controller_command(["validate-gate"])
    if "GATE VALIDATED: AI-001" not in validation_output:
        fail("Control Center did not validate AI-001; approval must remain blocked")

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)
    verify_integrity()
    validated_state = read_state()
    require_validated_state(validated_state, evidence_notes)

    packet_markers = (
        "CURRENT_GATE=AI-001",
        "CURRENT_SUBTASK=AI-001-T10",
        "AI-001-T09|DONE|Run AI safety security and reliability tests",
        "AI-001-T10|READY_FOR_APPROVAL|Freeze AI platform and agents",
        "AI-001-AC01|VERIFIED|",
        "AI-001-AC02|VERIFIED|",
        "AI-001-AC03|VERIFIED|",
        "AI-001-AC04|VERIFIED|",
        "AI-001-AC05|VERIFIED|",
        "AI-001-AC06|VERIFIED|",
    )
    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in packet_markers:
            if marker not in content:
                fail(f"{path.name} lacks required current-state marker {marker!r}")

    untracked_before_evidence = sorted(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            display=False,
        ).splitlines()
    )
    snapshot_paths = [
        path
        for path in untracked_before_evidence
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json",
            path,
        )
    ]
    if len(snapshot_paths) != 7:
        fail(
            "expected seven controller snapshots (six criterion verifications "
            f"and gate validation); found {snapshot_paths}"
        )
    if set(untracked_before_evidence) != set(snapshot_paths):
        fail(
            "unexpected untracked files before evidence creation: "
            f"{untracked_before_evidence}"
        )
    for relative in snapshot_paths:
        assert_snapshot(ROOT / relative)

    evidence_path = EVIDENCE.relative_to(ROOT).as_posix()
    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    state_blob_sha = run(["git", "hash-object", str(STATE)], display=False)
    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/{os.environ['ACTIONS_REPOSITORY']}"
        f"/actions/runs/{run_id}"
    )

    evidence_lines = [
        "# AI-001 — Acceptance Criteria Validation Evidence",
        "",
        "## Authority and exact verification",
        "",
        "- Project: HOMIO / REOS",
        "- Canonical branch: `reos-development`",
        f"- Verified source commit: `{expected_sha}`",
        f"- GitHub Actions run: [{run_id}]({run_url})",
        "- State transitions: existing Control Center `verify-criterion` and `validate-gate` commands",
        "- Direct `state.json` mutation by this runner: **not performed**",
        "- T10 approval/freeze: **not performed**; explicit approval remains required",
        "- Live provider credentials and customer-facing AI: **not enabled**",
        "",
        "## Criterion-specific regression results",
        "",
    ]
    for criterion_id, count in focused_counts.items():
        evidence_lines.append(f"- {criterion_id}: **{count} passed**")
    evidence_lines.extend(
        [
            f"- AI entrypoint contract suite: **{entrypoint_count} passed**",
            f"- Full AI platform suite: **{ai_count} passed**",
            f"- Full ACRL suite: **{acrl_count} passed**",
            f"- AI and retrieval source compilation: **{compile_count} files passed**",
            "",
            "## Reviewed source and test blob SHAs",
            "",
            "| Path | Git blob SHA |",
            "|---|---|",
        ]
    )
    for relative in dict.fromkeys(SOURCE_PATHS):
        blob_sha = run(
            ["git", "rev-parse", f"{expected_sha}:{relative}"],
            display=False,
        )
        evidence_lines.append(f"| `{relative}` | `{blob_sha}` |")
    evidence_lines.extend(
        [
            "",
            "## Canonical state after validation",
            "",
            f"- State blob SHA: `{state_blob_sha}`",
            "- Canonical state integrity: `PASS`",
            "- AI-001 gate: `VALIDATED`",
            "- AI-001-T01 through AI-001-T09: `DONE`",
            "- AI-001-T10: `READY_FOR_APPROVAL`",
            "- AI-001-AC01 through AI-001-AC06: all `VERIFIED`",
            "- New gate approval or freeze: **not executed**",
            "",
            "The acceptance criteria are validated only against the verified source commit and recorded tests. "
            "This workflow deliberately stops before `approve-gate`; AI-001-T10 remains subject to explicit owner approval.",
            "",
        ]
    )
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        "\n".join(evidence_lines),
        encoding="utf-8",
        newline="\n",
    )

    untracked_after_evidence = set(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            display=False,
        ).splitlines()
    )
    expected_untracked = set(snapshot_paths) | {evidence_path}
    if untracked_after_evidence != expected_untracked:
        fail(
            "untracked allowlist mismatch after evidence: "
            f"{sorted(untracked_after_evidence)}"
        )

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }
    actual_tracked = set(
        run(["git", "diff", "--name-only"], display=False).splitlines()
    )
    if actual_tracked != expected_tracked:
        fail(f"unexpected tracked changes: {sorted(actual_tracked)}")
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"])

    staged_paths = sorted(expected_tracked | expected_untracked)
    run(["git", "add", "--", *staged_paths], capture=False)
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"])
    actual_staged = set(
        run(["git", "diff", "--cached", "--name-only"], display=False).splitlines()
    )
    if actual_staged != set(staged_paths):
        fail(f"staged path allowlist mismatch: {sorted(actual_staged)}")

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            "chore(control-center): validate AI-001 acceptance criteria",
        ],
        capture=False,
    )
    transition_commit = run(["git", "rev-parse", "HEAD"], display=False)
    if run(["git", "rev-parse", "HEAD^"], display=False) != expected_sha:
        fail("validation transition commit parent is not the verified source SHA")

    run(
        ["git", "fetch", "--no-tags", "origin", "refs/heads/reos-development"],
        capture=False,
    )
    if run(["git", "rev-parse", "FETCH_HEAD"], display=False) != expected_sha:
        fail("canonical branch moved during validation; refusing to publish state")
    run(["git", "push", "origin", "HEAD:refs/heads/reos-development"], capture=False)
    run(
        ["git", "fetch", "--no-tags", "origin", "refs/heads/reos-development"],
        capture=False,
    )
    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"], display=False)
    if remote_sha != transition_commit:
        fail("canonical remote readback differs from validation transition commit")

    readback_path = (
        Path(os.environ["RUNNER_TEMP"]) / "ai001-validation-state-readback.json"
    )
    readback_path.write_bytes(
        subprocess.check_output(
            ["git", "show", f"{remote_sha}:REOS_CONTROL_CENTER/data/state.json"],
            cwd=ROOT,
        )
    )
    try:
        remote_state = json.loads(readback_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"remote canonical state could not be parsed: {exc}")
    if remote_state.get("integrity", {}).get("sha256") != calculate_hash(remote_state):
        fail("remote canonical state integrity is invalid")
    require_validated_state(remote_state, evidence_notes)

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        remote_content = run(
            ["git", "show", f"{remote_sha}:{relative}"],
            display=False,
        )
        for marker in packet_markers:
            if marker not in remote_content:
                fail(f"remote {relative} lacks {marker!r}")

    remote_evidence = run(
        ["git", "show", f"{remote_sha}:{evidence_path}"],
        display=False,
    )
    for marker in (
        expected_sha,
        run_id,
        "AI-001 gate: `VALIDATED`",
        "AI-001-T10: `READY_FOR_APPROVAL`",
        "AI-001-AC01 through AI-001-AC06: all `VERIFIED`",
        str(entrypoint_count),
        str(ai_count),
        str(acrl_count),
    ):
        if marker not in remote_evidence:
            fail(f"remote acceptance evidence is missing {marker!r}")

    print(f"AI001_AC01_TEST_COUNT={focused_counts['AI-001-AC01']}")
    print(f"AI001_AC02_TEST_COUNT={focused_counts['AI-001-AC02']}")
    print(f"AI001_AC03_TEST_COUNT={focused_counts['AI-001-AC03']}")
    print(f"AI001_AC04_TEST_COUNT={focused_counts['AI-001-AC04']}")
    print(f"AI001_AC05_TEST_COUNT={focused_counts['AI-001-AC05']}")
    print(f"AI001_AC06_TEST_COUNT={focused_counts['AI-001-AC06']}")
    print(f"AI_ENTRYPOINT_TEST_COUNT={entrypoint_count}")
    print(f"AI_PLATFORM_TEST_COUNT={ai_count}")
    print(f"ACRL_TEST_COUNT={acrl_count}")
    print(f"AI_AND_RETRIEVAL_SOURCE_COMPILE_COUNT={compile_count}")
    print(f"VALIDATION_TRANSITION_COMMIT={transition_commit}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("AI-001 ACCEPTANCE VALIDATION AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
