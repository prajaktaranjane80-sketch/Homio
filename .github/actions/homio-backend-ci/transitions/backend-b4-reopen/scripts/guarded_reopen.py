
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path(__file__).resolve()
try:
    ROOT = _SCRIPT_PATH.parents[6]
except IndexError:
    ROOT = _SCRIPT_PATH.parents[2]

STATE_PATH = "REOS_CONTROL_CENTER/data/state.json"
PLAN_PATH = "REOS_CONTROL_CENTER/B4 ka work plan"
MASTER_PATH = "REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure"
TARGET_EVIDENCE_PATH = "REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-target-backup-restore-evidence.md"
COMPLETION_EVIDENCE_PATH = "REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-completion-ci-evidence.md"
PACKET_PATH = "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
HANDOFF_PATH = "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt"

REPOSITORY = "prajaktaranjane80-sketch/Homio"
OWNER = "prajaktaranjane80-sketch"
OWNER_ID = "320960487"
REPOSITORY_ID = "1346051793"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
EXPECTED_OIDC_SUBJECT = (
    "repo:prajaktaranjane80-sketch@320960487/Homio@1346051793:"
    "ref:refs/heads/reos-development"
)
BRANCH_REF = "refs/heads/reos-development"

APPROVAL_PREFIX = "[CONTROL-CENTER-REOPEN-BACKEND-001-B4]"
TRANSITION_PREFIX = "[CONTROL-CENTER-B4-REOPENED]"

BASELINE_HEAD = "ab51c9706cdbec2441658e82f3c534170f1e5969"
BASELINE_STATE_BLOB_SHA = "3482877a8e321f9d81782270bb44cfaeec297496"
BASELINE_PLAN_BLOB_SHA = "84c94c82ac5b0fde7c7bdf94acca235402c465ab"
BASELINE_MASTER_BLOB_SHA = "f8d9cd456568cc6c8eaae0caf764123a7e859ba6"
BASELINE_TARGET_EVIDENCE_BLOB_SHA = "9798c2b964426dd37f190108460f9120a6174555"
BASELINE_COMPLETION_EVIDENCE_BLOB_SHA = "9d954208406309a55afba3d1b22fe0ceea65ed69"

PREVIOUS_COMPLETION_SHA = "17784ada3e96edc5182cebb9cc548b2266b40296"
PREVIOUS_COMPLETION_RUN_ID = "45808014761"
PREVIOUS_COMPLETION_EVENT_ID = "236ee797-3a16-4f94-9dc8-e548ef5000db"

B4_ID = "BACKEND-001-B4"
B2_ID = "BACKEND-001-B2-PRODUCTION-BINDING"

EXPECTED_B4_ACCEPTANCE_CRITERIA = [
    "Only the approved ARCH-037 schema and canonical owners are used.",
    "Migrations have deterministic ordering and integrity checks.",
    "Tenant access is enforced by the target persistence boundary.",
    "Repositories and transaction boundaries have explicit write ownership.",
    "Durable session and revocation storage is supported.",
    "Shared rate-limit state and minimized audit persistence are supported.",
    "Migration, concurrency, backup and recovery tests pass.",
    "No second schema or persistence authority is introduced.",
]

ALLOWED_OWNER_COMMIT_PATHS = {
    ".github/workflows/backend-b4-reopen.yml",
    ".github/actions/homio-backend-ci/transitions/backend-b4-reopen/action.yml",
    ".github/actions/homio-backend-ci/transitions/backend-b4-reopen/scripts/guarded_reopen.py",
    ".github/actions/homio-backend-ci/transitions/backend-b4-reopen/scripts/test_guarded_reopen.py",
}


def fail(message: str) -> None:
    raise SystemExit(f"B4_REOPEN_GUARD_FAILURE: {message}")


def validate_owner_push(
    event: dict[str, Any],
    env: dict[str, str],
    expected_sha: str,
) -> None:
    required = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
        "GITHUB_REF",
        "GITHUB_REPOSITORY",
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
    )
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise ValueError(f"missing required owner-push metadata: {missing}")

    if not isinstance(event, dict):
        raise ValueError("push event payload must be an object")

    if (
        not isinstance(event.get("repository"), dict)
        or not isinstance(event.get("sender"), dict)
        or not isinstance(event.get("head_commit"), dict)
    ):
        raise ValueError("push event identity or commit fields are malformed")

    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("expected source SHA must be a full lowercase Git commit SHA")

    if env["GITHUB_ACTOR"] != OWNER or event["sender"].get("login") != OWNER:
        raise ValueError("only the immutable repository owner may request B4 reopening")

    if env["GITHUB_EVENT_NAME"] != "push" or env["GITHUB_REF"] != BRANCH_REF:
        raise ValueError("B4 reopening requires an owner push to reos-development")

    if env["GITHUB_REPOSITORY"] != REPOSITORY:
        raise ValueError("unexpected repository identity")

    if env["EXPECTED_SHA"] != expected_sha or env["VERIFIED_CODE_SHA"] != expected_sha:
        raise ValueError("triggering and verified source SHAs must match exactly")

    if event.get("ref") != BRANCH_REF or event.get("after") != expected_sha:
        raise ValueError("push event branch or commit SHA is inconsistent")

    if event["repository"].get("full_name") != REPOSITORY:
        raise ValueError("push event belongs to a different repository")

    message = event["head_commit"].get("message")
    if not isinstance(message, str) or not message.startswith(APPROVAL_PREFIX):
        raise ValueError("owner commit must begin with the exact B4 reopen approval prefix")


def _task_map(
    state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        execution = state["execution"]
        gate = state["gate_plans"]["BACKEND-001"]
        tasks = {item["id"]: item for item in gate["subtasks"]}
        b4 = tasks[B4_ID]
        b2 = tasks[B2_ID]
    except (KeyError, TypeError) as exc:
        raise ValueError("canonical BACKEND-001 state structure is incomplete") from exc

    return execution, gate, {"b4": b4, "b2": b2, "tasks": tasks}


def validate_reopen_baseline(state: dict[str, Any]) -> None:
    execution, gate, task_data = _task_map(state)
    b4 = task_data["b4"]
    b2 = task_data["b2"]

    if execution.get("current_gate") != "BACKEND-001" or gate.get("status") != "CURRENT":
        raise ValueError("BACKEND-001 must remain the active canonical gate")

    if execution.get("current_subtask") != B2_ID or gate.get("current_subtask") != B2_ID:
        raise ValueError("only the expected B2 production-binding successor may be displaced")

    if b4.get("status") != "DONE" or b2.get("status") != "CURRENT":
        raise ValueError("B4 must be DONE and B2 production binding CURRENT before reopening")

    if (
        execution.get("current_task") != f"{B2_ID}: {b2.get('title')}."
        or execution.get("status") != "CONTROL_CENTER_DRIVEN"
    ):
        raise ValueError("execution projection does not match the expected B2 successor")

    if execution.get("current_acceptance_criteria") != b2.get("acceptance_criteria"):
        raise ValueError("current B2 acceptance-criteria projection has drifted")

    note = b4.get("note")
    if not isinstance(note, str):
        raise ValueError("B4 completion history note is missing")

    lower_note = note.casefold()
    required_history = (
        PREVIOUS_COMPLETION_SHA.casefold(),
        PREVIOUS_COMPLETION_RUN_ID.casefold(),
        "controlled non-production target restore",
        "production disaster recovery",
        "wal/pitr remain not tested",
    )
    missing = [marker for marker in required_history if marker not in lower_note]
    if missing:
        raise ValueError(
            f"B4 completion note no longer contains the pinned incomplete-recovery history: {missing}"
        )

    if b4.get("acceptance_criteria") != EXPECTED_B4_ACCEPTANCE_CRITERIA:
        raise ValueError("B4 eight-criterion acceptance contract has changed")

    criteria_state = gate.get("criteria_state", [])
    expected_criterion_ids = {
        f"BACKEND-001-AC{number:02d}" for number in range(1, 11)
    }
    actual_criterion_ids = {
        item.get("id") for item in criteria_state if isinstance(item, dict)
    }
    if len(criteria_state) != 10 or actual_criterion_ids != expected_criterion_ids:
        raise ValueError("BACKEND-001 gate-level AC01-AC10 contract changed")

    completion_events = [
        event for event in state.get("events", [])
        if event.get("id") == PREVIOUS_COMPLETION_EVENT_ID
        and event.get("type") == "SUBTASK_COMPLETED"
        and event.get("payload", {}).get("id") == B4_ID
    ]
    if len(completion_events) != 1:
        raise ValueError("original guarded B4 completion event is missing or duplicated")

    if completion_events[0].get("payload", {}).get("note") != note:
        raise ValueError("B4 completion event and current task note do not preserve the same source record")

    if any(
        not isinstance(item, dict)
        or item.get("status") != "PENDING"
        or item.get("evidence") is not None
        or item.get("verified_at") is not None
        for item in gate["criteria_state"]
    ):
        raise ValueError("B4 reopen must preserve backend gate-level AC01-AC10 as PENDING")


def apply_reopen_transition(
    state: dict[str, Any],
    *,
    expected_sha: str,
    run_id: str,
    attempt: str,
    owner: str,
    owner_id: str,
    repository_id: str,
    oidc_issuer: str,
    oidc_subject: str,
    timestamp: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("expected source SHA is invalid")

    if (
        not run_id.isdigit()
        or not attempt.isdigit()
        or owner != OWNER
        or owner_id != OWNER_ID
        or repository_id != REPOSITORY_ID
        or oidc_issuer != OIDC_ISSUER
        or oidc_subject != EXPECTED_OIDC_SUBJECT
    ):
        raise ValueError("run, attempt or verified owner OIDC identity is invalid")

    validate_reopen_baseline(state)
    execution, gate, task_data = _task_map(state)
    b4 = task_data["b4"]
    b2 = task_data["b2"]
    previous_note = b4["note"]
    previous_completed_at = b4.get("completed_at")

    payload = {
        "id": B4_ID,
        "reason": (
            "Reopen B4 because its original guarded completion records controlled non-production "
            "target restore and WAL/PITR as NOT TESTED, while B4 Work Plan sections 32, 47 and 55 "
            "require target recovery evidence and applicable operational recovery controls."
        ),
        "previous_status": "DONE",
        "previous_completed_at": previous_completed_at,
        "previous_completion_note": previous_note,
        "previous_completion_source_sha": PREVIOUS_COMPLETION_SHA,
        "previous_completion_run_id": PREVIOUS_COMPLETION_RUN_ID,
        "previous_completion_event_id": PREVIOUS_COMPLETION_EVENT_ID,
        "reopen_source_sha": expected_sha,
        "reopen_actions_run_id": run_id,
        "reopen_actions_attempt": attempt,
        "approved_by": owner,
        "approved_owner_id": owner_id,
        "approved_repository_id": repository_id,
        "oidc_issuer": oidc_issuer,
        "oidc_subject": oidc_subject,
        "work_plan": "REOS_CONTROL_CENTER/B4 ka work plan",
        "work_plan_sections": ["32", "47", "48", "55"],
    }

    b4["status"] = "CURRENT"
    b4.pop("completed_at", None)
    b4["note"] = (
        "REOPENED under owner-authorized B4 recovery correction. Previous guarded completion "
        f"source {PREVIOUS_COMPLETION_SHA}, run {PREVIOUS_COMPLETION_RUN_ID}, and original note "
        "are preserved in the SUBTASK_REOPENED event. Resume B4 Work Plan Phase 8; do not "
        "repeat completed phases or change B4 acceptance criteria."
    )

    b2["status"] = "PENDING"
    b2.pop("completed_at", None)

    gate["current_subtask"] = B4_ID
    execution["current_subtask"] = B4_ID
    execution["current_task"] = f"{B4_ID}: {b4['title']}."
    execution["current_acceptance_criteria"] = list(b4["acceptance_criteria"])

    state.setdefault("events", []).append({
        "id": str(uuid.uuid4()),
        "time": timestamp,
        "type": "SUBTASK_REOPENED",
        "payload": payload,
    })
    return payload


def run(command: list[str], *, capture: bool = True) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )
    if completed.returncode != 0:
        output = (completed.stderr or completed.stdout or "").strip()
        fail(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}: {output[:2000]}"
        )

    # Preserve git status' two leading porcelain columns.
    # Only remove line terminators; never strip meaningful spaces.
    return (completed.stdout or "").rstrip("\r\n")


def parse_porcelain_status_paths(output: str) -> set[str]:
    """Parse porcelain-v1 records without discarding their two status columns."""
    paths: set[str] = set()
    for line_number, record in enumerate(output.splitlines(), start=1):
        if len(record) < 4 or record[2] != " ":
            fail(
                "git status returned a malformed porcelain-v1 record "
                f"at line {line_number}"
            )

        path = record[3:]
        if not path:
            fail(
                "git status returned an empty path "
                f"at line {line_number}"
            )

        paths.add(path)

    return paths


def verify_commit_scope(expected_sha: str) -> None:
    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checkout does not equal exact triggering source SHA")

    run(["git", "merge-base", "--is-ancestor", BASELINE_HEAD, expected_sha])

    changed = set(
        run(["git", "diff", "--name-only", f"{BASELINE_HEAD}..{expected_sha}"]).splitlines()
    )
    if changed != ALLOWED_OWNER_COMMIT_PATHS:
        fail(
            "owner reopen commit changed unexpected paths: "
            f"{sorted(changed ^ ALLOWED_OWNER_COMMIT_PATHS)}"
        )

    if run(["git", "status", "--porcelain=v1", "--untracked-files=all"]):
        fail("source checkout must be clean before the state transition")

    pins = {
        STATE_PATH: BASELINE_STATE_BLOB_SHA,
        PLAN_PATH: BASELINE_PLAN_BLOB_SHA,
        MASTER_PATH: BASELINE_MASTER_BLOB_SHA,
        TARGET_EVIDENCE_PATH: BASELINE_TARGET_EVIDENCE_BLOB_SHA,
        COMPLETION_EVIDENCE_PATH: BASELINE_COMPLETION_EVIDENCE_BLOB_SHA,
    }
    for path, expected in pins.items():
        actual = run(["git", "rev-parse", f"{expected_sha}:{path}"])
        if actual != expected:
            fail(f"protected B4 authority/evidence source changed: {path}")

    for relative in ALLOWED_OWNER_COMMIT_PATHS:
        candidate = ROOT / relative
        if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size == 0:
            fail(f"required B4 reopen source is missing, empty or a symlink: {relative}")

    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)
    if run(["git", "rev-parse", "FETCH_HEAD"]) != expected_sha:
        fail("canonical branch moved; refusing stale B4 reopen")


def main() -> None:
    required = (
        "GITHUB_ACTOR",
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_REF",
        "GITHUB_REPOSITORY",
        "EXPECTED_SHA",
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_RUN_ATTEMPT",
        "ACTIONS_ID_TOKEN_REQUEST_URL",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    )
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        fail(f"required GitHub environment values are missing: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        fail("triggering source SHA is invalid")

    try:
        event = json.loads(
            Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")
        )
        validate_owner_push(event, os.environ, expected_sha)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        fail(f"owner approval event is invalid: {exc}")

    verify_commit_scope(expected_sha)

    # Reuse the already-established GitHub Actions OIDC/T18 identity verifier.
    guard_dir = ROOT / ".github/actions/homio-backend-ci/transitions/backend-b4-completion/scripts"
    sys.path.insert(0, str(guard_dir))
    sys.path.insert(0, str(ROOT))

    try:
        import guarded_transition as completion_guard

        if (
            completion_guard.OWNER != OWNER
            or completion_guard.OWNER_ID != OWNER_ID
            or completion_guard.REPOSITORY != REPOSITORY
            or completion_guard.REPOSITORY_ID != REPOSITORY_ID
            or completion_guard.OIDC_ISSUER != OIDC_ISSUER
            or completion_guard.EXPECTED_OIDC_SUBJECT != EXPECTED_OIDC_SUBJECT
        ):
            fail("B4 reopen identity constants differ from the existing Control Center OIDC owner")

        token = completion_guard.request_github_oidc_token()
        principal = completion_guard.GitHubActionsPrincipalVerifier(expected_sha)
        claims = principal.verify_identity_token(token)
    except Exception as exc:
        fail(
            "existing Control Center owner OIDC verifier rejected the reopen request: "
            f"{type(exc).__name__}"
        )

    from REOS_CONTROL_CENTER import reos_control_center as controller

    try:
        run(
            [sys.executable, "REOS_CONTROL_CENTER/reos_control_center.py", "verify-state"],
            capture=False,
        )
        state = controller.load_state()
        validate_reopen_baseline(state)
    except Exception as exc:
        fail(f"canonical Control Center state is not eligible for B4 reopening: {exc}")

    apply_reopen_transition(
        state,
        expected_sha=expected_sha,
        run_id=os.environ["ACTIONS_RUN_ID"],
        attempt=os.environ["ACTIONS_RUN_ATTEMPT"],
        owner=OWNER,
        owner_id=str(claims.get("actor_id", "")),
        repository_id=str(claims.get("repository_id", "")),
        oidc_issuer=str(claims.get("iss", "")),
        oidc_subject=str(claims.get("sub", "")),
        timestamp=controller.now(),
    )

    controller.build_handoff_packet(state)
    state.setdefault("session", {})["last_handoff"] = PACKET_PATH
    controller.save_state(state)

    run(
        [sys.executable, "REOS_CONTROL_CENTER/reos_control_center.py", "verify-state"],
        capture=False,
    )

    persisted_state = controller.load_state()
    if not controller.is_phase_coherent(persisted_state):
        fail("Control Center phase projection became incoherent during B4 reopening")

    # Only Control Center-owned state projection, handoff packet and snapshot
    # may be generated by this guarded transition.
    allowed_generated = {STATE_PATH, PACKET_PATH, HANDOFF_PATH}
    changed = parse_porcelain_status_paths(
        run(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    )

    for path in changed:
        if not (
            path in allowed_generated
            or path.startswith("REOS_CONTROL_CENTER/snapshots/state_")
        ):
            fail(f"unexpected file changed during guarded B4 reopen: {path}")

    generated_paths = sorted(changed)
    run(["git", "add", "--", *generated_paths])
    run(["git", "config", "user.name", "github-actions[bot]"])
    run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ]
    )

    transition_message = f"{TRANSITION_PREFIX} Reopen B4 for recovery completion"
    run(["git", "commit", "-m", transition_message], capture=False)
    transition_sha = run(["git", "rev-parse", "HEAD"])
    run(["git", "push", "origin", f"HEAD:{BRANCH_REF}"], capture=False)
    run(["git", "fetch", "--no-tags", "origin", BRANCH_REF], capture=False)

    remote_sha = run(["git", "rev-parse", "FETCH_HEAD"])
    if remote_sha != transition_sha:
        fail("canonical branch readback differs from the Control Center transition commit")

    remote_state_text = run(["git", "show", f"{remote_sha}:{STATE_PATH}"])
    remote_state = json.loads(remote_state_text)

    if remote_state.get("integrity", {}).get("sha256") != controller.calculate_hash(remote_state):
        fail("remote state readback failed integrity verification")

    validate_reopen_baseline_after(
        remote_state,
        expected_sha=expected_sha,
        run_id=os.environ["ACTIONS_RUN_ID"],
    )

    for path in (PACKET_PATH, HANDOFF_PATH):
        content = run(["git", "show", f"{remote_sha}:{path}"])
        expected_markers = (
            "CURRENT_SUBTASK=BACKEND-001-B4",
            "BACKEND-001-B4|CURRENT|PostgreSQL integration",
            "BACKEND-001-B2-PRODUCTION-BINDING|PENDING|API security and trusted context — production binding",
        )
        missing_markers = [marker for marker in expected_markers if marker not in content]
        if missing_markers:
            fail(f"remote handoff readback missing reopened task projection in {path}: {missing_markers}")

    print(f"B4_REOPEN_SOURCE_SHA={expected_sha}")
    print(f"B4_REOPEN_ACTIONS_RUN_ID={os.environ['ACTIONS_RUN_ID']}")
    print(f"B4_REOPEN_OWNER={OWNER}")
    print(f"B4_REOPEN_OIDC_SUBJECT={claims.get('sub')}")
    print(f"B4_REOPEN_TRANSITION_COMMIT={transition_sha}")
    print(f"B4_REOPEN_REMOTE_HEAD={remote_sha}")
    print(f"B4_REOPEN_STATE_BLOB_SHA={run(['git', 'rev-parse', f'{remote_sha}:{STATE_PATH}'])}")
    print("B4_REOPEN_EVENT_PRESERVED_PREVIOUS_COMPLETION=true")
    print("B4_REOPEN_CURRENT_TASK=BACKEND-001-B4")
    print("B4_REOPEN_SUCCESS=true")


def validate_reopen_baseline_after(
    state: dict[str, Any],
    *,
    expected_sha: str,
    run_id: str,
) -> None:
    execution, gate, task_data = _task_map(state)
    b4, b2 = task_data["b4"], task_data["b2"]

    if execution.get("current_subtask") != B4_ID or gate.get("current_subtask") != B4_ID:
        fail("remote Control Center readback does not set B4 CURRENT")

    if b4.get("status") != "CURRENT" or b2.get("status") != "PENDING":
        fail("remote Control Center status readback is inconsistent")

    if (
        "completed_at" in b4
        or execution.get("current_task") != f"{B4_ID}: {b4.get('title')}."
    ):
        fail("remote B4 completion timestamp or current-task projection was not reset")

    if b4.get("acceptance_criteria") != EXPECTED_B4_ACCEPTANCE_CRITERIA:
        fail("remote reopen changed the eight canonical B4 acceptance criteria")

    if execution.get("current_acceptance_criteria") != EXPECTED_B4_ACCEPTANCE_CRITERIA:
        fail("remote execution projection does not expose the eight canonical B4 criteria")

    criteria_state = gate.get("criteria_state", [])
    if len(criteria_state) != 10 or any(
        not isinstance(item, dict)
        or item.get("status") != "PENDING"
        or item.get("evidence") is not None
        or item.get("verified_at") is not None
        for item in criteria_state
    ):
        fail("remote reopen mutated backend gate-level AC01-AC10")

    matching = [
        event for event in state.get("events", [])
        if event.get("type") == "SUBTASK_REOPENED"
        and event.get("payload", {}).get("reopen_source_sha") == expected_sha
        and event.get("payload", {}).get("reopen_actions_run_id") == run_id
    ]
    if len(matching) != 1:
        fail("remote state must contain exactly one exact-SHA B4 reopen event")

    payload = matching[0].get("payload", {})
    if payload.get("previous_completion_event_id") != PREVIOUS_COMPLETION_EVENT_ID:
        fail("remote reopen event does not preserve the original B4 completion event identity")

    old_events = [
        event for event in state.get("events", [])
        if event.get("id") == PREVIOUS_COMPLETION_EVENT_ID
        and event.get("type") == "SUBTASK_COMPLETED"
        and event.get("payload", {}).get("id") == B4_ID
    ]
    if (
        len(old_events) != 1
        or old_events[0].get("payload", {}).get("note") != payload.get("previous_completion_note")
    ):
        fail("remote state did not preserve the exact original B4 completion event and note")

    if (
        payload.get("approved_by") != OWNER
        or payload.get("approved_owner_id") != OWNER_ID
        or payload.get("approved_repository_id") != REPOSITORY_ID
        or payload.get("oidc_issuer") != OIDC_ISSUER
        or payload.get("oidc_subject") != EXPECTED_OIDC_SUBJECT
    ):
        fail("remote reopen event does not preserve the verified repository-owner OIDC identity")

    if PREVIOUS_COMPLETION_SHA not in str(payload.get("previous_completion_note", "")):
        fail("remote reopen event does not preserve the previous B4 completion note")


if __name__ == "__main__":
    main()
