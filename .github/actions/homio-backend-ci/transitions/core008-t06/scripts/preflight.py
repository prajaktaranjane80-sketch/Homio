"""Strict read-only preflight for the CORE-008-T06 guarded transition."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
SHARED = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(SHARED))

from transition_contract import (  # noqa: E402
    read_canonical_state,
    state_indexes,
    require_core008_criteria_baseline,
)


def run(command: list[str], *, capture: bool = True) -> str:
    completed = subprocess.run(
        command,
        check=True,
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return completed.stdout.strip() if capture else ""


def fail(message: str) -> None:
    raise SystemExit(f"BLOCKED: {message}")


def main() -> None:
    os.chdir(REPOSITORY_ROOT)

    if os.environ.get("GITHUB_ACTOR") != "prajaktaranjane80-sketch":
        fail("only the repository owner may authorize this transition.")

    if os.environ.get("GITHUB_REF") != "refs/heads/reos-development":
        fail("transition is allowed only from reos-development.")

    expected_sha = os.environ.get("EXPECTED_SHA", "")
    if not expected_sha:
        fail("EXPECTED_SHA is not set.")

    actual_sha = run(["git", "rev-parse", "HEAD"])
    if actual_sha != expected_sha:
        fail(
            "checked-out SHA mismatch: "
            f"expected={expected_sha}, actual={actual_sha}"
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

    if remote_sha != expected_sha:
        fail(
            "canonical branch moved: "
            f"expected={expected_sha}, remote={remote_sha}"
        )

    dirty = run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    )
    if dirty:
        run(["git", "status", "--short"], capture=False)
        fail("checkout is not clean before transition preflight.")

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

    if execution.get("current_gate") != "CORE-008":
        fail("current gate is not CORE-008.")

    if execution.get("current_subtask") != "CORE-008-T06":
        fail("T06 is no longer the canonical current task.")

    if gate.get("status") != "CURRENT":
        fail("CORE-008 gate is not CURRENT.")

    if subtasks.get("CORE-008-T05", {}).get("status") != "DONE":
        fail("T05 is not DONE.")

    if subtasks.get("CORE-008-T06", {}).get("status") != "CURRENT":
        fail("T06 is not CURRENT.")

    if subtasks.get("CORE-008-T07", {}).get("status") != "PENDING":
        fail("T07 is not PENDING.")

    finance = (
        REPOSITORY_ROOT
        / "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial"
    )
    required_files = (
        finance / "commission_financial_audit.py",
        finance / "test_core008_t06_financial_audit_evidence.py",
        finance / "__init__.py",
    )

    for path in required_files:
        if not path.is_file():
            fail(
                "required T06 file is missing: "
                f"{path.relative_to(REPOSITORY_ROOT)}"
            )

    evidence_path = (
        REPOSITORY_ROOT
        / "REOS_CONTROL_CENTER/evidence/CORE-008/"
        "T06-financial-audit-ci-evidence.md"
    )
    if evidence_path.exists():
        fail("T06 evidence already exists; refusing a duplicate transition.")

    print(
        f"T06 PREFLIGHT PASS: SHA={expected_sha}; "
        "canonical task and AC baseline verified."
    )


if __name__ == "__main__":
    main()
