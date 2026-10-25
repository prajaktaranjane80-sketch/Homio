
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
SHARED = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SHARED))
os.chdir(ROOT)

from transition_contract import (  # noqa: E402
    read_canonical_state,
    require_core008_criteria_baseline,
    state_indexes,
)

CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data/state.json"
PACKET = CONTROL / "packets/NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"
FINANCIAL = CONTROL / "AUTONOMY_ENGINE/core/commission_financial"
ACRL = CONTROL / "AUTONOMY_ENGINE/continuity/acrl"
EVIDENCE = (
    CONTROL
    / "evidence/CORE-008/T08-precision-concurrency-ci-evidence.md"
)

FOCUSED_TESTS = (
    "test_core008_t01_financial_domain.py",
    "test_core008_t01_financial_ledger_boundary.py",
    "test_core008_t03_allocation_participants.py",
    "test_core008_t04_optimistic_concurrency.py",
    "test_core008_t04_reconciliation_replay.py",
    "test_core008_t13_concurrency_security_reos.py",
    "test_core008_t13_financial_regression.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"T08 TRANSITION BLOCKED: {message}")


def run(
    command: list[str],
    *,
    capture: bool = True,
    check: bool = True,
) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    output = (result.stdout or "") if capture else ""
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    if check and result.returncode:
        fail(f"command failed ({result.returncode}): {' '.join(command)}")
    return output.strip()


def pytest_count(output: str, label: str) -> int:
    matches = re.findall(r"(\d+)\s+passed(?:\s|$)", output)
    if not matches or int(matches[-1]) < 1:
        fail(f"{label}: no positive pytest pass count found")
    if re.search(r"\b\d+\s+failed\b", output):
        fail(f"{label}: pytest reported failures")
    return int(matches[-1])


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
    )
    if original.count(b"\n") > 0 and original.count(b"\n") == original.count(b"\r\n"):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def check_state(
    state: dict,
    *,
    expected_t08: str,
    expected_t09: str,
) -> None:
    execution = state.get("execution", {})
    gate, subtasks, _criteria = state_indexes(state)
    require_core008_criteria_baseline(state)

    if execution.get("current_gate") != "CORE-008":
        fail("canonical current gate is not CORE-008")
    if gate.get("status") != "CURRENT":
        fail("CORE-008 gate is not CURRENT")
    if execution.get("current_subtask") != f"CORE-008-T{ '08' if expected_t08 == 'CURRENT' else '09' }":
        fail("execution.current_subtask disagrees with expected T08/T09 state")
    if subtasks.get("CORE-008-T07", {}).get("status") != "DONE":
        fail("T07 is not DONE")
    if subtasks.get("CORE-008-T08", {}).get("status") != expected_t08:
        fail(f"T08 must be {expected_t08}")
    if subtasks.get("CORE-008-T09", {}).get("status") != expected_t09:
        fail(f"T09 must be {expected_t09}")


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
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        fail(f"missing environment values: {missing}")

    if os.environ["GITHUB_ACTOR"] != "prajaktaranjane80-sketch":
        fail("only the repository owner may authorize this transition")
    if os.environ["GITHUB_REF"] != "refs/heads/reos-development":
        fail("only reos-development is permitted")
    if os.environ["EXPECTED_SHA"] != os.environ["VERIFIED_CODE_SHA"]:
        fail("expected and verified code SHAs differ")

    expected_sha = os.environ["EXPECTED_SHA"]
    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checked-out commit does not match EXPECTED_SHA")

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
    if run(["git", "rev-parse", "FETCH_HEAD"]) != expected_sha:
        fail("canonical branch moved; refusing a stale transition")

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
    state = read_canonical_state()
    check_state(state, expected_t08="CURRENT", expected_t09="PENDING")

    if EVIDENCE.exists():
        fail("T08 evidence already exists; refusing duplicate completion")

    for filename in FOCUSED_TESTS:
        path = FINANCIAL / filename
        if not path.is_file():
            fail(f"focused test is missing: {path.relative_to(ROOT)}")

    focused_command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        *[str((FINANCIAL / name).relative_to(ROOT)) for name in FOCUSED_TESTS],
    ]
    focused_output = run(focused_command)
    focused_count = pytest_count(focused_output, "focused precision/concurrency suite")

    financial_output = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(FINANCIAL.relative_to(ROOT)),
        ]
    )
    financial_count = pytest_count(financial_output, "full financial suite")

    acrl_output = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(ACRL.relative_to(ROOT)),
        ]
    )
    acrl_count = pytest_count(acrl_output, "complete ACRL suite")

    import REOS_CONTROL_CENTER.reos_control_center as controller

    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")
    note = (
        "CORE-008-T08 completed through the existing Control Center after "
        f"focused precision/concurrency tests ({focused_count} passed), "
        f"full financial regressions ({financial_count} passed), and full "
        f"ACRL regressions ({acrl_count} passed) succeeded in Actions run "
        f"{os.environ['ACTIONS_RUN_ID']} for verified code commit {expected_sha}. "
        "CORE-008-AC01, AC04, AC05, and AC06 remain PENDING; this subtask "
        "transition does not bulk-verify acceptance criteria."
    )
    sys.argv = [
        "reos_control_center.py",
        "complete-subtask",
        "CORE-008-T08",
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
    state = read_canonical_state()
    check_state(state, expected_t08="DONE", expected_t09="CURRENT")

    if (
        state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is not repository-relative")

    markers = (
        "CURRENT_SUBTASK=CORE-008-T09",
        "CORE-008-T08|DONE|Run precision and concurrency tests",
        "CORE-008-T09|CURRENT|Run financial security and approval review",
    )
    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                fail(f"{path.name} is missing handoff marker {marker!r}")

    untracked = sorted(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
    )
    if len(untracked) != 1:
        fail(f"expected only the controller snapshot before evidence: {untracked}")

    snapshot = Path(untracked[0])
    if not re.fullmatch(
        r"REOS_CONTROL_CENTER/snapshots/state_\d{8}_\d{6}_\d{6}\.json",
        snapshot.as_posix(),
    ):
        fail(f"unexpected controller snapshot path: {snapshot}")

    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    snapshot_data = json.loads(snapshot.read_text(encoding="utf-8"))
    stored_snapshot_hash = snapshot_data.get("integrity", {}).get("sha256")
    if (
        not isinstance(stored_snapshot_hash, str)
        or stored_snapshot_hash != calculate_hash(snapshot_data)
    ):
        fail("controller snapshot integrity is invalid")

    source_paths = (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/financial_domain.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_concurrency.py",
        *[
            f"REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/{name}"
            for name in FOCUSED_TESTS
        ],
    )
    source_rows = []
    for relative in source_paths:
        blob_sha = run(
            ["git", "rev-parse", f"{expected_sha}:{relative}"]
        )
        source_rows.append(f"| `{relative}` | `{blob_sha}` |")

    state_blob_sha = run(["git", "hash-object", str(STATE)])
    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/"
        f"{os.environ['ACTIONS_RUN_ID']}"
    )
    evidence_text = textwrap.dedent(
        f"""\
        # CORE-008-T08 — Precision and Concurrency CI Evidence

        ## Authority

        - Project: HOMIO / REOS
        - Branch: `reos-development`
        - Verified code commit: `{expected_sha}`
        - Actions run: [{os.environ['ACTIONS_RUN_ID']}]({run_url})
        - Canonical transition: existing Control Center `complete-subtask`
        - No manual `state.json` edits were performed.

        ## Verification results

        - Focused precision/concurrency tests: **{focused_count} passed**
        - Full commission financial suite: **{financial_count} passed**
        - Complete ACRL suite: **{acrl_count} passed**

        ## Exact reviewed source and test blobs

        | Path | Git blob SHA |
        |---|---|
        {chr(10).join(source_rows)}

        ## Canonical readback

        - State blob SHA after controller transition: `{state_blob_sha}`
        - T07: `DONE`
        - T08: `DONE`
        - T09: `CURRENT`
        - CORE-008-AC01: `PENDING`
        - CORE-008-AC02: `VERIFIED`
        - CORE-008-AC03: `VERIFIED`
        - CORE-008-AC04: `PENDING`
        - CORE-008-AC05: `PENDING`
        - CORE-008-AC06: `PENDING`

        This evidence closes T08 only. It does not claim that the CORE-008
        gate or its remaining acceptance criteria are complete.
        """
    )
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(evidence_text, encoding="utf-8", newline="\n")

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

    staged_paths = sorted(expected_tracked | expected_untracked)
    run(["git", "add", "--", *staged_paths])
    run(
        ["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"]
    )
    actual_staged = set(
        run(["git", "diff", "--cached", "--name-only"]).splitlines()
    )
    if actual_staged != set(staged_paths):
        fail(f"staged allowlist mismatch: {sorted(actual_staged)}")

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            "chore(control-center): complete CORE-008-T08 via controller",
        ],
        capture=False,
    )
    local_commit = run(["git", "rev-parse", "HEAD"])
    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("transition commit parent differs from verified code commit")

    run(
        ["git", "push", "origin", "HEAD:refs/heads/reos-development"],
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
    if remote_sha != local_commit:
        fail("remote branch readback does not match transition commit")

    readback_path = Path(os.environ["RUNNER_TEMP"]) / "state-readback.json"
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
    stored_state_hash = readback.get("integrity", {}).get("sha256")
    if (
        not isinstance(stored_state_hash, str)
        or stored_state_hash != calculate_hash(readback)
    ):
        fail("remote canonical state hash is invalid")
    check_state(readback, expected_t08="DONE", expected_t09="CURRENT")

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        content = run(["git", "show", f"{remote_sha}:{relative}"])
        for marker in markers:
            if marker not in content:
                fail(f"remote {relative} lacks {marker!r}")

    remote_evidence = run(
        [
            "git",
            "show",
            f"{remote_sha}:{EVIDENCE.relative_to(ROOT).as_posix()}",
        ]
    )
    if (
        expected_sha not in remote_evidence
        or str(focused_count) not in remote_evidence
        or os.environ["ACTIONS_RUN_ID"] not in remote_evidence
    ):
        fail("remote T08 evidence is missing its SHA, run ID, or focused count")

    print(f"T08_FOCUSED_TEST_COUNT={focused_count}")
    print(f"FINANCIAL_TEST_COUNT={financial_count}")
    print(f"ACRL_TEST_COUNT={acrl_count}")
    print(f"TRANSITION_COMMIT={local_commit}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("T08 TRANSITION AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
