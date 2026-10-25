"""Apply T06 through the canonical controller and create its evidence record."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

sys.dont_write_bytecode = True

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
SHARED = Path(__file__).resolve().parents[3] / "shared"

sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(SHARED))
os.chdir(REPOSITORY_ROOT)

from transition_contract import (  # noqa: E402
    read_canonical_state,
    state_indexes,
    require_core008_criteria_baseline,
)

CONTROL_ROOT = REPOSITORY_ROOT / "REOS_CONTROL_CENTER"
STATE_PATH = CONTROL_ROOT / "data/state.json"
PACKET_PATH = CONTROL_ROOT / "packets/NEW_CHAT_PACKET.txt"
NEXT_CHAT_PATH = CONTROL_ROOT / "REOS_NEXT_CHAT.txt"
EVIDENCE_PATH = (
    CONTROL_ROOT / "evidence/CORE-008/T06-financial-audit-ci-evidence.md"
)


def fail(message: str) -> None:
    raise SystemExit(f"POST-CHECK FAILED: {message}")


def main() -> None:
    required_env = (
        "VERIFIED_CODE_SHA",
        "ACTIONS_RUN_ID",
        "ACTIONS_SERVER_URL",
        "ACTIONS_REPOSITORY",
        "T06_TEST_COUNT",
        "FINANCIAL_TEST_COUNT",
        "ACRL_TEST_COUNT",
    )
    missing = [key for key in required_env if not os.environ.get(key)]
    if missing:
        fail(f"missing required environment values: {missing!r}")

    if EVIDENCE_PATH.exists():
        fail("T06 evidence already exists; refusing to overwrite prior evidence.")

    import REOS_CONTROL_CENTER.reos_control_center as control_center

    # Store a repository-relative handoff path; do not persist runner paths.
    control_center.PACKETS = Path("REOS_CONTROL_CENTER/packets")

    note = (
        "CORE-008-T06 completed through the existing Control Center after focused T06, "
        f"full financial ({os.environ['FINANCIAL_TEST_COUNT']} passed), and full ACRL "
        f"({os.environ['ACRL_TEST_COUNT']} passed) regressions succeeded in Actions run "
        f"{os.environ['ACTIONS_RUN_ID']} for verified code commit "
        f"{os.environ['VERIFIED_CODE_SHA']}. Focused T06 count: "
        f"{os.environ['T06_TEST_COUNT']}. AC01, AC04, AC05, and AC06 remain pending."
    )

    sys.argv = [
        "reos_control_center.py",
        "complete-subtask",
        "CORE-008-T06",
        "--note",
        note,
    ]
    control_center.main()

    subprocess.run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
    )

    # Restore the original CRLF style only if the committed file used it
    # exclusively. The controller remains responsible for state content/hash.
    for path in (STATE_PATH, PACKET_PATH, NEXT_CHAT_PATH):
        original = subprocess.check_output(
            [
                "git",
                "show",
                f"HEAD:{path.relative_to(REPOSITORY_ROOT).as_posix()}",
            ],
            cwd=REPOSITORY_ROOT,
        )
        lf_count = original.count(b"\n")
        crlf_count = original.count(b"\r\n")

        if lf_count > 0 and lf_count == crlf_count:
            normalized = path.read_bytes().replace(b"\r\n", b"\n")
            path.write_bytes(normalized.replace(b"\n", b"\r\n"))

    subprocess.run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-state",
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
    )

    state = read_canonical_state()
    execution = state.get("execution", {})
    gate, subtasks, _criteria = state_indexes(state)

    try:
        require_core008_criteria_baseline(state)
    except ValueError as exc:
        fail(str(exc))

    checks = (
        (execution.get("current_gate") == "CORE-008", "current gate changed"),
        (
            execution.get("current_subtask") == "CORE-008-T07",
            "controller did not advance to T07",
        ),
        (gate.get("status") == "CURRENT", "CORE-008 is not CURRENT"),
        (
            state.get("session", {}).get("last_handoff")
            == "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
            "handoff path is not repository-relative",
        ),
        (
            subtasks.get("CORE-008-T05", {}).get("status") == "DONE",
            "T05 is not DONE",
        ),
        (
            subtasks.get("CORE-008-T06", {}).get("status") == "DONE",
            "T06 is not DONE",
        ),
        (
            subtasks.get("CORE-008-T07", {}).get("status") == "CURRENT",
            "T07 is not CURRENT",
        ),
    )

    for passed, message in checks:
        if not passed:
            fail(message)

    expected_markers = (
        "CURRENT_SUBTASK=CORE-008-T07",
        "CORE-008-T06|DONE|Implement financial audit and evidence",
        "CORE-008-T07|CURRENT|Implement financial reporting hooks",
    )

    for label, path in (
        ("Control Center packet", PACKET_PATH),
        ("next-chat handoff", NEXT_CHAT_PATH),
    ):
        content = path.read_text(encoding="utf-8")
        for marker in expected_markers:
            if marker not in content:
                fail(f"{label} lacks {marker!r}")

    # Before creating the evidence file, exactly one new untracked file must
    # exist: the snapshot created by the Control Center save operation.
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPOSITORY_ROOT,
        text=True,
    ).splitlines()

    if len(untracked) != 1:
        fail(
            "expected one controller snapshot before evidence creation; "
            f"found {untracked!r}"
        )

    snapshot_path = Path(untracked[0])
    if (
        not snapshot_path.is_file()
        or not str(snapshot_path).startswith("REOS_CONTROL_CENTER/snapshots/state_")
        or not str(snapshot_path).endswith(".json")
    ):
        fail(f"unexpected untracked path {snapshot_path}")

    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    stored_hash = snapshot.get("integrity", {}).get("sha256")
    if not isinstance(stored_hash, str) or stored_hash != calculate_hash(snapshot):
        fail("controller-created snapshot integrity is invalid")

    run_url = (
        f"{os.environ['ACTIONS_SERVER_URL']}/"
        f"{os.environ['ACTIONS_REPOSITORY']}/actions/runs/"
        f"{os.environ['ACTIONS_RUN_ID']}"
    )
    verified_sha = os.environ["VERIFIED_CODE_SHA"]

    source_paths = (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/commission_financial_audit.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/test_core008_t06_financial_audit_evidence.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/__init__.py",
    )

    source_rows = []
    for relpath in source_paths:
        blob_sha = subprocess.check_output(
            ["git", "rev-parse", f"{verified_sha}:{relpath}"],
            cwd=REPOSITORY_ROOT,
            text=True,
        ).strip()
        source_rows.append(f"| `{relpath}` | `{blob_sha}` |")

    state_blob_sha = subprocess.check_output(
        ["git", "hash-object", str(STATE_PATH)],
        cwd=REPOSITORY_ROOT,
        text=True,
    ).strip()

    evidence = textwrap.dedent(
        f"""\
        # CORE-008-T06 — Financial Audit and Evidence Verification

        ## 1. Scope and authority

        - Project: HOMIO / REOS
        - Branch: `reos-development`
        - Completed subtask: `CORE-008-T06 — Implement financial audit and evidence`
        - Next current subtask: `CORE-008-T07 — Implement financial reporting hooks`
        - Canonical execution authority: `REOS_CONTROL_CENTER/data/state.json`
        - The state transition was performed by the existing Control Center controller, not by manually editing `state.json`.

        ## 2. Exact verification snapshot

        - Verified code/workflow commit: `{verified_sha}`
        - GitHub Actions run: {run_url}
        - Focused T06 audit/evidence tests passed: **{os.environ['T06_TEST_COUNT']}**
        - Complete `commission_financial` suite passed: **{os.environ['FINANCIAL_TEST_COUNT']}**
        - Complete ACRL suite passed: **{os.environ['ACRL_TEST_COUNT']}**

        ## 3. Verified file blob SHAs

        | File | Blob SHA |
        |---|---|
        {chr(10).join(source_rows)}

        ## 4. Audit and evidence controls

        T06 adds tenant- and commission-scoped immutable audit entries, external evidence references, deterministic fingerprints, a sequential append-only chain, idempotent replay of identical audit IDs, and detection of conflicting replay, sequence gaps, invalid previous-record links, and tampering with recorded entries.

        Successful critical actions require authorization references, and successful settlement, reconciliation, resolution, and reversal entries require evidence links. The module references evidence rather than storing evidence payloads; existing security, ledger, and evidence authorities remain separate.

        ## 5. Control Center transition and readback

        - Controller command: `complete-subtask CORE-008-T06`
        - Controller integrity verification: `PASS`
        - Controller-created snapshot integrity verification: `PASS`
        - Canonical state blob SHA before publish: `{state_blob_sha}`
        - Canonical subtask readback: T05=`DONE`, T06=`DONE`, T07=`CURRENT`
        - Both handoff files identify T07 as current.
        - Snapshot: `{snapshot_path}`

        ## 6. Acceptance-criterion boundary

        | Criterion | Status after transition |
        |---|---|
        | AC01 — Commission source of truth is authoritative | PENDING |
        | AC02 — Deal and ownership attribution is traceable | VERIFIED |
        | AC03 — Financial amounts use safe fixed-precision semantics | VERIFIED |
        | AC04 — Settlement and reversal are auditable | PENDING |
        | AC05 — Critical financial actions require appropriate approval | PENDING |
        | AC06 — Security and concurrency tests pass | PENDING |

        No acceptance criterion was bulk-verified.

        **Final disposition:** T06 implementation, focused tests, full financial and ACRL regressions, guarded Control Center transition, and canonical readback are recorded for the verified commit and Actions run above. CORE-008 remains open; T07 is current.
        """
    ).rstrip() + "\n"

    EVIDENCE_PATH.write_text(evidence, encoding="utf-8")

    print("POST-CHECK PASS: T06 DONE, T07 CURRENT, acceptance criteria preserved.")
    print(f"STATE_BLOB_SHA={state_blob_sha}")
    print(f"SNAPSHOT_PATH={snapshot_path}")
    print(f"ACTIONS_RUN={run_url}")


if __name__ == "__main__":
    main()
