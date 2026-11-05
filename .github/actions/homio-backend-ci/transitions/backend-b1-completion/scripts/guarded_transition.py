from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data/state.json"
PACKET = CONTROL / "packets/NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"
BACKEND = CONTROL / "backend"

ACRL_ROOT = (
    CONTROL
    / "AUTONOMY_ENGINE/continuity/acrl"
)

REQUEST = (
    CONTROL
    / "evidence/BACKEND-001/B1-completion-request.md"
)

EVIDENCE = (
    CONTROL
    / "evidence/BACKEND-001/"
    "B1-application-foundation-ci-evidence.md"
)

OWNER = "prajaktaranjane80-sketch"
REPOSITORY = "prajaktaranjane80-sketch/Homio"
BRANCH = "reos-development"

APPROVAL_PREFIX = (
    "[CONTROL-CENTER-COMPLETE-BACKEND-001-B1]"
)

B1_ACCEPTANCE = [
    "Build is reproducible.",
    "Invalid runtime configuration fails safely.",
    "Health and readiness semantics are tested.",
    "Graceful shutdown is tested.",
    "No duplicate public API application exists.",
]

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


for import_root in (ROOT, CONTROL):
    value = str(import_root)
    if value in sys.path:
        sys.path.remove(value)
    sys.path.insert(0, value)

os.chdir(ROOT)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True


def fail(message: str) -> None:
    raise SystemExit(
        f"BACKEND-001-B1 COMPLETION BLOCKED: {message}"
    )


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = True,
    display: bool = True,
) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )

    output = (
        completed.stdout or ""
        if capture
        else ""
    )

    if output and display:
        print(
            output,
            end="" if output.endswith("\n") else "\n",
        )

    if completed.returncode != 0:
        fail(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}"
        )

    return output.strip()


def clean_ansi(value: str) -> str:
    return ANSI_ESCAPE.sub("", value)


def extract_vitest_count(
    output: str,
    label: str,
) -> int:
    cleaned = clean_ansi(output)

    match = re.search(
        rf"\b{re.escape(label)}\s+(\d+)\s+passed\b",
        cleaned,
    )

    if match is None:
        fail(
            f"npm verification did not report "
            f"a successful {label} count"
        )

    count = int(match.group(1))

    if count < 1:
        fail(f"{label} reported no passing tests")

    if re.search(r"\b\d+\s+failed\b", cleaned):
        fail(f"{label} reported failed tests")

    return count


def extract_pytest_count(
    output: str,
    label: str,
) -> int:
    matches = re.findall(
        r"(\d+)\s+passed(?:\s|,|$)",
        clean_ansi(output),
    )

    if not matches:
        fail(f"{label} did not report a positive pytest pass count")

    if re.search(
        r"\b\d+\s+failed\b",
        clean_ansi(output),
    ):
        fail(f"{label} reported failed tests")

    count = int(matches[-1])

    if count < 1:
        fail(f"{label} reported no passing tests")

    return count


def read_state() -> dict:
    return json.loads(
        STATE.read_text(encoding="utf-8")
    )


def validate_state(
    state: dict,
    *,
    transitioned: bool,
    expected_sha: str | None = None,
    run_id: str | None = None,
) -> None:
    execution = state.get("execution", {})
    gate = state.get("gate_plans", {}).get("BACKEND-001")

    if not isinstance(gate, dict):
        fail("canonical BACKEND-001 gate is missing")

    if execution.get("current_gate") != "BACKEND-001":
        fail("canonical current gate is no longer BACKEND-001")

    if gate.get("status") != "CURRENT":
        fail("BACKEND-001 is not CURRENT")

    subtasks = {
        item.get("id"): item
        for item in gate.get("subtasks", [])
        if isinstance(item, dict)
    }

    wanted_current = (
        "BACKEND-001-B2"
        if transitioned
        else "BACKEND-001-B1"
    )

    expected_statuses = {
        "BACKEND-001-B0": "DONE",
        "BACKEND-001-B1": "DONE" if transitioned else "CURRENT",
        "BACKEND-001-B2": "CURRENT" if transitioned else "PENDING",
    }

    expected_statuses.update(
        {
            f"BACKEND-001-B{number:02d}": "PENDING"
            for number in range(3, 11)
        }
    )

    for subtask_id, expected_status in expected_statuses.items():
        actual = subtasks.get(
            subtask_id,
            {},
        ).get("status")

        if actual != expected_status:
            fail(
                f"{subtask_id} must be {expected_status}; "
                f"found {actual!r}"
            )

    if gate.get("current_subtask") != wanted_current:
        fail("gate current_subtask does not match the expected position")

    if execution.get("current_subtask") != wanted_current:
        fail("execution current_subtask does not match the expected position")

    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution mode is no longer CONTROL_CENTER_DRIVEN")

    b1 = subtasks.get("BACKEND-001-B1", {})

    if b1.get("acceptance_criteria") != B1_ACCEPTANCE:
        fail("B1 acceptance criteria differ from the approved contract")

    if (
        subtasks.get("BACKEND-001-B2", {}).get("title")
        != "API security and trusted context"
    ):
        fail("B2 title differs from the approved backend sequence")

    criteria = {
        item.get("id"): item.get("status")
        for item in gate.get("criteria_state", [])
        if isinstance(item, dict)
    }

    expected_criteria = {
        f"BACKEND-001-AC{number:02d}": "PENDING"
        for number in range(1, 11)
    }

    if criteria != expected_criteria:
        fail(
            "Gate-level acceptance criteria changed; "
            "B1 must not bulk-verify AC01 through AC10"
        )

    if transitioned:
        note = b1.get("note", "")

        if not isinstance(note, str):
            fail("B1 completion note is missing")

        if expected_sha and expected_sha not in note:
            fail("B1 completion note is not bound to the verified SHA")

        if run_id and run_id not in note:
            fail("B1 completion note is not bound to the Actions run")


def assert_exact_branch(expected_sha: str) -> None:
    actual = run(["git", "rev-parse", "HEAD"])

    if actual != expected_sha:
        fail("checked-out HEAD differs from the tested commit")

    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            f"refs/heads/{BRANCH}",
        ],
        capture=False,
    )

    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"])

    if remote_sha != expected_sha:
        fail("canonical branch moved; refusing a stale transition")


def preserve_line_endings(path: Path) -> None:
    relative_path = path.relative_to(ROOT).as_posix()

    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative_path}"],
        cwd=ROOT,
    )

    if (
        original.count(b"\n") > 0
        and original.count(b"\n") == original.count(b"\r\n")
    ):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(
            normalized.replace(b"\n", b"\r\n")
        )


def run_backend_verification() -> tuple[int, int, int]:
    package_manifest = BACKEND / "package.json"
    package_lock = BACKEND / "package-lock.json"

    for path in (package_manifest, package_lock):
        if not path.is_file() or path.stat().st_size == 0:
            fail(
                "required committed backend manifest is missing: "
                f"{path.relative_to(ROOT)}"
            )

        run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                path.relative_to(ROOT).as_posix(),
            ],
            display=False,
        )

    run(
        ["npm", "ci", "--no-audit", "--fund=false"],
        cwd=BACKEND,
        capture=False,
    )

    output = run(
        ["npm", "run", "verify"],
        cwd=BACKEND,
    )

    test_files = extract_vitest_count(
        output,
        "Test Files",
    )

    test_count = extract_vitest_count(
        output,
        "Tests",
    )

    if test_files < 5 or test_count < 13:
        fail(
            "backend verification count is below the "
            "currently verified B1 baseline"
        )

    run(
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            "package.json",
            "package-lock.json",
        ],
        cwd=BACKEND,
    )

    print(f"B1_BACKEND_TEST_FILES={test_files}")
    print(f"B1_BACKEND_TEST_COUNT={test_count}")
    print("B1_BACKEND_VERIFICATION=PASS")
    print("B1_LOCKFILE_REPRODUCIBILITY=PASS")

    acrl_output = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(ACRL_ROOT),
        ],
        cwd=CONTROL,
    )

    acrl_count = extract_pytest_count(
        acrl_output,
        "Complete ACRL suite",
    )

    if acrl_count < 1456:
        fail(
            "complete ACRL result is below the current "
            "verified regression baseline"
        )

    print(f"B1_ACRL_TEST_COUNT={acrl_count}")

    return test_files, test_count, acrl_count


def main() -> None:
    required_env = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
        "GITHUB_REF",
        "GITHUB_REPOSITORY",
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_SERVER_URL",
        "ACTIONS_REPOSITORY",
        "RUNNER_TEMP",
    )

    missing = [
        name
        for name in required_env
        if not os.environ.get(name)
    ]

    if missing:
        fail(f"required environment values are missing: {missing}")

    if os.environ["GITHUB_ACTOR"] != OWNER:
        fail("only the repository owner may authorize B1 completion")

    if os.environ["GITHUB_REPOSITORY"] != REPOSITORY:
        fail("unexpected repository identity")

    if os.environ["ACTIONS_REPOSITORY"] != REPOSITORY:
        fail("Actions repository identity differs from the canonical repository")

    if os.environ["GITHUB_EVENT_NAME"] != "push":
        fail("B1 completion is permitted only from an owner push")

    if os.environ["GITHUB_REF"] != f"refs/heads/{BRANCH}":
        fail("only the canonical development branch is permitted")

    expected_sha = os.environ["EXPECTED_SHA"]

    if expected_sha != os.environ["VERIFIED_CODE_SHA"]:
        fail("expected and verified code SHAs differ")

    subject = run(
        ["git", "log", "-1", "--pretty=%s"]
    )

    if not subject.startswith(APPROVAL_PREFIX):
        fail("the exact B1 completion commit prefix is missing")

    assert_exact_branch(expected_sha)

    if run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ]
    ):
        fail("checkout is not clean before the transition")

    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )

    validate_state(
        read_state(),
        transitioned=False,
    )

    if not REQUEST.is_file():
        fail("the explicit owner B1 completion request is missing")

    request_content = REQUEST.read_text(
        encoding="utf-8"
    )

    required_approval = (
        "APPROVAL: AUTHORIZE BACKEND-001-B1 COMPLETION"
    )

    if required_approval not in request_content:
        fail("the exact owner B1 completion approval is missing")

    if "SCOPE: BACKEND-001-B1 only" not in request_content:
        fail("the request must be restricted to B1 only")

    if not EVIDENCE.is_file():
        fail("the canonical B1 verification evidence is missing")

    previous_evidence = EVIDENCE.read_text(
        encoding="utf-8"
    )

    if "13 passed" not in previous_evidence:
        fail("B1 evidence does not contain the backend test result")

    if "1456 passed" not in previous_evidence:
        fail("B1 evidence does not contain the ACRL regression result")

    if os.environ["ACTIONS_RUN_ID"] in previous_evidence:
        fail("this Actions run is already recorded in the B1 evidence")

    test_files, test_count, acrl_count = (
        run_backend_verification()
    )

    assert_exact_branch(expected_sha)

    # Canonical state changes only through the existing Control Center.
    import REOS_CONTROL_CENTER.reos_control_center as controller

    controller.PACKETS = Path(
        "REOS_CONTROL_CENTER/packets"
    )

    note = (
        "BACKEND-001-B1 completed through the existing Control Center "
        f"after exact-commit backend verification ({test_files} test files, "
        f"{test_count} tests passed), reproducible npm ci/build verification, "
        f"and the complete ACRL regression suite ({acrl_count} passed). "
        f"GitHub Actions run {os.environ['ACTIONS_RUN_ID']} verified "
        f"commit {expected_sha}. Only B1 is completed. "
        "BACKEND-001-AC01 through BACKEND-001-AC10 remain PENDING. "
        "This transition does not approve the whole backend gate or production."
    )

    sys.argv = [
        "reos_control_center.py",
        "complete-subtask",
        "BACKEND-001-B1",
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

    validate_state(
        transitioned_state,
        transitioned=True,
        expected_sha=expected_sha,
        run_id=os.environ["ACTIONS_RUN_ID"],
    )

    if (
        transitioned_state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is not repository-relative")

    markers = (
        "CURRENT_SUBTASK=BACKEND-001-B2",
        "BACKEND-001-B1|DONE|Backend application foundation",
        "BACKEND-001-B2|CURRENT|API security and trusted context",
    )

    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")

        for marker in markers:
            if marker not in content:
                fail(
                    f"{path.name} is missing expected marker {marker!r}"
                )

    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    untracked = sorted(
        run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
            ]
        ).splitlines()
    )

    if len(untracked) != 1:
        fail(
            "expected exactly one Control Center snapshot; "
            f"found {untracked}"
        )

    snapshot = Path(untracked[0])

    if not re.fullmatch(
        r"REOS_CONTROL_CENTER/snapshots/"
        r"state_\d{8}_\d{6}_\d{6}\.json",
        snapshot.as_posix(),
    ):
        fail(f"unexpected Control Center snapshot path: {snapshot}")

    snapshot_data = json.loads(
        snapshot.read_text(encoding="utf-8")
    )

    if (
        snapshot_data.get("integrity", {}).get("sha256")
        != calculate_hash(snapshot_data)
    ):
        fail("Control Center snapshot integrity is invalid")

    state_blob_sha = run(
        [
            "git",
            "hash-object",
            str(STATE),
        ],
        display=False,
    )

    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{REPOSITORY}/actions/runs/"
        f"{os.environ['ACTIONS_RUN_ID']}"
    )

    evidence_addendum = f"""

## Formal B1 completion and exact-SHA verification

- Verified source commit: `{expected_sha}`
- GitHub Actions run: [{os.environ['ACTIONS_RUN_ID']}]({run_url})
- Backend test files: **{test_files} passed**
- Backend tests: **{test_count} passed**
- Reproducible dependency install: **PASS**
- TypeScript verification and production build: **PASS**
- Complete ACRL regression suite: **{acrl_count} passed**
- Canonical transition: existing Control Center `complete-subtask`
- Manual `state.json` editing: **not performed**
- Post-transition state blob SHA: `{state_blob_sha}`

### Canonical subtask readback

- BACKEND-001-B0: `DONE`
- BACKEND-001-B1: `DONE`
- BACKEND-001-B2: `CURRENT`
- BACKEND-001-B3 through B10: `PENDING`

### Gate-level acceptance boundary

BACKEND-001-AC01 through BACKEND-001-AC10 remain `PENDING`.

This transition closes B1 only. It does not complete BACKEND-001, validate gate-level acceptance criteria, approve production readiness, or authorize a production release.
"""

    with EVIDENCE.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as stream:
        stream.write(evidence_addendum)

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
        EVIDENCE.relative_to(ROOT).as_posix(),
    }

    actual_tracked = set(
        run(
            [
                "git",
                "diff",
                "--name-only",
            ]
        ).splitlines()
    )

    if actual_tracked != expected_tracked:
        fail(
            "tracked change allowlist mismatch: "
            f"{sorted(actual_tracked)}"
        )

    run(
        [
            "git",
            "-c",
            "core.whitespace=cr-at-eol",
            "diff",
            "--check",
        ]
    )

    expected_untracked = {snapshot.as_posix()}

    actual_untracked = set(
        run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
            ]
        ).splitlines()
    )

    if actual_untracked != expected_untracked:
        fail(
            "untracked file allowlist mismatch: "
            f"{sorted(actual_untracked)}"
        )

    staged = sorted(
        expected_tracked | expected_untracked
    )

    run(
        ["git", "add", "--", *staged]
    )

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
        run(
            [
                "git",
                "diff",
                "--cached",
                "--name-only",
            ]
        ).splitlines()
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
            "chore(control-center): complete BACKEND-001-B1 via controller",
        ],
        capture=False,
    )

    transition_sha = run(
        ["git", "rev-parse", "HEAD"]
    )

    if run(
        ["git", "rev-parse", "HEAD^"]
    ) != expected_sha:
        fail("transition commit parent is not the tested commit")

    run(
        [
            "git",
            "push",
            "origin",
            f"HEAD:refs/heads/{BRANCH}",
        ],
        capture=False,
    )

    run(
        [
            "git",
            "fetch",
            "--no-tags",
            "origin",
            f"refs/heads/{BRANCH}",
        ],
        capture=False,
    )

    remote_sha = run(
        ["git", "rev-parse", "FETCH_HEAD"]
    )

    if remote_sha != transition_sha:
        fail("canonical branch readback differs from transition commit")

    readback_path = (
        Path(os.environ["RUNNER_TEMP"])
        / "backend-b1-state-readback.json"
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

    readback = json.loads(
        readback_path.read_text(encoding="utf-8")
    )

    if (
        readback.get("integrity", {}).get("sha256")
        != calculate_hash(readback)
    ):
        fail("remote canonical state integrity is invalid")

    validate_state(
        readback,
        transitioned=True,
        expected_sha=expected_sha,
        run_id=os.environ["ACTIONS_RUN_ID"],
    )

    for relative_path in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        content = run(
            [
                "git",
                "show",
                f"{remote_sha}:{relative_path}",
            ],
            display=False,
        )

        for marker in markers:
            if marker not in content:
                fail(
                    f"remote {relative_path} lacks {marker!r}"
                )

    remote_evidence = run(
        [
            "git",
            "show",
            f"{remote_sha}:"
            f"{EVIDENCE.relative_to(ROOT).as_posix()}",
        ],
        display=False,
    )

    if (
        expected_sha not in remote_evidence
        or os.environ["ACTIONS_RUN_ID"] not in remote_evidence
        or f"**{test_count} passed**" not in remote_evidence
        or f"**{acrl_count} passed**" not in remote_evidence
        or state_blob_sha not in remote_evidence
    ):
        fail("remote B1 evidence is missing exact-SHA or test proof")

    print(f"B1_BACKEND_TEST_FILES={test_files}")
    print(f"B1_BACKEND_TEST_COUNT={test_count}")
    print(f"B1_ACRL_TEST_COUNT={acrl_count}")
    print(f"TRANSITION_COMMIT={transition_sha}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("BACKEND-001-B1 COMPLETION AND READBACK: PASS")


if __name__ == "__main__":
    main()
