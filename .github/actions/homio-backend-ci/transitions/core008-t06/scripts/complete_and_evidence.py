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

    # Keep the state handoff repository-relative and portable across runners.
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

    # Restore legacy CRLF only where the committed blob used CRLF exclusively.
    # Content updates and integrity recalculation remain controller-owned.
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
            normalized = path.read_bytes().replace(b"\r\n",
