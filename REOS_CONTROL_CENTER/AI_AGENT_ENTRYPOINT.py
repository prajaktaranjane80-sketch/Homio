"""
HOMIO / REOS — AI AGENT ENTRYPOINT
==================================

Repository-level operating contract for new GPT/AI sessions.

This file is not:
- a second Control Center, state store, ACRL or execution engine;
- a Git synchronization runner;
- an authorization or task-selection engine.

Canonical authorities:
- Execution state: REOS_CONTROL_CENTER/data/state.json
- Committed code and history: GitHub branch reos-development
- Task selection and transitions: existing REOS Control Center
- T18: execution authorization
- T20: repair and patch verification
- T21: Git repository coordination
- T22: commit and checkpoint coordination
- T23: evidence resolution
- T24: continuity and recovery

Chat history, Markdown plans and diagnostic output are evidence/context,
not execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# REPOSITORY IDENTITY
# ---------------------------------------------------------------------------

PROJECT_NAME = "HOMIO / REOS"
PROJECT_DESCRIPTION = (
    "Global AI Real Estate OS + International Brokerage + SaaS."
)

CONTROL_CENTER_NAME = "REOS_CONTROL_CENTER"
CONTROL_CENTER_PATH = Path(__file__).resolve().parent

CANONICAL_LOCAL_WORKSPACE = Path(r"D:\HOMIO")
CANONICAL_CONTROL_CENTER = (
    CANONICAL_LOCAL_WORKSPACE / CONTROL_CENTER_NAME
)

REPOSITORY_FULL_NAME = "prajaktaranjane80-sketch/Homio"
EXPECTED_BRANCH = "reos-development"
EXPECTED_ORIGIN = (
    "https://github.com/prajaktaranjane80-sketch/Homio.git"
)

CANONICAL_CODE_SOURCE = (
    "GitHub repository branch reos-development"
)

IMPLEMENTATION_WRITE_INTERFACE = (
    "Guarded GitHub REST API writes to reos-development; "
    "no competing workflow runner"
)

POWERSHELL_WRITE_ALLOWED = True
POWERSHELL_IS_VERIFICATION_ONLY = False
POWERSHELL_REMOTE_GITHUB_API_WRITE_ALLOWED = True
POWERSHELL_LOCAL_WORKTREE_WRITE_ALLOWED = False
POWERSHELL_LOCAL_GIT_MUTATION_ALLOWED = False
POWERSHELL_WRITE_MODE = "GUARDED_GITHUB_REST_API_ONLY"

PS_OUTPUT_IS_EVIDENCE_ONLY = True

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    "__pycache__/",
    "*.pyc",
    "*.pyo",
)

STATE_PATH = CONTROL_CENTER_PATH / "data" / "state.json"
AUTONOMY_ENGINE_PATH = CONTROL_CENTER_PATH / "AUTONOMY_ENGINE"
ACRL_PATH = AUTONOMY_ENGINE_PATH / "continuity" / "acrl"

ACRL_ENTRYPOINT = (
    ACRL_PATH
    / "T07_New_Chat_Bootstrap"
    / "new_chat_bootstrap.py"
)
ACRL_REPOSITORY_CONTEXT = (
    ACRL_PATH / "T14_Repository_Intelligence_Context"
)
ACRL_OPERATOR_AUTONOMY = (
    ACRL_PATH / "T15_AI_Operator_Autonomy"
)
ACRL_EXECUTION_AUTHORIZATION = (
    ACRL_PATH / "T18_Safe_Execution_Authorization_Guard"
)
ACRL_REPAIR_VERIFICATION = (
    ACRL_PATH / "T20_Autonomous_Repair_Patch_Verification"
)
ACRL_GIT_REPOSITORY_COORDINATION = (
    ACRL_PATH / "T21_Git_Repository_Read_Write_Coordination"
)
ACRL_COMMIT_CHECKPOINT_COORDINATION = (
    ACRL_PATH / "T22_Commit_Execution_Checkpoint_Coordination"
)
ACRL_EVIDENCE_RESOLUTION = (
    ACRL_PATH / "T23_Reference_Evidence_Resolution_Engine"
)
ACRL_CONTINUITY_RECOVERY = (
    ACRL_PATH / "T24_Cross_Chat_Continuity_Recovery_Engine"
)


# ---------------------------------------------------------------------------
# OPERATING CONTRACT
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class REOSAgentOperatingContract:
    """
    Descriptive repository contract.

    This does not authorize execution or replace the Control Center/ACRL.
    """

    project: str = PROJECT_NAME
    project_description: str = PROJECT_DESCRIPTION
    authoritative_state: str = (
        "REOS_CONTROL_CENTER/data/state.json"
    )
    authoritative_code_reference: str = (
        "GitHub repository branch reos-development"
    )
    implementation_write_interface: str = (
        IMPLEMENTATION_WRITE_INTERFACE
    )
    current_verification: str = (
        "Read-only local verification plus authorized guarded remote "
        "GitHub REST API writes"
    )
    continuity_system: str = "ACRL"
    chat_history_authority: str = "NON_AUTHORITATIVE"
    control_authority: str = "REOS_CONTROL_CENTER"
    execution_authority: str = (
        "REOS Control Center and applicable ACRL authorization, "
        "repair-verification, evidence and checkpoint boundaries"
    )
    ai_role: str = "Architecture-aware engineering operator"


# ---------------------------------------------------------------------------
# AI OPERATING RULES
# ---------------------------------------------------------------------------

AI_OPERATING_RULES: tuple[str, ...] = (
    "Treat REOS_CONTROL_CENTER as the project control authority.",
    "Treat data/state.json as canonical machine-readable project state.",
    "Treat GitHub branch reos-development as the canonical implementation source.",
    "Treat chat history as communication only, never as project truth.",
    "Inspect the canonical repository before proposing code changes.",
    "Inspect an exact target path before classifying it as ADD or REPLACE.",
    "Do not create duplicate files, routes, components, modules or engines.",
    "Do not reopen completed layers without repository evidence of a real need.",
    "Use T07 for bootstrap and T14 for repository-aware context.",
    "Respect T15 AI Operator Autonomy boundaries.",
    "Respect architecture locks and Control Center authority.",
    "Never directly modify authoritative state to manufacture completion.",
    "Never self-authorize execution or self-approve governance changes.",
    "Do not assume a local checkout matches the live GitHub branch.",
    "A dirty or untracked local worktree fails preflight closed.",
    "Missing upstream configuration fails preflight closed.",
    "Local ahead/behind counts must be zero for local-ready status.",
    "A local upstream-tracking ref is cached evidence, not proof of live remote HEAD.",
    "Local preflight, remote readback, canonical state and authorization are separate checks.",
    "Do not claim tests or CI passed without evidence for the exact tested SHA.",
    "Run focused verification and relevant regressions before declaring success.",
    "When evidence conflicts or is insufficient, stop and report the blocker.",
)


# ---------------------------------------------------------------------------
# DEVELOPMENT WORKFLOW CONTRACT
# ---------------------------------------------------------------------------

DEVELOPMENT_WORKFLOW_RULES: tuple[str, ...] = (
    "This entrypoint defines the agent-facing workflow policy; it does not execute writes.",
    "GitHub branch reos-development is the canonical code source.",
    "Guarded GitHub REST API writes are the approved remote implementation method.",
    "Local worktree source writes and local Git mutations are forbidden.",
    "Manual GitHub UI editing is permitted when explicitly chosen by the owner.",
    "Supporting work plans cannot override the Control Center or state.json.",
    "Inspect canonical GitHub state before every requested change.",
    "Classify files as ADD, REPLACE, VERIFY, NO CHANGE or BLOCKED as appropriate.",
    "ADD requires the exact path to be absent on the canonical branch.",
    "REPLACE requires the exact path to exist and own the requested responsibility.",
    "Never recreate a file merely because a local workspace is stale.",
    "A full replacement request requires complete replacement content, not an inferred patch.",
    "Verify remote branch, commit parent and exact content after writes.",
    "T18 authorization, T20 patch verification and T21 Git coordination remain separate responsibilities.",
    "Never treat T20 VERIFIED as proof that a Git commit occurred.",
    "The existing backend-ci.yml workflow must run the EntryPoint contract regression.",
    "The contract test must not be silently skipped if its file is missing.",
    "Do not create, download, invoke or rely on a standalone runner as a competing workflow authority.",
    "During final workflow alignment, update AI_AGENT_ENTRYPOINT.py only after the required supporting policy, test and CI work.",
)


# ---------------------------------------------------------------------------
# REMOTE GIT SYNCHRONIZATION CONTRACT
# ---------------------------------------------------------------------------

REMOTE_GIT_SYNCHRONIZATION_RULES: tuple[str, ...] = (
    "REOS_CONTROL_CENTER remains the project control authority.",
    "REOS_CONTROL_CENTER/data/state.json remains the canonical project state.",
    "GitHub branch reos-development remains the canonical code source.",
    "AI_AGENT_ENTRYPOINT.py defines policy and does not execute Git writes.",
    "Do not create a second Git synchronization engine.",
    "Do not create a second checkpoint, evidence, continuity or state engine.",
    "T18 remains the applicable execution-authorization boundary.",
    "T20 remains the repair and patch-verification boundary.",
    "T21 remains the Git repository coordination boundary.",
    "T22 remains the commit and checkpoint coordination boundary.",
    "T23 remains the evidence-resolution boundary.",
    "T24 remains the continuity and recovery boundary.",
    "T07 and T14 responsibilities must be reused rather than duplicated.",
    "Capture the live branch HEAD before an approved remote write.",
    "Use the captured HEAD as the expected commit parent.",
    "Re-read branch HEAD immediately before updating the ref.",
    "Abort if branch HEAD changes unexpectedly.",
    "Never force-update the active branch to bypass a conflict.",
    "A failed, ambiguous or conflicting operation must fail closed.",
    "Preflight failures must stop execution before any branch-ref update.",
    "Local ahead/behind data does not prove the server-side branch tip.",
    "Remote readback and commit-parent verification are separate evidence.",
    "Report PASS only after exact branch, commit parent and file content are verified.",
)


# ---------------------------------------------------------------------------
# REPOSITORY PREFLIGHT CONTRACT
# ---------------------------------------------------------------------------

REPOSITORY_PREFLIGHT_RULES: tuple[str, ...] = (
    "Canonical local workspace is D:\\HOMIO.",
    "Canonical Control Center is D:\\HOMIO\\REOS_CONTROL_CENTER.",
    "Expected repository is prajaktaranjane80-sketch/Homio.",
    "Expected branch is reos-development.",
    "Expected origin resolves to the canonical GitHub repository.",
    "Local workspace may be stale and must not override canonical GitHub evidence.",
    "Local worktree content is not a source for remote writes.",
    "Inspect staged, modified, deleted and untracked files with Git porcelain status.",
    "Inspect configured upstream without fetching or mutating the repository.",
    "Report ahead/behind counts against the local upstream-tracking ref.",
    "Missing status evidence or malformed count evidence fails closed.",
    "Any dirty worktree fails local-ready status.",
    "Missing upstream fails local-ready status.",
    "Any nonzero ahead or behind count fails local-ready status.",
    "A divergence fails local-ready status.",
    "A clean local preflight does not establish that live remote HEAD is current.",
    "Obtain separate live remote readback before remote-write verification.",
    "PS Output and frontend diagnostics are evidence only.",
    "Never mutate state.json directly.",
)


# ---------------------------------------------------------------------------
# FILE CHANGE CLASSIFICATION
# ---------------------------------------------------------------------------

FILE_CHANGE_CLASSIFICATION: tuple[str, ...] = (
    "ADD: exact path is absent on canonical branch and no existing owner has the responsibility.",
    "REPLACE: exact path exists and owns the requested responsibility.",
    "NO CHANGE: repository evidence does not justify modification.",
    "VERIFY: inspect evidence without changing the target.",
    "BLOCKED: required authority, dependency or evidence is missing.",
    "Existing routes, components and modules take precedence over duplicates.",
    "A stale local checkout is not proof that a GitHub file is missing.",
    "A completed layer is reopened only for a verified dependency, integration need or regression.",
)


# ---------------------------------------------------------------------------
# EXECUTION / IMPLEMENTATION WORKFLOW
# ---------------------------------------------------------------------------

EXECUTION_WORKFLOW: tuple[str, ...] = (
    "1. Read canonical state from REOS_CONTROL_CENTER/data/state.json.",
    "2. Verify the current GitHub branch and live repository baseline.",
    "3. Inspect exact requested paths and existing responsibility owners.",
    "4. Classify each requested file action.",
    "5. Resolve applicable architecture and dependency constraints.",
    "6. Apply required ACRL authorization and patch-verification boundaries.",
    "7. Provide exact, complete implementation content for owner-approved changes.",
    "8. Use the approved guarded remote-write workflow or the owner's explicit UI fallback.",
    "9. Verify branch, commit parent and exact changed-file content.",
    "10. Run focused tests and relevant regression checks.",
    "11. Inspect CI for the exact commit SHA.",
    "12. Resolve missing or conflicting evidence through the applicable ACRL boundary.",
    "13. Change canonical state only through the existing Control Center workflow.",
    "14. Never report PASS without independent verification evidence.",
)


# ---------------------------------------------------------------------------
# REQUIRED NEW-SESSION WORKFLOW
# ---------------------------------------------------------------------------

NEW_SESSION_WORKFLOW: tuple[str, ...] = (
    "1. Identify this repository as HOMIO / REOS.",
    "2. Read this entrypoint and reconstruct current repository context.",
    "3. Verify the live GitHub branch reos-development.",
    "4. Read active gate, task and subtask from canonical state.",
    "5. Reuse the existing T07 bootstrap and T14 repository context.",
    "6. Inspect architecture ownership, exact paths, related modules and tests.",
    "7. Classify required file actions before implementation.",
    "8. Check repository readiness and distinguish local evidence from remote proof.",
    "9. Apply applicable authorization and verification boundaries.",
    "10. Run focused tests and relevant regression tests.",
    "11. Verify the resulting commit and changed file content.",
    "12. Update state only through the existing Control Center workflow.",
    "13. Report evidence, results, unresolved blockers and the next controlled step.",
)


# ---------------------------------------------------------------------------
# SOURCE OF TRUTH MAP
# ---------------------------------------------------------------------------

SOURCE_OF_TRUTH: dict[str, str] = {
    "project_state": "REOS_CONTROL_CENTER/data/state.json",
    "code_and_history": "GitHub repository branch reos-development",
    "agent_policy": "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py",
    "control_center": "REOS_CONTROL_CENTER/reos_control_center.py",
    "implementation_write_interface": IMPLEMENTATION_WRITE_INTERFACE,
    "current_execution_evidence": (
        "Verified GitHub commit, branch readback, exact target content, "
        "focused tests and relevant CI evidence"
    ),
    "ps_output": "Evidence only",
    "continuity": "AUTONOMY_ENGINE/continuity/acrl",
    "new_session_bootstrap": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T07_New_Chat_Bootstrap/new_chat_bootstrap.py"
    ),
    "repository_context": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T14_Repository_Intelligence_Context"
    ),
    "ai_operator_boundary": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T15_AI_Operator_Autonomy"
    ),
    "execution_authorization": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard"
    ),
    "repair_verification": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T20_Autonomous_Repair_Patch_Verification"
    ),
    "git_repository_coordination": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T21_Git_Repository_Read_Write_Coordination"
    ),
    "commit_checkpoint_coordination": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T22_Commit_Execution_Checkpoint_Coordination"
    ),
    "evidence_resolution": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T23_Reference_Evidence_Resolution_Engine"
    ),
    "continuity_recovery": (
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T24_Cross_Chat_Continuity_Recovery_Engine"
    ),
    "chat_history": "NON_AUTHORITATIVE",
}


# ---------------------------------------------------------------------------
# NON-DEVELOPER OWNER WORKING CONTRACT
# ---------------------------------------------------------------------------

NON_DEVELOPER_OWNER_CONTRACT: tuple[str, ...] = (
    "The owner is not required to write or debug implementation code manually.",
    "Provide exact repository paths and clearly label each file action.",
    "Inspect canonical GitHub before instructing the owner to replace a file.",
    "Provide complete replacement content when full replacement is required.",
    "Do not require the owner to construct a patch from inferred fragments.",
    "Avoid unnecessary manual steps and unverified standalone sync scripts.",
    "Do not hide uncertainty behind a generic recommendation.",
    "Request targeted evidence when repository evidence is insufficient.",
)


# ---------------------------------------------------------------------------
# CHANGE DECISION RULE
# ---------------------------------------------------------------------------

CHANGE_DECISION_RULES: tuple[str, ...] = (
    "FIRST: inspect the current canonical GitHub repository state.",
    "SECOND: inspect existing ownership of the responsibility.",
    "THIRD: classify the requested action.",
    "FOURTH: determine whether the existing owner can be safely extended.",
    "FIFTH: add a file only when no existing owner exists and architecture permits it.",
    "SIXTH: verify completed-layer boundaries before implementation.",
    "NEVER: create duplicate modules, routes, components or sources of truth.",
    "NEVER: treat a stale local checkout as proof a file is missing.",
    "NEVER: reopen a completed layer without repository evidence.",
)


# ---------------------------------------------------------------------------
# FAILURE / RECOVERY RULES
# ---------------------------------------------------------------------------

FAILURE_RULES: tuple[str, ...] = (
    "If canonical repository state is unclear, reconstruct it before editing.",
    "If the exact target path has not been checked, do not classify it as ADD.",
    "If architecture authority is unclear, stop before architectural change.",
    "If local and remote evidence differs, treat canonical GitHub as code authority.",
    "If a file exists remotely but not locally, do not recreate it just to repair a stale checkout.",
    "If tests fail, diagnose the actual failure before changing the implementation.",
    "If an approved implementation is green, do not redesign it without evidence.",
    "If a change introduces duplicate responsibility, reject it.",
    "If execution authority is required but unavailable, fail closed.",
    "If project state cannot be safely reconstructed, do not manufacture state.",
    "If remote writes or manual saves cannot be independently verified, do not report PASS.",
)


# ---------------------------------------------------------------------------
# DISCOVERY HELPERS
# ---------------------------------------------------------------------------

def repository_paths() -> dict[str, str]:
    """Return important repository paths without reading or mutating state."""

    return {
        "control_center": str(CONTROL_CENTER_PATH),
        "state": str(STATE_PATH),
        "autonomy_engine": str(AUTONOMY_ENGINE_PATH),
        "acrl": str(ACRL_PATH),
        "t07": str(ACRL_ENTRYPOINT),
        "t14": str(ACRL_REPOSITORY_CONTEXT),
        "t15": str(ACRL_OPERATOR_AUTONOMY),
        "t18": str(ACRL_EXECUTION_AUTHORIZATION),
        "t20": str(ACRL_REPAIR_VERIFICATION),
        "t21": str(ACRL_GIT_REPOSITORY_COORDINATION),
        "t22": str(ACRL_COMMIT_CHECKPOINT_COORDINATION),
        "t23": str(ACRL_EVIDENCE_RESOLUTION),
        "t24": str(ACRL_CONTINUITY_RECOVERY),
    }


def contract() -> REOSAgentOperatingContract:
    """Return the repository-level AI operating contract."""

    return REOSAgentOperatingContract()


def startup_instructions() -> dict[str, Any]:
    """
    Return complete machine-readable instructions for a new AI session.

    This does not mutate state, execute project commands, authorize execution,
    change architecture or replace ACRL.
    """

    operating_contract = contract()

    return {
        "entrypoint": "AI_AGENT_ENTRYPOINT.py",
        "project": operating_contract.project,
        "project_description": operating_contract.project_description,
        "authority": operating_contract.control_authority,
        "continuity": operating_contract.continuity_system,
        "chat_history_authority": operating_contract.chat_history_authority,
        "canonical_code_source": CANONICAL_CODE_SOURCE,
        "implementation_write_interface": IMPLEMENTATION_WRITE_INTERFACE,
        "powershell_verification_only": POWERSHELL_IS_VERIFICATION_ONLY,
        "powershell_write_allowed": POWERSHELL_WRITE_ALLOWED,
        "powershell_remote_github_api_write_allowed": (
            POWERSHELL_REMOTE_GITHUB_API_WRITE_ALLOWED
        ),
        "powershell_local_worktree_write_allowed": (
            POWERSHELL_LOCAL_WORKTREE_WRITE_ALLOWED
        ),
        "powershell_local_git_mutation_allowed": (
            POWERSHELL_LOCAL_GIT_MUTATION_ALLOWED
        ),
        "powershell_write_mode": POWERSHELL_WRITE_MODE,
        "source_of_truth": dict(SOURCE_OF_TRUTH),
        "paths": repository_paths(),
        "operating_rules": list(AI_OPERATING_RULES),
        "development_workflow_rules": list(DEVELOPMENT_WORKFLOW_RULES),
        "file_change_classification": list(FILE_CHANGE_CLASSIFICATION),
        "repository_preflight_rules": list(REPOSITORY_PREFLIGHT_RULES),
        "git_preflight": git_preflight(),
        "new_session_workflow": list(NEW_SESSION_WORKFLOW),
        "execution_workflow": list(EXECUTION_WORKFLOW),
        "change_decision_rules": list(CHANGE_DECISION_RULES),
        "remote_git_synchronization_rules": list(
            REMOTE_GIT_SYNCHRONIZATION_RULES
        ),
        "failure_rules": list(FAILURE_RULES),
        "non_developer_owner_contract": list(
            NON_DEVELOPER_OWNER_CONTRACT
        ),
    }


def _run_git(*args: str) -> tuple[int, str, str]:
    """
    Run one Git command read-only from the Control Center.

    Only commands used by git_preflight are invoked here. No fetch, checkout,
    clean, commit, pull, push, reset, merge or ref-update command is issued.
    """

    import subprocess

    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=CONTROL_CENTER_PATH,
            text=True,
            capture_output=True,
            check=False,
        )
    except (FileNotFoundError, OSError) as exc:
        return 127, "", str(exc)

    return (
        completed.returncode,
        completed.stdout.strip(),
        completed.stderr.strip(),
    )


def _normalize_origin(value: str) -> str:
    """Normalize common GitHub HTTPS and SSH origins for comparison."""

    from urllib.parse import urlsplit

    origin = value.strip()

    if origin.startswith("git@github.com:"):
        origin = "https://github.com/" + origin.split(":", 1)[1]
    elif origin.startswith("ssh://git@github.com/"):
        origin = (
            "https://github.com/"
            + origin.split("ssh://git@github.com/", 1)[1]
        )

    if origin.startswith("https://"):
        parsed = urlsplit(origin)
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        origin = "https://" + hostname + parsed.path

    if origin.endswith(".git"):
        origin = origin[:-4]

    return origin.rstrip("/").lower()


# ---------------------------------------------------------------------------
# READ-ONLY LOCAL REPOSITORY PREFLIGHT
# ---------------------------------------------------------------------------

def git_preflight() -> dict[str, Any]:
    """
    Return a local repository readiness report.

    This function does not fetch or mutate Git state. Ahead/behind counts are
    calculated against the local cached upstream-tracking ref. Such a ref
    does not prove the current live server-side branch tip.

    Therefore:
    - dirty/untracked files block ready status;
    - missing upstream blocks ready status;
    - any ahead or behind commit blocks ready status;
    - live remote proof remains false and remote readback remains required;
    - authorization, remote writes and checkpoint evidence stay separate.
    """

    result: dict[str, Any] = {
        "canonical_workspace": str(CANONICAL_LOCAL_WORKSPACE),
        "canonical_control_center": str(CANONICAL_CONTROL_CENTER),
        "current_cwd": str(Path.cwd()),
        "repository_root": "",
        "branch": "",
        "origin": "",
        "local_head": "",
        "upstream_ref": "",
        "ahead_by": None,
        "behind_by": None,
        "cwd_ok": False,
        "control_center_ok": False,
        "repository_root_ok": False,
        "branch_ok": False,
        "origin_ok": False,
        "local_head_ok": False,
        "clean_worktree": False,
        "upstream_configured": False,
        "ahead_behind_ok": False,
        "divergent": False,
        "live_remote_tip_proven": False,
        "remote_readback_required": True,
        "t21_authority_ok": False,
        "ready": False,
    }

    result["cwd_ok"] = (
        Path.cwd().resolve()
        == CANONICAL_CONTROL_CENTER.resolve()
    )

    result["control_center_ok"] = (
        CONTROL_CENTER_PATH.resolve()
        == CANONICAL_CONTROL_CENTER.resolve()
    )

    code, root, _ = _run_git(
        "rev-parse",
        "--show-toplevel",
    )
    result["repository_root"] = root
    result["repository_root_ok"] = (
        code == 0
        and bool(root)
        and Path(root).resolve()
        == CANONICAL_LOCAL_WORKSPACE.resolve()
    )

    code, branch, _ = _run_git(
        "branch",
        "--show-current",
    )
    result["branch"] = branch
    result["branch_ok"] = (
        code == 0
        and branch == EXPECTED_BRANCH
    )

    code, origin, _ = _run_git(
        "config",
        "--get",
        "remote.origin.url",
    )
    result["origin"] = origin
    normalized_origin = _normalize_origin(origin)
    normalized_expected_origin = _normalize_origin(EXPECTED_ORIGIN)
    result["origin_ok"] = (
        code == 0
        and bool(normalized_origin)
        and normalized_origin == normalized_expected_origin
    )

    code, local_head, _ = _run_git(
        "rev-parse",
        "HEAD",
    )
    result["local_head"] = local_head
    result["local_head_ok"] = (
        code == 0
        and bool(local_head)
    )

    status_code, status_output, _ = _run_git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    result["clean_worktree"] = (
        status_code == 0
        and status_output == ""
    )

    upstream_code, upstream_ref, _ = _run_git(
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )
    result["upstream_ref"] = upstream_ref
    result["upstream_configured"] = (
        upstream_code == 0
        and bool(upstream_ref)
    )

    if result["upstream_configured"]:
        counts_code, counts_output, _ = _run_git(
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
        )

        try:
            count_parts = counts_output.split()

            if counts_code == 0 and len(count_parts) == 2:
                ahead_by = int(count_parts[0])
                behind_by = int(count_parts[1])

                if ahead_by < 0 or behind_by < 0:
                    raise ValueError(
                        "Git returned negative divergence counts."
                    )

                result["ahead_by"] = ahead_by
                result["behind_by"] = behind_by
                result["divergent"] = (
                    ahead_by > 0
                    and behind_by > 0
                )
                result["ahead_behind_ok"] = (
                    ahead_by == 0
                    and behind_by == 0
                )
        except (TypeError, ValueError):
            result["ahead_by"] = None
            result["behind_by"] = None
            result["divergent"] = False
            result["ahead_behind_ok"] = False

    # Tracking refs are local cached evidence, not live remote proof.
    result["live_remote_tip_proven"] = False
    result["remote_readback_required"] = True

    result["t21_authority_ok"] = (
        ACRL_GIT_REPOSITORY_COORDINATION.is_dir()
    )

    result["ready"] = all(
        (
            result["cwd_ok"],
            result["control_center_ok"],
            result["repository_root_ok"],
            result["branch_ok"],
            result["origin_ok"],
            result["local_head_ok"],
            result["clean_worktree"],
            result["upstream_configured"],
            result["ahead_behind_ok"],
            result["t21_authority_ok"],
        )
    )

    return result


def validate_entrypoint() -> bool:
    """
    Return True only when required architecture paths exist and the local
    read-only repository preflight is clean.
    """

    if not CONTROL_CENTER_PATH.is_dir():
        return False

    if not AUTONOMY_ENGINE_PATH.is_dir():
        return False

    if not ACRL_PATH.is_dir():
        return False

    if not STATE_PATH.is_file():
        return False

    if not ACRL_ENTRYPOINT.is_file():
        return False

    return bool(git_preflight()["ready"])


# ---------------------------------------------------------------------------
# HUMAN-READABLE STARTUP
# ---------------------------------------------------------------------------

def print_startup_context() -> None:
    """Print the current agent contract and read-only local preflight."""

    print("=" * 72)
    print("HOMIO / REOS — AI AGENT ENTRYPOINT")
    print("=" * 72)
    print(f"PROJECT        : {PROJECT_NAME}")
    print(f"AUTHORITY      : {CONTROL_CENTER_NAME}")
    print("CONTINUITY     : ACRL")
    print("CHAT HISTORY   : NON-AUTHORITATIVE")
    print("STATE          : REOS_CONTROL_CENTER/data/state.json")
    print("CODE SOURCE    : GitHub / reos-development")
    print("WRITE METHOD   : Guarded remote GitHub REST API writes")
    print(f"WORKSPACE      : {CANONICAL_LOCAL_WORKSPACE}")
    print(f"CONTROL CENTER : {CANONICAL_CONTROL_CENTER}")
    print(f"BRANCH         : {EXPECTED_BRANCH}")
    print(f"REPOSITORY     : {REPOSITORY_FULL_NAME}")

    preflight = git_preflight()
    print(f"CWD CHECK      : {preflight['cwd_ok']}")
    print(f"ROOT CHECK     : {preflight['repository_root_ok']}")
    print(f"BRANCH CHECK   : {preflight['branch_ok']}")
    print(f"ORIGIN CHECK   : {preflight['origin_ok']}")
    print(f"WORKTREE CLEAN : {preflight['clean_worktree']}")
    print(f"UPSTREAM SET   : {preflight['upstream_configured']}")
    print(f"AHEAD BY       : {preflight['ahead_by']}")
    print(f"BEHIND BY      : {preflight['behind_by']}")
    print(f"REMOTE PROVEN  : {preflight['live_remote_tip_proven']}")
    print(f"REMOTE READBACK REQUIRED: {preflight['remote_readback_required']}")
    print(f"T21 AUTHORITY  : {preflight['t21_authority_ok']}")

    print("-" * 72)
    for layer, title in (
        ("T07", "New Chat Bootstrap"),
        ("T14", "Repository Intelligence Context"),
        ("T15", "AI Operator Autonomy"),
        ("T18", "Safe Execution Authorization"),
        ("T20", "Repair / Patch Verification"),
        ("T21", "Git Repository Coordination"),
        ("T22", "Commit / Checkpoint Coordination"),
        ("T23", "Evidence Resolution"),
        ("T24", "Continuity / Recovery"),
    ):
        print(f"{layer:14}: {title}")

    print("-" * 72)
    print("RULE           : AUDIT BEFORE MODIFY")
    print("RULE           : CLASSIFY FILE ACTIONS")
    print("RULE           : CANONICAL GITHUB STATE FIRST")
    print("RULE           : NO DUPLICATE FILES OR ENGINES")
    print("RULE           : LOCAL WORKTREE WRITES FORBIDDEN")
    print("RULE           : REMOTE API WRITES GUARDED")
    print("RULE           : FAIL CLOSED ON UNCERTAINTY")
    print("-" * 72)
    print(
        "STATUS         :",
        "READY" if validate_entrypoint() else "VERIFY",
    )
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_startup_context()
