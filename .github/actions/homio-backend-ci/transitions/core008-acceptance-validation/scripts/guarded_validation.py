from __future__ import annotations

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
    / "evidence/CORE-008/acceptance-criteria-validation-ci-evidence.md"
)

CRITERION_TESTS = {
    "CORE-008-AC01": (
        "test_core008_t01_financial_domain.py",
        "test_core008_t01_financial_ledger_boundary.py",
        "test_core008_t13_protection_ledger.py",
    ),
    "CORE-008-AC04": (
        "test_core008_t04_settlement_integrity_linkage.py",
        "test_core008_t04_settlement_reconciliation_lifecycle.py",
        "test_core008_t04_reconciliation_replay.py",
        "test_core008_t05_dispute_reversal_rules.py",
        "test_core008_t06_financial_audit_evidence.py",
    ),
    "CORE-008-AC05": (
        "test_core008_t09_security_approval_review.py",
    ),
    "CORE-008-AC06": (
        "test_core008_t04_optimistic_concurrency.py",
        "test_core008_t13_concurrency_security_reos.py",
        "test_core008_t13_adversarial_boundaries.py",
    ),
}

CRITERION_LABELS = {
    "CORE-008-AC01": "Commission source of truth is authoritative",
    "CORE-008-AC04": "Settlement and reversal are auditable",
    "CORE-008-AC05": "Critical financial actions require appropriate approval",
    "CORE-008-AC06": "Security and concurrency tests pass",
}

SOURCE_PATHS = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/financial_domain.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/financial_ledger_boundary.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/commission_release.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/commission_security.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/commission_settlement.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/commission_settlement_integrity.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
    "commission_financial/commission_dispute.py",
)


def fail(message: str) -> None:
    raise SystemExit(
        f"CORE-008 ACCEPTANCE VALIDATION BLOCKED: {message}"
    )


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
        print(
            output,
            end="" if output.endswith("\n") else "\n",
        )

    if check and result.returncode:
        fail(
            f"command failed ({result.returncode}): "
            f"{' '.join(command)}"
        )

    return output.strip()


def pytest_count(output: str, label: str) -> int:
    matches = re.findall(r"(\d+)\s+passed(?:\s|$)", output)

    if not matches or int(matches[-1]) < 1:
        fail(f"{label}: no positive pytest pass count found")

    if re.search(r"\b\d+\s+failed\b", output):
        fail(f"{label}: pytest reported failures")

    if re.search(r"\b\d+\s+error(?:s)?\b", output):
        fail(f"{label}: pytest reported errors")

    return int(matches[-1])


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


def preflight(expected_sha: str) -> dict:
    if os.environ.get("GITHUB_ACTOR") != "prajaktaranjane80-sketch":
        fail("only the repository owner may authorize validation")

    if os.environ.get("GITHUB_REF") != "refs/heads/reos-development":
        fail("only reos-development is permitted")

    if expected_sha != os.environ.get("VERIFIED_CODE_SHA"):
        fail("expected and verified code SHAs differ")

    if run(["git", "rev-parse", "HEAD"]) != expected_sha:
        fail("checked-out code SHA differs from expected SHA")

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
        fail("canonical branch changed before validation")

    if run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    ):
        fail("checkout is not clean before validation")

    verify_integrity()

    state = read_canonical_state()

    try:
        require_core008_criteria_baseline(state)
    except (ValueError, KeyError, TypeError) as exc:
        fail(f"acceptance-criteria baseline drift: {exc}")

    execution = state.get("execution", {})
    gate, subtasks, _criteria = state_indexes(state)

    if execution.get("current_gate") != "CORE-008":
        fail("canonical current gate is not CORE-008")

    if gate.get("status") != "READY_FOR_VALIDATION":
        fail(
            "gate must be READY_FOR_VALIDATION; got "
            f"{gate.get('status')!r}"
        )

    if execution.get("current_subtask") != "CORE-008-T10":
        fail("canonical execution pointer must be CORE-008-T10")

    if gate.get("current_subtask") != "CORE-008-T10":
        fail("gate current_subtask must be CORE-008-T10")

    if subtasks.get("CORE-008-T08", {}).get("status") != "DONE":
        fail("T08 must be DONE")

    if subtasks.get("CORE-008-T09", {}).get("status") != "DONE":
        fail("T09 must be DONE before acceptance validation")

    if subtasks.get("CORE-008-T10", {}).get("status") != "PENDING":
        fail("T10 must remain PENDING until validation and approval")

    for item in gate.get("subtasks", []):
        if item.get("id") == "CORE-008-T10":
            continue
        if item.get("status") not in ("DONE", "CLOSED"):
            fail(
                "prior implementation subtask is unfinished: "
                f"{item.get('id')}={item.get('status')}"
            )

    if EVIDENCE.exists():
        fail(
            "acceptance-validation evidence already exists; "
            "refusing a duplicate transition"
        )

    for filenames in CRITERION_TESTS.values():
        for filename in filenames:
            path = FINANCIAL / filename
            if not path.is_file():
                fail(
                    "required existing test is missing: "
                    f"{path.relative_to(ROOT)}"
                )

    for relative in SOURCE_PATHS:
        if not (ROOT / relative).is_file():
            fail(f"required source file is missing: {relative}")

    return state


def run_test_group(
    criterion_id: str,
    filenames: tuple[str, ...],
) -> int:
    output = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *[
                str((FINANCIAL / filename).relative_to(ROOT))
                for filename in filenames
            ],
        ]
    )

    return pytest_count(
        output,
        f"{criterion_id} focused tests",
    )


def run_full_suite(path: Path, label: str) -> int:
    output = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(path.relative_to(ROOT)),
        ]
    )

    return pytest_count(output, label)


def controller_verify_criterion(
    criterion_id: str,
    evidence: str,
) -> None:
    output = run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "verify-criterion",
            criterion_id,
            "--evidence",
            evidence,
        ]
    )

    if f"VERIFIED: {criterion_id}" not in output:
        fail(f"controller did not verify {criterion_id}")

    verify_integrity()

    state = read_canonical_state()
    gate, _subtasks, criteria = state_indexes(state)

    if gate.get("status") != "READY_FOR_VALIDATION":
        fail("gate changed unexpectedly before validation completed")

    if criteria.get(criterion_id) != "VERIFIED":
        fail(f"{criterion_id} did not persist as VERIFIED")


def check_validated_state(state: dict) -> None:
    execution = state.get("execution", {})
    gate, subtasks, criteria = state_indexes(state)

    if execution.get("current_gate") != "CORE-008":
        fail("readback current gate is not CORE-008")

    if execution.get("current_subtask") != "CORE-008-T10":
        fail("readback execution pointer is not CORE-008-T10")

    if execution.get("status") != "READY_FOR_APPROVAL":
        fail(
            "execution status should be READY_FOR_APPROVAL; got "
            f"{execution.get('status')!r}"
        )

    if gate.get("status") != "VALIDATED":
        fail("gate is not VALIDATED")

    if gate.get("current_subtask") != "CORE-008-T10":
        fail("gate pointer is not CORE-008-T10")

    if subtasks.get("CORE-008-T08", {}).get("status") != "DONE":
        fail("T08 changed unexpectedly")

    if subtasks.get("CORE-008-T09", {}).get("status") != "DONE":
        fail("T09 changed unexpectedly")

    if (
        subtasks.get("CORE-008-T10", {}).get("status")
        != "READY_FOR_APPROVAL"
    ):
        fail("T10 must be READY_FOR_APPROVAL, not auto-approved")

    for criterion_id in (
        "CORE-008-AC01",
        "CORE-008-AC02",
        "CORE-008-AC03",
        "CORE-008-AC04",
        "CORE-008-AC05",
        "CORE-008-AC06",
    ):
        if criteria.get(criterion_id) != "VERIFIED":
            fail(f"{criterion_id} is not VERIFIED")

    if (
        state.get("session", {}).get("last_handoff")
        != "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
    ):
        fail("canonical handoff path is incorrect")


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
        name for name in required_env
        if not os.environ.get(name)
    ]

    if missing:
        fail(f"missing required environment: {missing}")

    expected_sha = os.environ["EXPECTED_SHA"]
    run_id = os.environ["ACTIONS_RUN_ID"]

    preflight(expected_sha)

    focused_counts: dict[str, int] = {}

    # All focused and full regressions must pass before any criteria status
    # changes are submitted to the canonical Control Center.
    for criterion_id, filenames in CRITERION_TESTS.items():
        focused_counts[criterion_id] = run_test_group(
            criterion_id,
            filenames,
        )

    financial_count = run_full_suite(
        FINANCIAL,
        "complete commission financial suite",
    )

    acrl_count = run_full_suite(
        ACRL,
        "complete ACRL regression suite",
    )

    evidence_notes = {
        "CORE-008-AC01": (
            "Financial domain, ledger boundary, and protection-ledger "
            "authority review passed. Focused tests: "
            f"{focused_counts['CORE-008-AC01']} passed; "
            f"full financial regressions: {financial_count} passed; "
            f"full ACRL regressions: {acrl_count} passed. "
            f"Verified code SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "CORE-008-AC04": (
            "Settlement integrity, reconciliation lifecycle/replay, "
            "dispute reversal, and financial audit evidence review passed. "
            "Focused tests: "
            f"{focused_counts['CORE-008-AC04']} passed; "
            f"full financial regressions: {financial_count} passed; "
            f"full ACRL regressions: {acrl_count} passed. "
            f"Verified code SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "CORE-008-AC05": (
            "Critical financial-action approval boundary review passed "
            "through the focused security/approval suite. Focused tests: "
            f"{focused_counts['CORE-008-AC05']} passed; "
            f"full financial regressions: {financial_count} passed; "
            f"full ACRL regressions: {acrl_count} passed. "
            f"Verified code SHA: {expected_sha}; Actions run: {run_id}."
        ),
        "CORE-008-AC06": (
            "Financial concurrency, security, and adversarial focused "
            "regressions passed. Focused tests: "
            f"{focused_counts['CORE-008-AC06']} passed; "
            f"full financial regressions: {financial_count} passed; "
            f"full ACRL regressions: {acrl_count} passed. "
            f"Verified code SHA: {expected_sha}; Actions run: {run_id}."
        ),
    }

    for criterion_id, evidence in evidence_notes.items():
        controller_verify_criterion(criterion_id, evidence)

    validation_output = run(
        [
            sys.executable,
            "REOS_CONTROL_CENTER/reos_control_center.py",
            "validate-gate",
        ]
    )

    if "GATE VALIDATED: CORE-008" not in validation_output:
        fail(
            "Control Center did not validate CORE-008; "
            "review validation output before retrying"
        )

    for path in (STATE, PACKET, HANDOFF):
        preserve_line_endings(path)

    verify_integrity()

    state = read_canonical_state()
    check_validated_state(state)

    for criterion_id, evidence in evidence_notes.items():
        criterion = next(
            (
                item
                for item in state["gate_plans"]["CORE-008"][
                    "criteria_state"
                ]
                if item.get("id") == criterion_id
            ),
            None,
        )

        if not criterion or evidence != criterion.get("evidence"):
            fail(f"canonical evidence mismatch for {criterion_id}")

    markers = (
        "CURRENT_SUBTASK=CORE-008-T10",
        "CORE-008-T09|DONE|Run financial security and approval review",
        "CORE-008-T10|READY_FOR_APPROVAL|Freeze commission and financial core",
        "CORE-008-AC01|VERIFIED|",
        "CORE-008-AC02|VERIFIED|",
        "CORE-008-AC03|VERIFIED|",
        "CORE-008-AC04|VERIFIED|",
        "CORE-008-AC05|VERIFIED|",
        "CORE-008-AC06|VERIFIED|",
    )

    for path in (PACKET, HANDOFF):
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                fail(f"{path.name} lacks handoff marker {marker!r}")

    untracked = sorted(
        run(
            ["git", "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
    )

    snapshot_paths = [
        path for path in untracked
        if re.fullmatch(
            r"REOS_CONTROL_CENTER/snapshots/"
            r"state_\d{8}_\d{6}_\d{6}\.json",
            path,
        )
    ]

    if len(snapshot_paths) != 5:
        fail(
            "expected five controller snapshots from four criterion "
            f"verifications and gate validation; found {snapshot_paths}"
        )

    evidence_path = EVIDENCE.relative_to(ROOT).as_posix()
    expected_untracked = set(snapshot_paths) | {evidence_path}

    if set(untracked) != expected_untracked:
        fail(
            "untracked change allowlist mismatch: "
            f"{sorted(untracked)}"
        )

    from REOS_CONTROL_CENTER.reos_control_center import calculate_hash

    evidence_lines = [
        "# CORE-008 — Acceptance Criteria Validation Evidence",
        "",
        "## Authority",
        "",
        "- Project: HOMIO / REOS",
        "- Branch: `reos-development`",
        f"- Verified source commit: `{expected_sha}`",
        f"- Actions run: [{run_id}]({os.environ['ACTIONS_SERVER_URL']}/{os.environ['ACTIONS_REPOSITORY']}/actions/runs/{run_id})",
        "- Criterion statuses were updated using the existing Control Center.",
        "- No direct `state.json` writes were performed by this runner.",
        "- The gate was validated, but it was not approved or frozen.",
        "",
        "## Focused regression results",
        "",
    ]

    for criterion_id, count in focused_counts.items():
        evidence_lines.append(
            f"- {criterion_id}: **{count} passed**"
        )

    evidence_lines.extend(
        [
            f"- Full commission financial suite: **{financial_count} passed**",
            f"- Full ACRL suite: **{acrl_count} passed**",
            "",
            "## Reviewed source and test blobs",
            "",
            "| Path | Git blob SHA |",
            "|---|---|",
        ]
    )

    test_paths = [
        f"REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/{name}"
        for names in CRITERION_TESTS.values()
        for name in names
    ]

    all_source_paths = list(dict.fromkeys((*SOURCE_PATHS, *test_paths)))

    for relative in all_source_paths:
        blob_sha = run(
            ["git", "rev-parse", f"{expected_sha}:{relative}"]
        )
        evidence_lines.append(f"| `{relative}` | `{blob_sha}` |")

    state_blob_sha = run(["git", "hash-object", str(STATE)])

    evidence_lines.extend(
        [
            "",
            "## Canonical readback",
            "",
            f"- State blob SHA: `{state_blob_sha}`",
            "- State integrity: `PASS`",
            "- CORE-008 gate: `VALIDATED`",
            "- T08: `DONE`",
            "- T09: `DONE`",
            "- T10: `READY_FOR_APPROVAL`",
            "- CORE-008-AC01: `VERIFIED`",
            "- CORE-008-AC02: `VERIFIED`",
            "- CORE-008-AC03: `VERIFIED`",
            "- CORE-008-AC04: `VERIFIED`",
            "- CORE-008-AC05: `VERIFIED`",
            "- CORE-008-AC06: `VERIFIED`",
            "",
            "T10 financial-core freeze remains subject to explicit approval. "
            "This workflow does not run `approve-gate`.",
        ]
    )

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(
        "\n".join(evidence_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    expected_tracked = {
        "REOS_CONTROL_CENTER/data/state.json",
        "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt",
        "REOS_CONTROL_CENTER/REOS_NEXT_CHAT.txt",
    }

    actual_tracked = set(
        run(["git", "diff", "--name-only"]).splitlines()
    )

    if actual_tracked != expected_tracked:
        fail(
            "unexpected tracked changes: "
            f"{sorted(actual_tracked)}"
        )

    run(
        ["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"]
    )

    run(["git", "add", "--", *sorted(expected_tracked | expected_untracked)])

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

    staged = set(
        run(["git", "diff", "--cached", "--name-only"]).splitlines()
    )

    if staged != expected_tracked | expected_untracked:
        fail(f"staged allowlist mismatch: {sorted(staged)}")

    run(
        [
            "git",
            "-c",
            "user.name=github-actions[bot]",
            "-c",
            "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit",
            "-m",
            "chore(control-center): validate CORE-008 acceptance criteria",
        ],
        capture=False,
    )

    local_commit = run(["git", "rev-parse", "HEAD"])

    if run(["git", "rev-parse", "HEAD^"]) != expected_sha:
        fail("validation commit parent differs from verified source commit")

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

    if remote_sha != local_commit:
        fail("remote branch does not match validation commit")

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

    readback = json.loads(
        readback_path.read_text(encoding="utf-8")
    )

    stored_hash = readback.get("integrity", {}).get("sha256")

    if (
        not isinstance(stored_hash, str)
        or stored_hash != calculate_hash(readback)
    ):
        fail("remote canonical state integrity check failed")

    check_validated_state(readback)

    for criterion_id, evidence in evidence_notes.items():
        criterion = next(
            (
                item
                for item in readback["gate_plans"]["CORE-008"][
                    "criteria_state"
                ]
                if item.get("id") == criterion_id
            ),
            None,
        )

        if not criterion or criterion.get("evidence") != evidence:
            fail(f"remote criterion evidence mismatch for {criterion_id}")

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
            f"{remote_sha}:{evidence_path}",
        ]
    )

    for required in (
        expected_sha,
        run_id,
        str(financial_count),
        str(acrl_count),
        "T10: `READY_FOR_APPROVAL`",
        "CORE-008 gate: `VALIDATED`",
    ):
        if required not in remote_evidence:
            fail(f"remote evidence is missing required marker: {required}")

    print(f"CORE008_AC01_TEST_COUNT={focused_counts['CORE-008-AC01']}")
    print(f"CORE008_AC04_TEST_COUNT={focused_counts['CORE-008-AC04']}")
    print(f"CORE008_AC05_TEST_COUNT={focused_counts['CORE-008-AC05']}")
    print(f"CORE008_AC06_TEST_COUNT={focused_counts['CORE-008-AC06']}")
    print(f"FINANCIAL_TEST_COUNT={financial_count}")
    print(f"ACRL_TEST_COUNT={acrl_count}")
    print(f"VALIDATION_COMMIT={local_commit}")
    print(f"CANONICAL_BRANCH_HEAD={remote_sha}")
    print("CORE-008 ACCEPTANCE VALIDATION AND CANONICAL READBACK: PASS")


if __name__ == "__main__":
    main()
