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
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from transition_contract import read_canonical_state  # noqa: E402

CONTROL = ROOT / "REOS_CONTROL_CENTER"
STATE = CONTROL / "data/state.json"
PACKET = CONTROL / "packets/NEW_CHAT_PACKET.txt"
HANDOFF = CONTROL / "REOS_NEXT_CHAT.txt"
REQUEST = CONTROL / "evidence/AI-001/T10-freeze-approval-request.md"
VALIDATION_EVIDENCE = (
    CONTROL / "evidence/AI-001/acceptance-criteria-validation-ci-evidence.md"
)
EVIDENCE = CONTROL / "evidence/AI-001/final-freeze-approval-ci-evidence.md"

APPROVAL_PREFIX = "[CONTROL-CENTER-APPROVE-AI-001]"
EXPECTED_CRITERIA = {f"AI-001-AC{i:02d}" for i in range(1, 7)}
EXPECTED_SUBTASKS = {f"AI-001-T{i:02d}" for i in range(1, 11)}
PUSH_COMMAND = ["git", "push", "origin", "HEAD:refs/heads/reos-development"]

VALIDATED_PATHS = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching",
    "REOS_CONTROL_CENTER/tets/test_ai_agent_entrypoint_contract.py",
)


def fail(message: str) -> None:
    raise SystemExit(f"AI-001 T10 APPROVAL BLOCKED: {message}")


def run(command: list[str], *, capture: bool = True, check: bool = True) -> str:
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


def read_state() -> dict:
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"canonical state cannot be read: {exc}")
    if not isinstance(state, dict):
        fail("canonical state root is not an object")
    return state


def state_indexes(state: dict) -> tuple[dict, dict[str, dict], dict[str, str]]:
    gate = state.get("gate_plans", {}).get("AI-001", {})
    subtasks = {
        item.get("id"): item for item in gate.get("subtasks", [])
        if isinstance(item, dict)
    }
    criteria = {
        item.get("id"): item.get("status")
        for item in gate.get("criteria_state", [])
        if isinstance(item, dict)
    }
    return gate, subtasks, criteria


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
        fail("canonical state integrity digest does not match its contents")


def preserve_line_endings(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    original = subprocess.check_output(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
    )
    if (
        original.count(b"\n")
        and original.count(b"\n") == original.count(b"\r\n")
    ):
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))


def validate_request() -> None:
    if not REQUEST.is_file():
        fail("AI-001-T10 approval request file is missing")

    request = REQUEST.read_text(encoding="utf-8")
    required = (
        "APPROVAL: AUTHORIZE AI-001-T10 FINAL APPROVAL AND FREEZE",
        "SCOPE: AI-001-T10 only",
        "Use the existing Control Center approve-gate command.",
        "Do not edit REOS_CONTROL_CENTER/data/state.json manually.",
        "Do not enable live provider credentials or production tool execution.",
        "Do not approve any gate other than AI-001.",
    )
    for marker in required:
        if marker not in request:
            fail(f"approval request lacks required boundary: {marker}")


def validate_acceptance_evidence(approval_sha: str) -> tuple[str, str]:
    if not VALIDATION_EVIDENCE.is_file():
        fail("AI-001 acceptance-validation evidence file is missing")

    content = VALIDATION_EVIDENCE.read_text(encoding="utf-8")
    tick = chr(96)
    source_pattern = (
        r"^- Verified source commit: "
        + tick
        + r"([0-9a-f]{40})"
        + tick
        + r"$"
    )
    source_match = re.search(source_pattern, content, re.MULTILINE)
    if not source_match:
        fail("acceptance evidence lacks the exact validated source SHA")
    validated_sha = source_match.group(1)

    required_markers = (
        "AI-001 gate: " + tick + "VALIDATED" + tick,
        "AI-001-T10: " + tick + "READY_FOR_APPROVAL" + tick,
        "AI-001-AC01 through AI-001-AC06: all "
        + tick
        + "VERIFIED"
        + tick,
        "- AI-001-AC01: **34 passed**",
        "- AI-001-AC02: **59 passed**",
        "- AI-001-AC03: **102 passed**",
        "- AI-001-AC04: **48 passed**",
        "- AI-001-AC05: **46 passed**",
        "- AI-001-AC06: **22 passed**",
        "- AI entrypoint contract suite: **15 passed**",
        "- Full AI platform suite: **157 passed**",
        "- Full ACRL suite: **1444 passed**",
        "T10 approval/freeze: **not performed**; explicit approval remains required",
    )
    for marker in required_markers:
        if marker not in content:
            fail(f"acceptance evidence lacks required verified result: {marker}")

    run_match = re.search(
        r"^- GitHub Actions run: \[(\d+)\]",
        content,
        re.MULTILINE,
    )
    if not run_match:
        fail("acceptance evidence lacks the validation Actions run ID")
    validation_run_id = run_match.group(1)

    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            validated_sha,
            approval_sha,
        ],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail("validated source is not an ancestor of the approval commit")

    # The acceptance-validated implementation and test inventory must stay
    # unchanged between acceptance validation and the approval-trigger commit.
    for relative in VALIDATED_PATHS:
        unchanged = subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                validated_sha,
                approval_sha,
                "--",
                relative,
            ],
            cwd=ROOT,
            check=False,
        )
        if unchanged.returncode != 0:
            fail(
                "acceptance-validated implementation or test changed: "
                f"{relative}"
            )

    return validated_sha, validation_run_id


def check_preapproval_state(state: dict) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if execution.get("current_gate") != "AI-001":
        fail("canonical current gate is not AI-001")
    if execution.get("current_subtask") != "AI-001-T10":
        fail("canonical current subtask is not AI-001-T10")
    if execution.get("status") != "READY_FOR_APPROVAL":
        fail(
            "execution status is not READY_FOR_APPROVAL: "
            f"{execution.get('status')!r}"
        )
    if gate.get("status") != "VALIDATED":
        fail(f"AI-001 gate is not VALIDATED: {gate.get('status')!r}")
    if gate.get("current_subtask") != "AI-001-T10":
        fail("AI-001 gate current_subtask is not T10")

    if set(subtasks) != EXPECTED_SUBTASKS:
        fail("AI-001 subtask inventory differs from T01-T10")
    for index in range(1, 10):
        task_id = f"AI-001-T{index:02d}"
        if subtasks[task_id].get("status") != "DONE":
            fail(f"{task_id} is not DONE")
    if subtasks["AI-001-T10"].get("status") != "READY_FOR_APPROVAL":
        fail("AI-001-T10 is not READY_FOR_APPROVAL")

    if set(criteria) != EXPECTED_CRITERIA:
        fail("AI-001 acceptance-criteria inventory differs from AC01-AC06")
    unverified = sorted(
        criterion_id
        for criterion_id, status in criteria.items()
        if status != "VERIFIED"
    )
    if unverified:
        fail(f"acceptance criteria are not all VERIFIED: {unverified}")

    if gate.get("completion_policy") != (
        "All blocking subtasks DONE + all criteria VERIFIED + explicit approval."
    ):
        fail("AI-001 completion policy has changed")

    sequence = state.get("execution_plan", {}).get(
        "authoritative_sequence",
        [],
    )
    index = next(
        (
            i
            for i, item in enumerate(sequence)
            if item.get("gate") == "AI-001"
        ),
        None,
    )
    if index is None or sequence[index].get("status") != "CURRENT":
        fail("AI-001 is not CURRENT in the authoritative execution sequence")
    if index + 1 >= len(sequence):
        fail("the next authoritative gate is missing")

    next_item = sequence[index + 1]
    if (
        next_item.get("gate") != "APP-001"
        or next_item.get("status") != "FUTURE"
    ):
        fail("APP-001 is not the expected FUTURE gate")

    templates = json.loads(
        (CONTROL / "GATE_TEMPLATES.json").read_text(encoding="utf-8")
    )
    if "APP-001" not in templates:
        fail("APP-001 gate template is missing")


def check_approved_state(state: dict) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if gate.get("status") != "APPROVED":
        fail("canonical AI-001 gate is not APPROVED")
    if set(subtasks) != EXPECTED_SUBTASKS:
        fail("AI-001 subtask inventory changed")
    for task_id in EXPECTED_SUBTASKS:
        if subtasks[task_id].get("status") != "DONE":
            fail(f"read-back does not show {task_id}=DONE")
    if set(criteria) != EXPECTED_CRITERIA:
        fail("AI-001 acceptance-criteria inventory changed")
    for criterion_id in EXPECTED_CRITERIA:
        if criteria.get(criterion_id) != "VERIFIED":
            fail(f"read-back does not show {criterion_id}=VERIFIED")

    if execution.get("current_gate") != "APP-001":
        fail("next canonical gate is not APP-001")
    if execution.get("current_subtask") != "APP-001-T01":
        fail("next canonical subtask is not APP-001-T01")
    if execution.get("status") != "CONTROL_CENTER_DRIVEN":
        fail("execution status is not CONTROL_CENTER_DRIVEN")

    app_gate = state.get("gate_plans", {}).get("APP-001", {})
    if app_gate.get("status") != "CURRENT":
        fail("APP-001 gate was not materialized as CURRENT")

    app_subtasks = {
        item.get("id"): item
        for item in app_gate.get("subtasks", [])
        if isinstance(item, dict)
    }
    if app_subtasks.get("APP-001-T01", {}).get("status") != "CURRENT":
        fail("APP-001-T01 was not selected as CURRENT")

    sequence_status = {
        item.get("gate"): item.get("status")
        for item in state.get("execution_plan", {}).get(
            "authoritative_sequence",
            [],
        )
    }
    if sequence_status.get("AI-001") != "COMPLETE":
        fail("authoritative plan does not mark AI-001 COMPLETE")
    if sequence_status.get("APP-001") != "CURRENT":
        fail("authoritative plan does not select APP-001 as CURRENT")

    if state.get("session", {}).get("last_handoff") != (
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is incorrect")


def preflight(expected_sha: str) -> tuple[str, str]:
    if os.environ.get("GITHUB_ACTOR") != "prajaktaranjane80-sketch":
        fail("only the repository owner may trigger final approval")
    if os.environ.get("GITHUB_EVENT_NAME") != "push":
        fail("approval is permitted only for the guarded owner push")
    if os.environ.get("GITHUB_REF") != "refs/heads/reos-development":
        fail("only reos-development is permitted")
    if os.environ.get("ACTIONS_REPOSITORY") != "prajaktaranjane80-sketch/Homio":
        fail("approval workflow is running for an unexpected repository")
    if expected_sha != os.environ.get("VERIFIED_CODE_SHA"):
        fail("expected and verified source SHAs differ")
    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checked-out source SHA differs from the expected SHA")

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).is_file():
        fail("GitHub push event payload is missing")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    message = event.get("head_commit", {}).get("message", "")
    if not message.startswith(APPROVAL_PREFIX):
        fail("triggering commit lacks the exact approval prefix")

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
        fail("AI-001 final-freeze approval evidence already exists")

    validate_request()
    validated_sha, validation_run_id = validate_acceptance_evidence(
        expected_sha
    )
    return validated_sha, validation_run_id


def controller_command(arguments: list[str]) -> str:
    """Invoke the existing Control Center; do not directly edit state.json."""
    import REOS_CONTROL_CENTER.reos_control_center as controller

    previous_argv = sys.argv[:]
    previous_packets = controller.PACKETS
    previous_materialize = controller.materialize_current_gate
    captured = io.StringIO()
    controller.PACKETS = Path("REOS_CONTROL_CENTER/packets")

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
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        fail(f"required environment is missing: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]
    run_id = os.environ["ACTIONS_RUN_ID"]
    validated_sha, validation_run_id = preflight(expected_sha)

    result = controller_command(["approve-gate"])
    if "GATE APPROVED & FROZEN: AI-001" not in result:
        fail("Control Center did not approve and freeze AI-001")

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)
    verify_integrity()

    state = read_state()
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
            "expected exactly one controller snapshot after approval; "
            f"found {untracked}"
        )

    snapshot_state = json.loads(
        (ROOT / snapshots[0]).read_text(encoding="utf-8")
    )
    snapshot_hash = snapshot_state.get("integrity", {}).get("sha256")
    if (
        not isinstance(snapshot_hash, str)
        or snapshot_hash != calculate_hash(snapshot_state)
    ):
        fail("controller-created snapshot integrity is invalid")

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }
    actual_tracked = set(run(["git", "diff", "--name-only"]).splitlines())
    if actual_tracked != expected_tracked:
        fail(f"unexpected tracked changes: {sorted(actual_tracked)}")
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"])

    state_blob_sha = run(["git", "hash-object", str(STATE)])
    server = os.environ["ACTIONS_SERVER_URL"]
    repository = os.environ["ACTIONS_REPOSITORY"]
    approval_url = f"{server}/{repository}/actions/runs/{run_id}"
    validation_url = (
        f"{server}/{repository}/actions/runs/{validation_run_id}"
    )
    tick = chr(96)

    evidence_text = "\n".join(
        [
            "# AI-001-T10 - Final AI Platform Freeze Approval Evidence",
            "",
            "## Authority and source",
            "",
            "- Project: HOMIO / REOS",
            "- Branch: reos-development",
            f"- Verified approval-trigger commit: {tick}{expected_sha}{tick}",
            f"- Acceptance-validated implementation commit: {tick}{validated_sha}{tick}",
            f"- Acceptance validation Actions run: [{validation_run_id}]({validation_url})",
            f"- Final approval Actions run: [{run_id}]({approval_url})",
            "- Approval command: existing Control Center approve-gate",
            "- Backend, entrypoint and ACRL verification passed on this exact approval-trigger commit before the state transition.",
            "- AI implementation, search/retrieval sources and entrypoint contract tests are unchanged since the acceptance-validated source commit.",
            "- state.json was updated only by the existing Control Center.",
            "- Live provider credentials and production/customer-facing AI remain disabled.",
            "",
            "## Preconditions",
            "",
            "- Owner actor and guarded commit prefix: PASS",
            "- Canonical repository, branch and checked-out SHA: PASS",
            "- Canonical state integrity: PASS",
            f"- AI-001 gate: {tick}VALIDATED{tick} before approval",
            "- AI-001-T01 through AI-001-T09: DONE before approval",
            f"- AI-001-T10: {tick}READY_FOR_APPROVAL{tick} before approval",
            "- AI-001-AC01 through AI-001-AC06: all VERIFIED before approval",
            "- Acceptance evidence and unchanged implementation/test inventory: PASS",
            "",
            "## Canonical transition and remote read-back",
            "",
            f"- AI-001 gate: {tick}APPROVED{tick}",
            "- AI-001-T01 through AI-001-T10: all DONE",
            "- AI-001-AC01 through AI-001-AC06: all VERIFIED",
            f"- Authoritative plan: AI-001 {tick}COMPLETE{tick}",
            f"- Next gate: APP-001 {tick}CURRENT{tick}",
            f"- Next subtask: {tick}APP-001-T01{tick}",
            f"- Post-transition state blob SHA: {tick}{state_blob_sha}{tick}",
            "- Controller-created snapshot, canonical integrity, packet, handoff, evidence, branch and remote read-back verified before PASS.",
            "",
            "This evidence proves the guarded AI-001-T10 approval/freeze transition only. It does not claim that APP-001 is complete or enable live AI providers or production tool execution.",
            "",
        ]
    )
    EVIDENCE.write_text(evidence_text, encoding="utf-8", newline="\n")

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
    run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--cached", "--check"])
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
            "chore(control-center): approve and freeze AI-001 via controller",
        ],
        capture=False,
    )
    transition_commit = run(["git", "rev-parse", "HEAD"])
    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("approval transition commit parent differs from verified source SHA")

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
            "CURRENT_GATE=APP-001",
            "CURRENT_SUBTASK=APP-001-T01",
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
        validated_sha,
        validation_run_id,
        run_id,
        state_blob_sha,
        "AI-001 gate:",
        "APPROVED",
        "Next gate: APP-001",
        "CURRENT",
    ):
        if marker not in remote_evidence:
            fail(f"remote approval evidence lacks {marker!r}")

    print(f"APPROVAL_SOURCE_SHA={expected_sha}")
    print(f"ACCEPTANCE_VALIDATED_SOURCE_SHA={validated_sha}")
    print(f"APPROVAL_TRANSITION_COMMIT={transition_commit}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("AI-001 GATE APPROVED & FROZEN")
    print("NEXT GATE: APP-001")
    print("AI-001-T10 APPROVAL AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
