
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
T07_TEST = FINANCIAL / "test_core008_t07_financial_reporting.py"
EVIDENCE = (
    CONTROL
    / "evidence/CORE-008/T07-financial-reporting-ci-evidence.md"
)


def fail(message: str) -> None:
    raise SystemExit(f"T07 TRANSITION BLOCKED: {message}")


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
    output = result.stdout or "" if capture else ""
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    if check and result.returncode:
        fail(f"command failed ({result.returncode}): {' '.join(command)}")
    return output


def pytest_count(output: str, label: str) -> int:
    matches = re.findall(r"(\d+) passed(?:\s|$)", output)
    if not matches or int(matches[-1]) < 1:
        fail(f"{label}: no positive pytest pass count found")
    if re.search(r"\b\d+ failed\b", output):
        fail(f"{label}: pytest reported failures")
    return int(matches[-1])


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"], cwd=ROOT
    )
    if original.count(b"\n") and original.count(b"\n") == original.count(b"\r\n"):
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def check_state(
    state: dict,
    *,
    expected_t07: str,
    expected_t08: str,
) -> None:
    execution = state.get("execution", {})
    gate, subtasks, _criteria = state_indexes(state)

    require_core008_criteria_baseline(state)

    if execution.get("current_gate") != "CORE-008":
        fail("canonical current gate is not CORE-008")
    if gate.get("status") != "CURRENT":
        fail("CORE-008 gate is not CURRENT")
    if subtasks.get("CORE-008-T06", {}).get("status") != "DONE":
        fail("T06 is not DONE")
    if subtasks.get("CORE-008-T07", {}).get("status") != expected_t07:
        fail(f"T07 must be {expected_t07}")
    if subtasks.get("CORE-008-T08", {}).get("status") != expected_t08:
        fail(f"T08 must be {expected_t08}")


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
        ["git", "fetch", "--no-tags", "origin", "refs/heads/reos-development"],
        capture=False,
    )
    if run(["git", "rev-parse", "FETCH_HEAD"]) != expected_sha:
        fail("canonical branch moved; refusing a stale transition")

    if run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    ).strip():
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
    check_state(state, expected_t07="CURRENT", expected_t08="PENDING")

    required_files = (
        FINANCIAL / "commission_financial_reporting.py",
        T07_TEST,
        FINANCIAL / "__init__.py",
    )
    for path in required_files:
        if not path.is_file():
            fail(f"required T07 file is missing: {path.relative_to(ROOT)}")
    if EVIDENCE.exists():
        fail("T07 evidence already exists; refusing duplicate completion")

    tests = (
        (
            "T07",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                str(T07_TEST.relative_to(ROOT)),
            ],
        ),
        (
            "financial",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                str(FINANCIAL.relative_to(ROOT)),
            ],
        ),
        (
            "ACRL",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                str(ACRL.relative_to(ROOT)),
            ],
        ),
    )
    counts: dict[str, int] = {}
    for label, command in tests:
        output = run(command)
        counts[label] = pytest_count(output, label)

    import REOS_CONTROL_CENTER.reos_control_center as controller

    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")
    note = (
        "CORE-008-T07 completed through the existing Control Center after "
        f"focused T07 ({counts['T07']} passed), full financial "
        f"({counts['financial']} passed), and full ACRL "
        f"({counts['ACRL']} passed) regressions succeeded in Actions run "
        f"{os.environ['ACTIONS_RUN_ID']} for verified code commit "
        f"{expected_sha}. CORE-008-AC01, AC04, AC05, and AC06 remain PENDING; "
        "this subtask transition does not verify gate-level acceptance criteria."
    )
    sys.argv = [
        "reos_control_center.py",
        "complete-subtask",
        "CORE-008-T07",
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
    check_state(state, expected_t07="DONE", expected_t08="CURRENT")

    if (
        state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is not repository-relative")

    markers = (
        "CURRENT_SUBTASK=CORE-008-T08",
        "CORE-008-T07|DONE|Implement financial reporting hooks",
        "CORE-008-T08|CURRENT|Run precision and concurrency tests",
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
    stored = snapshot_data.get("integrity", {}).get("sha256")
    if not isinstance(stored, str) or stored != calculate_hash(snapshot_data):
        fail("controller snapshot integrity is invalid")

    source_paths = (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_financial_reporting.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/test_core008_t07_financial_reporting.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/__init__.py",
    )
    source_rows = []
    for relative in source_paths:
        blob_sha = run(
            ["git", "rev-parse", f"{expected_sha}:{relative}"]
        ).strip()
        source_rows.append(f"| `{relative}` | `{blob_sha}` |")

    state_blob_sha = run(["git", "hash-object", str(STATE)]).strip()
    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/"
        f"{os.environ['ACTIONS_RUN_ID']}"
    )
    evidence = textwrap.dedent(
        f"""\
        # CORE-008-T07 — Financial Reporting CI Evidence

        ## Authority

        - Project: HOMIO / REOS
        - Branch: `reos-development`
        - Verified code commit: `{expected_sha}`
        - Actions run: [{os.environ['ACTIONS_RUN_ID']}]({run_url})
        - Canonical state transition: existing Control Center `complete-subtask`
        - No manual `state.json` edits were performed.

        ## Regression results

        - Focused T07 reporting tests: **{counts['T07']} passed**
        - Full commission financial package: **{counts['financial']} passed**
        - Complete ACRL suite: **{counts['ACRL']} passed**

        ## Source blob SHAs at verified code commit

        | File | Git blob SHA |
        |---|---|
        {chr(10).join(source_rows)}

        ## Canonical readback

        - State blob SHA after controller transition: `{state_blob_sha}`
        - T06: `DONE`
        - T07: `DONE`
        - T08: `CURRENT`
        - CORE-008-AC01: `PENDING`
        - CORE-008-AC02: `VERIFIED`
        - CORE-008-AC03: `VERIFIED`
        - CORE-008-AC04: `PENDING`
        - CORE-008-AC05: `PENDING`
        - CORE-008-AC06: `PENDING`

        This evidence closes T07 only. It does not claim that the CORE-008
        gate or its remaining acceptance criteria are complete.
        """
    )
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
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"])
    actual_staged = set(
        run(["git", "diff", "--cached", "--name-only"]).splitlines()
    )
    if actual_staged != set(staged):
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
            "chore(control-center): complete CORE-008-T07 via controller",
        ],
        capture=False,
    )
    local_commit = run(["git", "rev-parse", "HEAD"]).strip()
    if run(["git", "rev-parse", "HEAD^"]).strip() != expected_sha:
        fail("transition commit parent differs from verified code commit")

    run(
        ["git", "push", "origin", "HEAD:refs/heads/reos-development"],
        capture=False,
    )
    run(
        ["git", "fetch", "--no-tags", "origin", "refs/heads/reos-development"],
        capture=False,
    )
    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"]).strip()
    if remote_sha != local_commit:
        fail("remote branch readback does not match transition commit")

    readback_path = Path(os.environ["RUNNER_TEMP"]) / "state-readback.json"
    readback_path.write_bytes(
        subprocess.check_output(
            ["git", "show", f"{remote_sha}:REOS_CONTROL_CENTER/data/state.json"],
            cwd=ROOT,
        )
    )
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    stored_hash = readback.get("integrity", {}).get("sha256")
    if not isinstance(stored_hash, str) or stored_hash != calculate_hash(readback):
        fail("remote canonical state hash is invalid")
    check_state(readback, expected_t07="DONE", expected_t08="CURRENT")

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        content = run(["git", "show", f"{remote_sha}:{relative}"])
        for marker in markers:
            if marker not in content:
                fail(f"remote {relative} lacks {marker!r}")

    remote_evidence = run(
        ["git", "show", f"{remote_sha}:{EVIDENCE.relative_to(ROOT).as_posix()}"]
    )
    if expected_sha not in remote_evidence or str(counts["T07"]) not in remote_evidence:
        fail("remote T07 evidence is missing its code SHA or focused test count")
    if os.environ["ACTIONS_RUN_ID"] not in remote_evidence:
        fail("remote T07 evidence is missing the Actions run ID")

    print(f"T07_TEST_COUNT={counts['T07']}")
    print(f"FINANCIAL_TEST_COUNT={counts['financial']}")
    print(f"ACRL_TEST_COUNT={counts['ACRL']}")
    print(f"TRANSITION_COMMIT={local_commit}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("T07 TRANSITION AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
