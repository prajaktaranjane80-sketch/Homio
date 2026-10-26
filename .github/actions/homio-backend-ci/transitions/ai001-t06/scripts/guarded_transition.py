from __future__ import annotations

import json
import os
import re
import shutil
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
ENTRYPOINT_TEST = CONTROL / "tets/test_ai_agent_entrypoint_contract.py"
ACRL_ROOT = CONTROL / "AUTONOMY_ENGINE/continuity/acrl"
REQUEST = CONTROL / "evidence/AI-001/T06-transition-request.md"
EVIDENCE = CONTROL / "evidence/AI-001/T06-authorization-tenant-evidence.md"

AI_TEST_NAMES = (
    "test_contracts.py",
    "test_model_gateway.py",
    "test_model_registry.py",
    "test_public_contract_stability.py",
    "test_embeddings_retrieval.py",
    "test_retrieval_and_rag.py",
    "test_agent_tool_boundaries.py",
    "test_authorization_tenant_isolation.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"AI-001-T06 TRANSITION BLOCKED: {message}")


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
        fail(
            f"command failed ({result.returncode}): "
            f"{' '.join(command)}"
        )
    return output.strip()


def run_pytest(label: str, paths: list[str]) -> int:
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
    matches = re.findall(r"(\d+) passed(?:\s|,|$)", output)
    if not matches or int(matches[-1]) < 1:
        fail(f"{label}: no positive pytest pass count found")
    if re.search(r"\b\d+ failed\b", output):
        fail(f"{label}: pytest reported failures")
    count = int(matches[-1])
    print(f"{label.upper().replace(' ', '_')}_PASSED={count}")
    return count


def read_state() -> dict:
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"canonical state cannot be read: {exc}")
    if not isinstance(state, dict):
        fail("canonical state root is not an object")
    return state


def validate_state(state: dict, *, transitioned: bool) -> None:
    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get("AI-001")
    if not isinstance(gate, dict):
        fail("canonical AI-001 gate is missing")
    if execution.get("current_gate") != "AI-001":
        fail("canonical current gate is no longer AI-001")
    if gate.get("status") != "CURRENT":
        fail("AI-001 gate is not CURRENT")

    subtasks = {
        item.get("id"): item
        for item in gate.get("subtasks", [])
        if isinstance(item, dict)
    }
    expected = {
        "AI-001-T01": "DONE",
        "AI-001-T02": "DONE",
        "AI-001-T03": "DONE",
        "AI-001-T04": "DONE",
        "AI-001-T05": "DONE",
        "AI-001-T06": "DONE" if transitioned else "CURRENT",
        "AI-001-T07": "CURRENT" if transitioned else "PENDING",
        "AI-001-T08": "PENDING",
        "AI-001-T09": "PENDING",
        "AI-001-T10": "PENDING",
    }
    current = "AI-001-T07" if transitioned else "AI-001-T06"
    for task_id, wanted in expected.items():
        actual = subtasks.get(task_id, {}).get("status")
        if actual != wanted:
            fail(f"{task_id} must be {wanted}; found {actual!r}")

    if gate.get("current_subtask") != current:
        fail("gate current_subtask does not match the guarded transition")
    if execution.get("current_subtask") != current:
        fail("execution current_subtask does not match the gate")

    criteria = {
        item.get("id"): item.get("status")
        for item in gate.get("criteria_state", [])
        if isinstance(item, dict)
    }
    expected_criteria = {
        f"AI-001-AC{i:02d}": "PENDING"
        for i in range(1, 7)
    }
    if criteria != expected_criteria:
        fail("AI-001 acceptance criteria changed; T06 must not bulk-verify them")
    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution mode is no longer CONTROL_CENTER_DRIVEN")


def assert_exact_branch(expected_sha: str) -> None:
    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checked-out HEAD differs from the expected verified SHA")
    run(
        [
            "git", "fetch", "--no-tags", "origin",
            "refs/heads/reos-development",
        ],
        capture=False,
    )
    if run(["git", "rev-parse", "FETCH_HEAD"]) != expected_sha:
        fail("canonical branch moved; refusing a stale transition")


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
    )
    if original.count(b"\n") > 0 and original.count(b"\n") == original.count(b"\r\n"):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def compile_ai_sources() -> int:
    sources = sorted(
        path for path in AI_ROOT.rglob("*.py") if path.is_file()
    )
    if not sources:
        fail("AI package source inventory is empty")
    for source in sources:
        try:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            fail(f"AI source compilation failed for {source}: {exc}")
    print(f"AI_PACKAGE_SOURCE_COMPILE_PASS={len(sources)}")
    return len(sources)


def clean_ai_bytecode() -> int:
    caches = sorted(
        (path for path in AI_ROOT.rglob("__pycache__") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    removed = 0
    for path in caches:
        if path.exists():
            try:
                shutil.rmtree(path)
            except OSError as exc:
                fail(f"cannot remove generated bytecode {path}: {exc}")
            removed += 1
    print(f"AI_PACKAGE_BYTECODE_CLEANUP_REMOVED_DIRS={removed}")
    return removed


def assert_test_inventory() -> None:
    required = [
        AI_ROOT / "__init__.py",
        AI_ROOT / "contracts.py",
        AI_ROOT / "errors.py",
        AI_ROOT / "model_gateway.py",
        AI_ROOT / "model_registry.py",
        AI_ROOT / "ports.py",
        AI_ROOT / "settings.py",
        AI_ROOT / "embeddings.py",
        AI_ROOT / "retrieval_adapter.py",
        AI_ROOT / "prompt_templates.py",
        AI_ROOT / "rag_pipeline.py",
        AI_ROOT / "agent_runtime.py",
        AI_ROOT / "tool_bridge.py",
        AI_ROOT / "authorization.py",
        ENTRYPOINT_TEST,
        *(AI_TESTS / name for name in AI_TEST_NAMES),
    ]
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in required
        if not path.is_file()
    ]
    if missing:
        fail(f"required AI source/test files are missing: {missing}")
    for duplicate in (
        AI_ROOT / "test_contracts.py",
        AI_ROOT / "test_model_gateway.py",
    ):
        if duplicate.exists():
            fail(f"obsolete duplicate AI test exists: {duplicate.relative_to(ROOT)}")


def assert_controller_snapshot(snapshot: Path) -> None:
    if not re.fullmatch(
        r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json",
        snapshot.as_posix(),
    ):
        fail(f"unexpected controller snapshot path: {snapshot}")
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash
    if data.get("integrity", {}).get("sha256") != calculate_hash(data):
        fail("controller-created snapshot has invalid integrity")


def main() -> None:
    required_env = (
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_SERVER_URL",
        "ACTIONS_REPOSITORY",
        "GITHUB_ACTOR",
        "GITHUB_REF",
        "RUNNER_TEMP",
    )
    missing = [key for key in required_env if not os.environ.get(key)]
    if missing:
        fail(f"required environment values are missing: {missing}")
    if os.environ["GITHUB_ACTOR"] != "prajaktaranjane80-sketch":
        fail("only the repository owner may authorize this transition")
    if os.environ["GITHUB_REF"] != "refs/heads/reos-development":
        fail("only reos-development is permitted")

    expected_sha = os.environ["EXPECTED_SHA"]
    if expected_sha != os.environ["VERIFIED_CODE_SHA"]:
        fail("expected and verified code SHAs differ")
    subject = run(["git", "log", "-1", "--pretty=%s"])
    if not subject.startswith("[CONTROL-CENTER-COMPLETE-AI-001-T06]"):
        fail("the guarded T06 completion commit prefix is missing")

    assert_exact_branch(expected_sha)
    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        fail("checkout is not clean before transition")
    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )
    validate_state(read_state(), transitioned=False)
    assert_test_inventory()

    if not REQUEST.is_file():
        fail("the explicit owner T06 transition request is missing")
    request_text = REQUEST.read_text(encoding="utf-8")
    if "APPROVAL: AUTHORIZE AI-001-T06 COMPLETION" not in request_text:
        fail("the T06 request lacks its exact authorization statement")
    if "SCOPE: AI-001-T06 only" not in request_text:
        fail("the T06 request is not strictly scoped to T06")
    if EVIDENCE.exists():
        fail("T06 evidence already exists; refusing duplicate completion")

    compile_count = compile_ai_sources()
    entrypoint_count = run_pytest(
        "AI entrypoint contract",
        [str(ENTRYPOINT_TEST)],
    )
    ai_count = run_pytest(
        "AI authorization tenant isolation and tool boundaries",
        [str(AI_TESTS / name) for name in AI_TEST_NAMES],
    )
    acrl_count = run_pytest(
        "complete ACRL suite",
        [str(ACRL_ROOT)],
    )
    assert_exact_branch(expected_sha)

    # Canonical state changes only through the existing Control Center command.
    import REOS_CONTROL_CENTER.reos_control_center as controller
    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")
    note = (
        "AI-001-T06 completed through the existing Control Center after "
        f"AI authorization, tenant-isolation and tool-boundary tests ({ai_count} passed), "
        f"entrypoint contract tests ({entrypoint_count} passed), and "
        f"complete ACRL regressions ({acrl_count} passed) succeeded in "
        f"Actions run {os.environ['ACTIONS_RUN_ID']} for verified commit "
        f"{expected_sha}. Only T06 is completed. AI-001-AC01 through "
        "AI-001-AC06 remain PENDING; this transition does not claim gate-level acceptance."
    )
    sys.argv = [
        "reos_control_center.py",
        "complete-subtask",
        "AI-001-T06",
        "--note",
        note,
    ]
    controller.main()

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)

    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )
    transitioned_state = read_state()
    validate_state(transitioned_state, transitioned=True)
    if transitioned_state.get("session", {}).get("last_handoff") != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt":
        fail("canonical handoff path is not repository-relative")

    markers = (
        "CURRENT_SUBTASK=AI-001-T07",
        "AI-001-T06|DONE|Implement AI authorization and tenant isolation",
        "AI-001-T07|CURRENT|Implement cost controls and usage tracking",
    )
    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                fail(f"{path.name} is missing expected marker {marker!r}")

    clean_ai_bytecode()
    untracked = sorted(
        run(["git", "ls-files", "--others", "--exclude-standard"]).splitlines()
    )
    if len(untracked) != 1:
        fail(f"expected one controller snapshot before evidence; found {untracked}")
    snapshot = Path(untracked[0])
    assert_controller_snapshot(snapshot)

    source_paths = (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/authorization.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tool_bridge.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_agent_tool_boundaries.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_authorization_tenant_isolation.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_retrieval_and_rag.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_embeddings_retrieval.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py",
        "REOS_CONTROL_CENTER/tets/test_ai_agent_entrypoint_contract.py",
        REQUEST.relative_to(ROOT).as_posix(),
    )
    source_rows = []
    for relative in source_paths:
        blob_sha = run(
            ["git", "rev-parse", f"{expected_sha}:{relative}"],
            display=False,
        )
        source_rows.append(f"| `{relative}` | `{blob_sha}` |")

    state_blob_sha = run(["git", "hash-object", str(STATE)], display=False)
    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/"
        f"{os.environ['ACTIONS_RUN_ID']}"
    )
    evidence = f"""# AI-001-T06 — AI Authorization and Tenant Isolation Evidence

## Authority and exact verification

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Verified code commit: `{expected_sha}`
- GitHub Actions run: [{os.environ['ACTIONS_RUN_ID']}]({run_url})
- Completion route: existing Control Center `complete-subtask`
- Manual `state.json` editing: **not performed**
- Live identity provider, tenant database, and production business execution: **not enabled**

## Test results on the verified commit

- AI entrypoint contract tests: **{entrypoint_count} passed**
- AI platform authorization, tenant-isolation, retrieval/RAG and tool-boundary tests: **{ai_count} passed**
- Complete ACRL regression suite: **{acrl_count} passed**
- AI package compilation: **PASS** ({compile_count} Python sources compiled in memory)
- Tests cover missing/untrusted context, invalid operations/tool names, policy service errors, cross-tenant resource denial, malformed decisions, tool authorization denial, and tool-argument tenant override.
- Trusted-context and domain-policy dependencies are injected ports tested with deterministic doubles. They are not represented as live production services.

## Scope and integration boundary

The AI platform exposes authorization entry points for model requests, tenant-scoped retrieval checks, and agent tool calls. Decisions are delegated to injected trusted-context verification and the domain authorization owner. The ToolBridge callback accepts only literal `True`; denied decisions, exceptions, untrusted contexts, and mismatched tool proposals fail closed before gateway execution.

This subtask adds the AI boundary adapter without replacing canonical identity, tenant, membership, or domain-policy ownership. Live provider credentials, persisted tenant membership, and production actions remain disabled. Gate-level acceptance criteria stay pending and are not bulk-verified by this transition.

## Verified source blob SHAs

| File | Git blob SHA |
|---|---|
{chr(10).join(source_rows)}

## Canonical state after controller transition

- State blob SHA before publishing this evidence: `{state_blob_sha}`
- AI-001-T01 through AI-001-T06: `DONE`
- AI-001-T07: `CURRENT`
- AI-001-T08 through AI-001-T10: `PENDING`
- AI-001-AC01 through AI-001-AC06: `PENDING`

This record closes AI-001-T06 only. It does not claim the AI-001 gate or acceptance criteria are complete, and it does not authorize production/customer-facing AI execution.
"""
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(evidence, encoding="utf-8", newline="\n")

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }
    actual_tracked = set(run(["git", "diff", "--name-only"]).splitlines())
    if actual_tracked != expected_tracked:
        fail(f"unexpected tracked changes: {sorted(actual_tracked)}")
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"])

    expected_untracked = {
        EVIDENCE.relative_to(ROOT).as_posix(),
        snapshot.as_posix(),
    }
    actual_untracked = set(
        run(["git", "ls-files", "--others", "--exclude-standard"]).splitlines()
    )
    if actual_untracked != expected_untracked:
        fail(f"unexpected untracked files: {sorted(actual_untracked)}")

    staged = sorted(expected_tracked | expected_untracked)
    run(["git", "add", "--", *staged])
    run(
        ["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"]
    )
    actual_staged = set(run(["git", "diff", "--cached", "--name-only"]).splitlines())
    if actual_staged != set(staged):
        fail("staged path allowlist mismatch")

    run(
        [
            "git", "-c", "user.name=github-actions[bot]",
            "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-m",
            "chore(control-center): complete AI-001-T06 via controller",
        ],
        capture=False,
    )
    transition_sha = run(["git", "rev-parse", "HEAD"])
    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("transition commit parent is not the tested code commit")

    run(
        ["git", "push", "origin", "HEAD:refs/heads/reos-development"],
        capture=False,
    )
    run(
        [
            "git", "fetch", "--no-tags", "origin",
            "refs/heads/reos-development",
        ],
        capture=False,
    )
    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"])
    if remote_sha != transition_sha:
        fail("canonical branch readback differs from transition commit")

    readback_path = Path(os.environ["RUNNER_TEMP"]) / "ai001-t06-state-readback.json"
    readback_path.write_bytes(
        subprocess.check_output(
            ["git", "show", f"{remote_sha}:REOS_CONTROL_CENTER/data/state.json"],
            cwd=ROOT,
        )
    )
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash
    if readback.get("integrity", {}).get("sha256") != calculate_hash(readback):
        fail("remote canonical state integrity is invalid")
    validate_state(readback, transitioned=True)

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        remote_content = run(
            ["git", "show", f"{remote_sha}:{relative}"],
            display=False,
        )
        for marker in markers:
            if marker not in remote_content:
                fail(f"remote {relative} lacks {marker!r}")

    remote_evidence = run(
        [
            "git", "show",
            f"{remote_sha}:{EVIDENCE.relative_to(ROOT).as_posix()}",
        ],
        display=False,
    )
    if (
        expected_sha not in remote_evidence
        or os.environ["ACTIONS_RUN_ID"] not in remote_evidence
        or f"**{ai_count} passed**" not in remote_evidence
    ):
        fail("remote evidence lacks the verified SHA, run ID, or test result")

    print(f"AI_ENTRYPOINT_TEST_COUNT={entrypoint_count}")
    print(f"AI_AUTHORIZATION_TENANT_TEST_COUNT={ai_count}")
    print(f"ACRL_TEST_COUNT={acrl_count}")
    print(f"AI_SOURCE_COMPILE_COUNT={compile_count}")
    print(f"TRANSITION_COMMIT={transition_sha}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("AI-001-T06 TRANSITION AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
