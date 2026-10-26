from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data/state.json"
PACKET = CONTROL / "packets/NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"

AI_ROOT = CONTROL / "AUTONOMY_ENGINE/ai_platform"
AI_TESTS = AI_ROOT / "tests"
ENTRYPOINT_TEST = CONTROL / "tets/test_ai_agent_entrypoint_contract.py"
ACRL_ROOT = CONTROL / "AUTONOMY_ENGINE/continuity/acrl"
COMPILE_SCRIPT = (
    ROOT
    / ".github/actions/homio-backend-ci/verification/scripts/"
    "compile_and_contracts.sh"
)

REQUEST = CONTROL / "evidence/AI-001/T01-transition-request.md"
EVIDENCE = CONTROL / "evidence/AI-001/T01-gateway-ci-evidence.md"


def fail(message: str) -> None:
    raise SystemExit(f"AI-001-T01 TRANSITION BLOCKED: {message}")


def run(
    command: list[str],
    *,
    capture: bool = True,
    display: bool = True,
    cwd: Path | None = None,
) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    output = (completed.stdout or "") if capture else ""

    if output and display:
        print(output, end="" if output.endswith("\n") else "\n")

    if completed.returncode:
        fail(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}"
        )

    return output.strip()


def pytest_count(output: str, label: str) -> int:
    matches = re.findall(r"(\d+) passed(?:\s|,|$)", output)

    if not matches or int(matches[-1]) < 1:
        fail(f"{label}: no positive pytest pass count found")

    if re.search(r"\b\d+ failed\b", output):
        fail(f"{label}: pytest reported failures")

    return int(matches[-1])


def run_pytest(label: str, paths: list[str]) -> int:
    # Match the existing CI's import root: REOS_CONTROL_CENTER.
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
    count = pytest_count(output, label)
    print(f"{label.upper().replace(' ', '_')}_PASSED={count}")
    return count


def read_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8"))


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
    }

    expected = {
        f"AI-001-T{i:02d}": "PENDING"
        for i in range(3, 11)
    }

    if transitioned:
        expected["AI-001-T01"] = "DONE"
        expected["AI-001-T02"] = "CURRENT"
        wanted_current = "AI-001-T02"
    else:
        expected["AI-001-T01"] = "CURRENT"
        expected["AI-001-T02"] = "PENDING"
        wanted_current = "AI-001-T01"

    for subtask_id, expected_status in expected.items():
        actual = subtasks.get(subtask_id, {}).get("status")
        if actual != expected_status:
            fail(
                f"{subtask_id} must be {expected_status}; "
                f"found {actual!r}"
            )

    if gate.get("current_subtask") != wanted_current:
        fail("gate current_subtask does not match the guarded transition")

    if execution.get("current_subtask") != wanted_current:
        fail("execution current_subtask does not match the gate")

    criteria = {
        item.get("id"): item.get("status")
        for item in gate.get("criteria_state", [])
    }
    expected_criteria = {
        f"AI-001-AC{i:02d}": "PENDING"
        for i in range(1, 7)
    }

    if criteria != expected_criteria:
        fail(
            "AI-001 acceptance criteria changed; "
            "T01 must not bulk-verify them"
        )

    if (
        not transitioned
        and execution.get("status") != "CONTROL_CENTER_DRIVEN"
    ):
        fail("execution mode is no longer CONTROL_CENTER_DRIVEN")


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


def assert_canonical_test_layout() -> None:
    required = (
        AI_ROOT / "__init__.py",
        AI_ROOT / "contracts.py",
        AI_ROOT / "errors.py",
        AI_ROOT / "model_gateway.py",
        AI_ROOT / "ports.py",
        AI_ROOT / "settings.py",
        AI_TESTS / "test_contracts.py",
        AI_TESTS / "test_model_gateway.py",
        AI_TESTS / "test_public_contract_stability.py",
        ENTRYPOINT_TEST,
        COMPILE_SCRIPT,
    )

    for path in required:
        if not path.is_file():
            fail(
                "required source/test file is missing: "
                f"{path.relative_to(ROOT)}"
            )

    for duplicate in (
        AI_ROOT / "test_contracts.py",
        AI_ROOT / "test_model_gateway.py",
    ):
        if duplicate.exists():
            fail(
                "obsolete duplicate test file exists: "
                f"{duplicate.relative_to(ROOT)}"
            )


def assert_exact_branch(expected_sha: str) -> None:
    actual = run(["git", "rev-parse", "HEAD"])
    if actual != expected_sha:
        fail("checked-out HEAD differs from the expected verified SHA")

    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            "refs/heads/reos-development",
        ],
        capture=False,
    )
    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"])

    if remote_sha != expected_sha:
        fail("canonical branch moved; refusing a stale transition")


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

    missing = [
        key
        for key in required_env
        if not os.environ.get(key)
    ]
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
    required_prefix = "[CONTROL-CENTER-COMPLETE-AI-001-T01]"

    if not subject.startswith(required_prefix):
        fail("the guarded completion commit prefix is missing")

    assert_exact_branch(expected_sha)

    if run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    ):
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
    assert_canonical_test_layout()

    if not REQUEST.is_file():
        fail("the explicit owner transition request is missing")

    request_content = REQUEST.read_text(encoding="utf-8")

    if "APPROVAL: AUTHORIZE AI-001-T01 COMPLETION" not in request_content:
        fail("the request does not contain the exact authorization statement")

    if "SCOPE: AI-001-T01 only" not in request_content:
        fail("the request must be restricted to AI-001-T01")

    if EVIDENCE.exists():
        fail("T01 evidence already exists; refusing duplicate completion")

    # Compile the AI gateway package. Do not enable any live provider.
    run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(AI_ROOT.relative_to(ROOT)),
        ],
        capture=False,
    )

    entrypoint_count = run_pytest(
        "AI entrypoint contract",
        [str(ENTRYPOINT_TEST)],
    )

    ai_count = run_pytest(
        "AI gateway package",
        [
            str(AI_TESTS / "test_contracts.py"),
            str(AI_TESTS / "test_model_gateway.py"),
            str(AI_TESTS / "test_public_contract_stability.py"),
        ],
    )

    acrl_count = run_pytest(
        "complete ACRL suite",
        [str(ACRL_ROOT)],
    )

    # Stop if the branch changed while regressions were running.
    assert_exact_branch(expected_sha)

    # The canonical controller owns state changes.
    # This script must never write state.json directly.
    import REOS_CONTROL_CENTER.reos_control_center as controller

    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")

    note = (
        "AI-001-T01 completed through the existing Control Center after "
        f"AI gateway tests ({ai_count} passed), entrypoint contract tests "
        f"({entrypoint_count} passed), and complete ACRL regressions "
        f"({acrl_count} passed) succeeded in Actions run "
        f"{os.environ['ACTIONS_RUN_ID']} for verified commit "
        f"{expected_sha}. Only T01 is completed. "
        "AI-001-AC01 through AI-001-AC06 remain PENDING; this transition "
        "does not claim gate-level acceptance."
    )

    sys.argv = [
        "reos_control_center.py",
        "complete-subtask",
        "AI-001-T01",
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

    if (
        transitioned_state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is not repository-relative")

    markers = (
        "CURRENT_SUBTASK=AI-001-T02",
        "AI-001-T01|DONE|Implement AI Gateway",
        "AI-001-T02|CURRENT|Implement provider and model registry",
    )

    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                fail(f"{path.name} is missing expected marker {marker!r}")

    # Before evidence creation, only the controller's snapshot may be untracked.
    untracked = sorted(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
    )

    if len(untracked) != 1:
        fail(f"expected one controller snapshot; found {untracked}")

    snapshot = Path(untracked[0])

    if not re.fullmatch(
        r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json",
        snapshot.as_posix(),
    ):
        fail(f"unexpected controller snapshot path: {snapshot}")

    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    snapshot_data = json.loads(snapshot.read_text(encoding="utf-8"))

    if (
        snapshot_data.get("integrity", {}).get("sha256")
        != calculate_hash(snapshot_data)
    ):
        fail("controller-created snapshot has invalid integrity")

    source_paths = (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/__init__.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/contracts.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/errors.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_gateway.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/ports.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/settings.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py",
        ".github/actions/homio-backend-ci/verification/scripts/compile_and_contracts.sh",
        REQUEST.relative_to(ROOT).as_posix(),
    )

    source_rows = []
    for relative in source_paths:
        blob_sha = run(
            ["git", "rev-parse", f"{expected_sha}:{relative}"],
            display=False,
        )
        source_rows.append(f"| `{relative}` | `{blob_sha}` |")

    state_blob_sha = run(
        ["git", "hash-object", str(STATE)],
        display=False,
    )

    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/"
        f"{os.environ['ACTIONS_RUN_ID']}"
    )

    evidence = f"""# AI-001-T01 — AI Gateway Completion Evidence

## Authority and exact verification

- Project: HOMIO / REOS
- Canonical branch: `reos-development`
- Verified code commit: `{expected_sha}`
- GitHub Actions run: [{os.environ['ACTIONS_RUN_ID']}]({run_url})
- Completion route: existing Control Center `complete-subtask`
- Manual `state.json` editing: **not performed**

## Test results on the verified commit

- AI entrypoint contract tests: **{entrypoint_count} passed**
- Canonical AI gateway package tests: **{ai_count} passed**
- Complete ACRL suite: **{acrl_count} passed**
- AI package compilation: **PASS**
- Obsolete root-level AI test duplicates: **absent**

## Verified source blob SHAs

| File | Git blob SHA |
|---|---|
{chr(10).join(source_rows)}

## Canonical state after controller transition

- State blob SHA before publishing this evidence: `{state_blob_sha}`
- AI-001-T01: `DONE`
- AI-001-T02: `CURRENT`
- AI-001-AC01: `PENDING`
- AI-001-AC02: `PENDING`
- AI-001-AC03: `PENDING`
- AI-001-AC04: `PENDING`
- AI-001-AC05: `PENDING`
- AI-001-AC06: `PENDING`

This record closes the AI Gateway subtask only. It does not claim the AI-001 gate, its six acceptance criteria, live provider integration, or production readiness are complete.
"""

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(evidence, encoding="utf-8", newline="\n")

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }

    actual_tracked = set(
        run(["git", "diff", "--name-only"]).splitlines()
    )

    if actual_tracked != expected_tracked:
        fail(f"unexpected tracked changes: {sorted(actual_tracked)}")

    run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "diff",
            "--check",
        ]
    )

    expected_untracked = {
        EVIDENCE.relative_to(ROOT).as_posix(),
        snapshot.as_posix(),
    }

    actual_untracked = set(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
    )

    if actual_untracked != expected_untracked:
        fail(f"unexpected untracked files: {sorted(actual_untracked)}")

    staged = sorted(expected_tracked | expected_untracked)

    run(["git", "add", "--", *staged])
    run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "diff",
            "--cached",
            "--check",
        ]
    )

    actual_staged = set(
        run(["git", "diff", "--cached", "--name-only"]).splitlines()
    )

    if actual_staged != set(staged):
        fail("staged path allowlist mismatch")

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            "chore(control-center): complete AI-001-T01 via controller",
        ],
        capture=False,
    )

    transition_sha = run(["git", "rev-parse", "HEAD"])

    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("transition commit parent is not the tested code commit")

    run(
        [
            "git",
            "push",
            "origin",
            "HEAD:refs/heads/reos-development",
        ],
        capture=False,
    )

    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            "refs/heads/reos-development",
        ],
        capture=False,
    )

    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"])

    if remote_sha != transition_sha:
        fail("canonical branch readback differs from transition commit")

    readback_path = (
        Path(os.environ["RUNNER_TEMP"]) / "ai001-state-readback.json"
    )

    readback_path.write_bytes(
        subprocess.check_output(
            [
                "git",
                "show",
                f"{remote_sha}:REOS_CONTROL_CENTER/data/state.json",
            ],
            cwd=ROOT,
        )
    )

    readback = json.loads(readback_path.read_text(encoding="utf-8"))

    if (
        readback.get("integrity", {}).get("sha256")
        != calculate_hash(readback)
    ):
        fail("remote canonical state integrity is invalid")

    validate_state(readback, transitioned=True)

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        content = run(
            ["git", "show", f"{remote_sha}:{relative}"],
            display=False,
        )
        for marker in markers:
            if marker not in content:
                fail(f"remote {relative} lacks {marker!r}")

    remote_evidence = run(
        [
            "git",
            "show",
            f"{remote_sha}:{EVIDENCE.relative_to(ROOT).as_posix()}",
        ],
        display=False,
    )

    if (
        expected_sha not in remote_evidence
        or os.environ["ACTIONS_RUN_ID"] not in remote_evidence
        or f"**{ai_count} passed**" not in remote_evidence
    ):
        fail("remote evidence is missing its code SHA, run ID, or test result")

    print(f"AI_ENTRYPOINT_TEST_COUNT={entrypoint_count}")
    print(f"AI_GATEWAY_TEST_COUNT={ai_count}")
    print(f"ACRL_TEST_COUNT={acrl_count}")
    print(f"TRANSITION_COMMIT={transition_sha}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("AI-001-T01 TRANSITION AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
