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
SHARED = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SHARED))
os.chdir(ROOT)

from transition_contract import read_canonical_state, state_indexes  # noqa: E402

CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data/state.json"
PACKET = CONTROL / "packets/NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"

VALIDATION_EVIDENCE = (
    CONTROL
    / "evidence/CORE-008/acceptance-criteria-validation-ci-evidence.md"
)
EVIDENCE = (
    CONTROL
    / "evidence/CORE-008/final-freeze-approval-ci-evidence.md"
)

APPROVAL_PREFIX = "[CONTROL-CENTER-APPROVE-CORE-008]"

EXPECTED_CRITERIA = {
    "CORE-008-AC01",
    "CORE-008-AC02",
    "CORE-008-AC03",
    "CORE-008-AC04",
    "CORE-008-AC05",
    "CORE-008-AC06",
}

EXPECTED_SUBTASKS = {
    f"CORE-008-T{i:02d}" for i in range(1, 11)
}

# Kept as one explicit command string so the workflow wiring test can
# verify the exact publication target. It executes as normal argv tokens.
PUSH_COMMAND = "git push origin HEAD:refs/heads/reos-development".split()


def fail(message: str) -> None:
    raise SystemExit(f"CORE-008 T10 APPROVAL BLOCKED: {message}")


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
        fail(
            f"command failed ({result.returncode}): "
            f"{' '.join(command)}"
        )

    return output.strip()


def controller_command(arguments: list[str]) -> str:
    """Run the existing Control Center without direct state-file edits."""
    import REOS_CONTROL_CENTER.reos_control_center as controller

    previous_argv = sys.argv[:]
    previous_packets = controller.PACKETS
    previous_materialize = controller.materialize_current_gate
    captured = io.StringIO()

    # Preserve the repository-relative handoff contract.
    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")

    # Avoid an intermediate save when approve-gate materializes AI-001.
    # The controller's final save will persist the gate, transition,
    # handoff and execution projection together.
    def materialize_without_intermediate_save(state, persist=True):
        return previous_materialize(state, persist=False)

    controller.materialize_current_gate = materialize_without_intermediate_save

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
        controller.materialize_current_gate = previous_materialize


def verify_integrity() -> None:
    run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        capture=False,
    )


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


def check_preapproval_state(state: dict) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if execution.get("current_gate") != "CORE-008":
        fail("canonical current gate is not CORE-008")

    if execution.get("current_subtask") != "CORE-008-T10":
        fail("canonical current subtask is not CORE-008-T10")

    if execution.get("status") != "READY_FOR_APPROVAL":
        fail(
            "execution status must be READY_FOR_APPROVAL; got "
            f"{execution.get('status')!r}"
        )

    if gate.get("status") != "VALIDATED":
        fail(
            "CORE-008 gate must be VALIDATED; got "
            f"{gate.get('status')!r}"
        )

    if gate.get("current_subtask") != "CORE-008-T10":
        fail("gate current_subtask must be CORE-008-T10")

    if set(subtasks) != EXPECTED_SUBTASKS:
        fail("CORE-008 subtask inventory differs from T01-T10")

    for index in range(1, 10):
        task_id = f"CORE-008-T{index:02d}"
        if subtasks[task_id].get("status") != "DONE":
            fail(f"{task_id} is not DONE")

    if (
        subtasks["CORE-008-T10"].get("status")
        != "READY_FOR_APPROVAL"
    ):
        fail("T10 must be READY_FOR_APPROVAL before approval")

    if set(criteria) != EXPECTED_CRITERIA:
        fail("acceptance-criteria inventory differs from AC01-AC06")

    unverified = sorted(
        criterion_id
        for criterion_id, status in criteria.items()
        if status != "VERIFIED"
    )

    if unverified:
        fail(f"acceptance criteria are not all VERIFIED: {unverified}")

    if gate.get("completion_policy") != (
        "All blocking subtasks DONE + all criteria VERIFIED "
        "+ explicit approval."
    ):
        fail("canonical CORE-008 completion policy has changed")

    sequence = state.get("execution_plan", {}).get(
        "authoritative_sequence",
        [],
    )

    index = next(
        (
            i
            for i, item in enumerate(sequence)
            if item.get("gate") == "CORE-008"
        ),
        None,
    )

    if index is None:
        fail("CORE-008 is absent from the authoritative execution sequence")

    if sequence[index].get("status") != "CURRENT":
        fail("CORE-008 must be CURRENT in the authoritative plan")

    if index + 1 >= len(sequence):
        fail("the next gate is missing from the authoritative sequence")

    next_item = sequence[index + 1]

    if (
        next_item.get("gate") != "AI-001"
        or next_item.get("status") != "FUTURE"
    ):
        fail("the expected next gate AI-001 is not FUTURE")

    templates = json.loads(
        (CONTROL / "GATE_TEMPLATES.json").read_text(encoding="utf-8")
    )

    if "AI-001" not in templates:
        fail("AI-001 gate template is missing")


def check_approved_state(state: dict) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if gate.get("status") != "APPROVED":
        fail("remote canonical CORE-008 gate is not APPROVED")

    if set(subtasks) != EXPECTED_SUBTASKS:
        fail("remote CORE-008 subtask inventory changed")

    for task_id in EXPECTED_SUBTASKS:
        if subtasks[task_id].get("status") != "DONE":
            fail(f"remote read-back does not show {task_id}=DONE")

    if set(criteria) != EXPECTED_CRITERIA:
        fail("remote acceptance-criteria inventory changed")

    for criterion_id in EXPECTED_CRITERIA:
        if criteria.get(criterion_id) != "VERIFIED":
            fail(
                "remote read-back does not show "
                f"{criterion_id}=VERIFIED"
            )

    if execution.get("current_gate") != "AI-001":
        fail("next canonical gate is not AI-001")

    if execution.get("current_subtask") != "AI-001-T01":
        fail("next canonical subtask is not AI-001-T01")

    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution status is not CONTROL_CENTER_DRIVEN")

    ai_gate = state.get("gate_plans", {}).get("AI-001", {})

    if ai_gate.get("status") != "CURRENT":
        fail("AI-001 gate was not materialized as CURRENT")

    ai_subtasks = {
        item.get("id"): item
        for item in ai_gate.get("subtasks", [])
    }

    if ai_subtasks.get("AI-001-T01", {}).get("status") != "CURRENT":
        fail("AI-001-T01 was not selected as CURRENT")

    sequence = state.get("execution_plan", {}).get(
        "authoritative_sequence",
        [],
    )

    sequence_status = {
        item.get("gate"): item.get("status")
        for item in sequence
    }

    if sequence_status.get("CORE-008") != "COMPLETE":
        fail("authoritative plan does not mark CORE-008 COMPLETE")

    if sequence_status.get("AI-001") != "CURRENT":
        fail("authoritative plan does not select AI-001 as CURRENT")

    if (
        state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is incorrect")


def preflight(expected_sha: str) -> dict:
    if os.environ.get("GITHUB_ACTOR") != "prajaktaranjane80-sketch":
        fail("only the repository owner may trigger final approval")

    if os.environ.get("GITHUB_EVENT_NAME") != "push":
        fail("approval is permitted only for the guarded owner push")

    if os.environ.get("GITHUB_REF") != "refs/heads/reos-development":
        fail("only reos-development is permitted")

    if expected_sha != os.environ.get("VERIFIED_CODE_SHA"):
        fail("expected and verified source SHAs differ")

    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checked-out source SHA differs from the expected SHA")

    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if not event_path or not Path(event_path).is_file():
        fail("GitHub push event payload is missing")

    event = json.loads(
        Path(event_path).read_text(encoding="utf-8")
    )

    message = event.get("head_commit", {}).get("message", "")

    if not message.startswith(APPROVAL_PREFIX):
        fail("triggering commit does not carry the exact approval prefix")

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
        fail("canonical branch changed before approval")

    if run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    ):
        fail("checkout is not clean before approval")

    verify_integrity()

    state = read_canonical_state()
    check_preapproval_state(state)

    if EVIDENCE.exists():
        fail("final-freeze approval evidence already exists")

    if not VALIDATION_EVIDENCE.is_file():
        fail("criterion-validation evidence file is missing")

    validation_text = VALIDATION_EVIDENCE.read_text(encoding="utf-8")

    if "CORE-008 gate: `VALIDATED`" not in validation_text:
        fail("criterion-validation evidence does not document a VALIDATED gate")

    for criterion_id in EXPECTED_CRITERIA:
        if f"- {criterion_id}: `VERIFIED`" not in validation_text:
            fail(
                "criterion-validation evidence lacks "
                f"{criterion_id}=VERIFIED"
            )

    return state


def main() -> None:
    required = (
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

    missing = [
        name for name in required
        if not os.environ.get(name)
    ]

    if missing:
        fail(f"required environment is missing: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]
    run_id = os.environ["ACTIONS_RUN_ID"]

    preflight(expected_sha)

    # The caller workflow requires the complete backend/ACRL verification
    # job to succeed before this approval transition can run.
    approval_output = controller_command(["approve-gate"])

    if "GATE APPROVED & FROZEN: CORE-008" not in approval_output:
        fail("Control Center did not approve and freeze CORE-008")

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)

    verify_integrity()

    state = read_canonical_state()
    check_approved_state(state)

    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    untracked = sorted(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
    )

    snapshots = [
        item
        for item in untracked
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/"
            r"state_\d{8}_\d{6}_\d{6}\.json",
            item,
        )
    ]

    if len(snapshots) != 1 or set(untracked) != set(snapshots):
        fail(
            "expected one controller snapshot after the atomic approval "
            f"transition; found {untracked}"
        )

    snapshot_path = ROOT / snapshots[0]
    snapshot_state = json.loads(
        snapshot_path.read_text(encoding="utf-8")
    )

    snapshot_hash = snapshot_state.get("integrity", {}).get("sha256")

    if (
        not isinstance(snapshot_hash, str)
        or snapshot_hash != calculate_hash(snapshot_state)
    ):
        fail("controller-created pre-approval snapshot has invalid integrity")

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

    state_blob_sha = run(["git", "hash-object", str(STATE)])

    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/{run_id}"
    )

    evidence_text = "\n".join(
        [
            "# CORE-008-T10 — Final Financial-Core Freeze Approval Evidence",
            "",
            "## Authority and source",
            "",
            "- Project: HOMIO / REOS",
            "- Branch: `reos-development`",
            f"- Verified triggering source commit: `{expected_sha}`",
            f"- GitHub Actions run: [{run_id}]({run_url})",
            "- Approval command: existing Control Center `approve-gate`",
            "- Backend/ACRL verification passed before approval.",
            "- `state.json` was updated only by the existing Control Center.",
            "",
            "## Preconditions",
            "",
            "- Owner actor and guarded commit prefix: PASS",
            "- Canonical branch and checked-out SHA match: PASS",
            "- Canonical state integrity: PASS",
            "- CORE-008 gate: `VALIDATED` before approval",
            "- T01-T09: `DONE` before approval",
            "- T10: `READY_FOR_APPROVAL` before approval",
            "- AC01-AC06: all `VERIFIED` before approval",
            "",
            "## Canonical transition and read-back",
            "",
            "- CORE-008 gate: `APPROVED`",
            "- T01-T10: all `DONE`",
            "- AC01-AC06: all `VERIFIED`",
            "- Authoritative plan: CORE-008 `COMPLETE`",
            "- Next gate: AI-001 `CURRENT`",
            "- Next subtask: AI-001-T01",
            f"- Post-transition state blob SHA: `{state_blob_sha}`",
            "- Remote branch, state integrity, handoff and evidence: verified before PASS",
            "",
            "This evidence proves the guarded CORE-008-T10 transition only. "
            "It does not claim that AI-001 is complete.",
            "",
        ]
    )

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        evidence_text,
        encoding="utf-8",
        newline="\n",
    )

    expected_untracked = {
        snapshots[0],
        EVIDENCE.relative_to(ROOT).as_posix(),
    }

    actual_untracked = set(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
    )

    if actual_untracked != expected_untracked:
        fail(f"unexpected untracked files: {sorted(actual_untracked)}")

    staged_paths = sorted(expected_tracked | expected_untracked)

    run(["git", "add", "--", *staged_paths])

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
            "chore(control-center): approve and freeze CORE-008 via controller",
        ],
        capture=False,
    )

    transition_commit = run(["git", "rev-parse", "HEAD"])

    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("approval transition commit parent differs from verified source SHA")

    # Fail closed if another commit was pushed while approval was running.
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
        fail("canonical branch moved before approval publication")

    run(PUSH_COMMAND, capture=False)

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

    if remote_sha != transition_commit:
        fail("remote branch read-back differs from approval transition commit")

    readback_path = (
        Path(os.environ["RUNNER_TEMP"]) / "state-readback.json"
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

    remote_state = json.loads(
        readback_path.read_text(encoding="utf-8")
    )

    remote_hash = remote_state.get("integrity", {}).get("sha256")

    if (
        not isinstance(remote_hash, str)
        or remote_hash != calculate_hash(remote_state)
    ):
        fail("remote canonical state integrity is invalid")

    check_approved_state(remote_state)

    for relative in (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    ):
        content = run(["git", "show", f"{remote_sha}:{relative}"])

        for marker in (
            "CURRENT_GATE=AI-001",
            "CURRENT_SUBTASK=AI-001-T01",
            "STATUS=CONTROL_CENTER_DRIVEN",
        ):
            if marker not in content:
                fail(f"remote {relative} lacks {marker!r}")

    remote_evidence = run(
        [
            "git",
            "show",
            f"{remote_sha}:{EVIDENCE.relative_to(ROOT).as_posix()}",
        ]
    )

    for marker in (
        expected_sha,
        run_id,
        state_blob_sha,
        "CORE-008 gate: `APPROVED`",
        "Next gate: AI-001 `CURRENT`",
    ):
        if marker not in remote_evidence:
            fail(f"remote approval evidence lacks {marker!r}")

    print(f"APPROVAL_SOURCE_SHA={expected_sha}")
    print(f"APPROVAL_TRANSITION_COMMIT={transition_commit}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("CORE-008 GATE APPROVED & FROZEN")
    print("NEXT GATE: AI-001")
    print("CORE-008 T10 APPROVAL AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
