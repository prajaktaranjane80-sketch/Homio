"""
HOMIO / REOS ΓÇö AI AGENT ENTRYPOINT
==================================

Purpose
-------
This file is the repository-level entry point for ANY new AI/GPT agent
working on HOMIO / REOS.

It is NOT:
    - a second Control Center
    - a second ACRL
    - a second state store
    - an architecture engine
    - an execution engine
    - an authorization engine
    - an AI decision engine
    - a replacement for T07/T14/T15

It exists so that a new AI session can recover the correct operating
protocol from the repository without depending on previous GPT chat history.

AUTHORITATIVE PROJECT SOURCES
-----------------------------
1. REOS_CONTROL_CENTER/data/state.json
   -> canonical machine-readable project state

2. Git repository / current branch
   -> canonical code, history, architecture reference and repository evidence

3. Local PowerShell execution
   -> canonical current verification of the actual working tree

4. ACRL
   -> continuity, reconstruction, evidence, checkpoint, drift,
      recovery and AI-operation framework

CHAT HISTORY
------------
Chat history is communication only.
It is NOT project memory.
A new GPT session MUST NOT assume that previous chat context is available,
correct, current, or authoritative.

IMPORTANT
---------
This entrypoint does not contain a copy of the project state.

It tells an AI HOW TO DISCOVER the authoritative state and HOW TO WORK
inside the existing REOS / ACRL system.
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

# Canonical local repository identity.
# Descriptive/read-only contract only.
CANONICAL_LOCAL_WORKSPACE = Path(r"D:\HOMIO")
CANONICAL_CONTROL_CENTER = CANONICAL_LOCAL_WORKSPACE / CONTROL_CENTER_NAME
REPOSITORY_FULL_NAME = "prajaktaranjane80-sketch/Homio"
EXPECTED_BRANCH = "reos-development"
EXPECTED_ORIGIN = "https://github.com/prajaktaranjane80-sketch/Homio.git"

# PowerShell Output is evidence only.
PS_OUTPUT_IS_EVIDENCE_ONLY = True

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    "__pycache__/",
    "*.pyc",
    "*.pyo",
)

STATE_PATH = CONTROL_CENTER_PATH / "data" / "state.json"

AUTONOMY_ENGINE_PATH = (
    CONTROL_CENTER_PATH / "AUTONOMY_ENGINE"
)

ACRL_PATH = (
    AUTONOMY_ENGINE_PATH / "continuity" / "acrl"
)


# ---------------------------------------------------------------------------
# EXISTING CANONICAL ACRL COMPONENTS
# ---------------------------------------------------------------------------

ACRL_ENTRYPOINT = (
    ACRL_PATH
    / "T07_New_Chat_Bootstrap"
    / "new_chat_bootstrap.py"
)

ACRL_REPOSITORY_CONTEXT = (
    ACRL_PATH
    / "T14_Repository_Intelligence_Context"
)

ACRL_OPERATOR_AUTONOMY = (
    ACRL_PATH
    / "T15_AI_Operator_Autonomy"
)

ACRL_EXECUTION_AUTHORIZATION = (
    ACRL_PATH
    / "T18_Safe_Execution_Authorization_Guard"
)

ACRL_REPAIR_VERIFICATION = (
    ACRL_PATH
    / "T20_Autonomous_Repair_Patch_Verification"
)

ACRL_GIT_REPOSITORY_COORDINATION = (
    ACRL_PATH
    / "T21_Git_Repository_Read_Write_Coordination"
)

ACRL_COMMIT_CHECKPOINT_COORDINATION = (
    ACRL_PATH
    / "T22_Commit_Execution_Checkpoint_Coordination"
)

ACRL_EVIDENCE_RESOLUTION = (
    ACRL_PATH
    / "T23_Reference_Evidence_Resolution_Engine"
)

ACRL_CONTINUITY_RECOVERY = (
    ACRL_PATH
    / "T24_Cross_Chat_Continuity_Recovery_Engine"
)


# ---------------------------------------------------------------------------
# OPERATING AUTHORITY
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class REOSAgentOperatingContract:
    """
    Compact repository-level contract for a new AI operator.

    This is descriptive metadata only.
    It does not replace any ACRL or Control Center implementation.
    """

    project: str = PROJECT_NAME
    project_description: str = PROJECT_DESCRIPTION

    authoritative_state: str = (
        "REOS_CONTROL_CENTER/data/state.json"
    )

    authoritative_code_reference: str = (
        "Git repository / active REOS branch"
    )

    current_verification: str = (
        "Local PowerShell execution"
    )

    continuity_system: str = "ACRL"

    chat_history_authority: str = "NON_AUTHORITATIVE"

    control_authority: str = "REOS_CONTROL_CENTER"

    execution_authority: str = (
        "ACRL T18 authorization -> T20 repair verification -> "
        "PowerShell executor -> T21 Git transaction -> T22 checkpoint -> "
        "T23 evidence resolution -> T24 continuity recovery"
    )

    ai_role: str = (
        "Architecture-aware engineering operator"
    )


# ---------------------------------------------------------------------------
# AI OPERATING RULES
# ---------------------------------------------------------------------------

AI_OPERATING_RULES: tuple[str, ...] = (
    "Treat REOS_CONTROL_CENTER as the project control authority.",
    "Treat data/state.json as canonical machine-readable project state.",
    "Treat Git as canonical code/history/reference.",
    "Treat local PowerShell execution as current verification.",
    "Treat chat history as communication only, never as project truth.",
    "Before changing code, reconstruct the current repository state.",
    "Use existing ACRL continuity mechanisms instead of inventing new continuity.",
    "Use T07 New Chat Bootstrap for new-session continuity.",
    "Use T14 Repository Intelligence Context for repository-aware context.",
    "Respect T15 AI Operator Autonomy boundaries.",
    "Do not bypass architecture locks.",
    "Do not bypass Control Center authority.",
    "Do not directly invent or modify authoritative project state.",
    "Do not create a second state store.",
    "Do not create a second Control Center.",
    "Do not create a second ACRL.",
    "Do not create duplicate business engines.",
    "Do not replace existing modules when an existing module already owns the responsibility.",
    "Do not infer local files merely because they exist in Git history or a remote snapshot.",
    "Verify the actual local working tree before depending on a file.",
    "Do not blindly patch from assumptions.",
    "Use targeted evidence before making a change.",
    "Prefer the smallest architecture-consistent change.",
    "Run focused verification after a change.",
    "Run relevant regression verification before declaring success.",
    "Do not declare a task complete from code appearance alone.",
    "Do not manipulate state.json directly to manufacture completion.",
    "Do not self-authorize execution.",
    "Do not self-approve architecture or governance decisions.",
    "When evidence conflicts, stop and resolve the conflict instead of guessing.",
)


# ---------------------------------------------------------------------------
# REMOTE GIT SYNCHRONIZATION CONTRACT
# ---------------------------------------------------------------------------

REMOTE_GIT_SYNCHRONIZATION_RULES: tuple[str, ...] = (
    "REOS_CONTROL_CENTER remains the project control authority.",
    "REOS_CONTROL_CENTER/data/state.json remains the canonical project state.",
    "ACRL T18 is the execution-authorization boundary.",
    "ACRL T20 is the repair and patch-verification boundary.",
    "Local PowerShell is the actual execution and current-working-tree verification interface.",
    "ACRL T21 is the Git repository read/write transaction boundary.",
    "ACRL T22 is the immutable commit execution checkpoint boundary.",
    "ACRL T23 is the authority for missing, stale or conflicting evidence resolution.",
    "ACRL T24 is the authority for continuity and recovery snapshots.",
    "PowerShell MUST NOT create a second synchronization engine.",
    "AI_AGENT_ENTRYPOINT.py is descriptive contract only and MUST NOT execute Git writes.",
    "A remote write is successful only after independent branch, commit and file evidence verification.",
    "The active REOS branch MUST be verified before any repository write.",
    "A failed, ambiguous or conflicting operation MUST fail closed.",
    "Do not create a second Git sync engine.",
    "Do not create a second checkpoint engine.",
    "Do not create a second evidence engine.",
    "Do not create a second continuity engine.",
    "Do not create a second state store.",
    "Do not bypass REOS Control Center authority.",
)

# ---------------------------------------------------------------------------
# REPOSITORY PREFLIGHT CONTRACT
# ---------------------------------------------------------------------------

REPOSITORY_PREFLIGHT_RULES: tuple[str, ...] = (
    "Canonical workspace is D:\\HOMIO.",
    "Canonical Control Center is D:\\HOMIO\\REOS_CONTROL_CENTER.",
    "Git repository root is D:\\HOMIO.",
    "Expected repository is prajaktaranjane80-sketch/Homio.",
    "Expected branch is reos-development.",
    "Expected origin resolves to the canonical GitHub repository.",
    "Current working directory must be the canonical Control Center.",
    "Repository root must resolve to the canonical Control Center.",
    "Generated Python caches are artifacts, never project source or state.",
    "PS Output is evidence only.",
    "AI_AGENT_ENTRYPOINT.py does not own Git synchronization.",
    "ACRL T21 is the single Git repository read/write coordination authority.",
    "ACRL T21 performs branch/HEAD/push/remote verification for Git transactions.",
    "T07 remains the new-chat bootstrap authority.",
    "T18 remains the execution-authorization authority.",
    "T20 remains the repair-verification authority.",
    "T22 remains the immutable checkpoint authority.",
    "T23 remains the evidence-resolution authority.",
    "T24 remains the continuity/recovery authority.",
)

# ---------------------------------------------------------------------------
# EXECUTION / SYNCHRONIZATION WORKFLOW
# ---------------------------------------------------------------------------

EXECUTION_WORKFLOW: tuple[str, ...] = (
    "1. Discover canonical state from REOS_CONTROL_CENTER/data/state.json.",
    "2. Resolve the authoritative current gate/task/subtask through REOS Control Center.",
    "3. Resolve architecture and dependency ownership before changing code.",
    "4. Obtain execution authorization through existing ACRL T18.",
    "5. Verify the proposed repair/patch through existing ACRL T20.",
    "6. Execute the authorized local change through PowerShell.",
    "7. Verify the changed working tree and focused tests locally.",
    "8. Coordinate Git mutation through existing ACRL T21.",
    "9. Create/verify the immutable execution checkpoint through T22 when required.",
    "10. Resolve execution evidence through T23.",
    "11. Preserve/recover continuity through T24 when required.",
    "12. Update canonical project state only through the existing REOS Control Center workflow.",
    "13. Never report PASS without independent verification evidence.",
)
# ---------------------------------------------------------------------------
# REQUIRED NEW-SESSION WORKFLOW
# ---------------------------------------------------------------------------

NEW_SESSION_WORKFLOW: tuple[str, ...] = (
    "1. Identify this repository as HOMIO / REOS.",
    "2. Read this entrypoint.",
    "3. Discover the existing ACRL T07 New Chat Bootstrap.",
    "4. Reconstruct current project state from REOS_CONTROL_CENTER.",
    "5. Inspect the current gate, task and subtask from canonical state.",
    "6. Inspect relevant architecture and dependency authority.",
    "7. Inspect the actual local repository tree before assuming files exist.",
    "8. Inspect relevant implementation and existing tests.",
    "9. Determine the smallest valid change.",
    "10. Execute only through the existing REOS-controlled workflow.",
    "11. Verify the changed scope.",
    "12. Run relevant regression tests.",
    "13. Update project state only through the existing Control Center workflow.",
    "14. Preserve checkpoint / continuity information when required.",
    "15. Report evidence, result and next controlled step.",
)


# ---------------------------------------------------------------------------
# SOURCE OF TRUTH MAP
# ---------------------------------------------------------------------------

SOURCE_OF_TRUTH: dict[str, str] = {
    "project_state": "REOS_CONTROL_CENTER/data/state.json",
    "code_and_history": "Git repository",
    "current_execution_evidence": "Local PowerShell",
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
    "The project owner is not required to write or debug implementation code manually.",
    "The AI must provide exact repository paths for every requested file change.",
    "The AI must provide complete replacement content when a full file replacement is required.",
    "The AI must provide exact PowerShell commands for file creation or replacement.",
    "The AI must avoid asking the owner to perform unnecessary manual code editing.",
    "The AI must verify before instructing the owner to replace a file.",
    "The AI must never hide a structural uncertainty behind a generic recommendation.",
    "If the repository evidence is insufficient, the AI must request targeted evidence rather than guess.",
)


# ---------------------------------------------------------------------------
# CHANGE DECISION RULE
# ---------------------------------------------------------------------------

CHANGE_DECISION_RULES: tuple[str, ...] = (
    "FIRST: determine whether an existing module already owns the required responsibility.",
    "SECOND: determine whether the existing module can be minimally extended.",
    "THIRD: add a new module only when no existing owner exists and architecture permits it.",
    "NEVER: create a duplicate module merely because discovery is inconvenient.",
    "NEVER: create a parallel source of truth.",
    "NEVER: create a parallel execution path.",
)


# ---------------------------------------------------------------------------
# FAILURE / RECOVERY RULES
# ---------------------------------------------------------------------------

FAILURE_RULES: tuple[str, ...] = (
    "If repository state is unclear, reconstruct it before editing.",
    "If architecture authority is unclear, stop before architectural change.",
    "If local and remote repository evidence differs, verify locally.",
    "If tests fail, diagnose the actual failure before patching.",
    "If an existing implementation is approved and green, do not redesign it without evidence.",
    "If a proposed change creates duplicate responsibility, reject the change.",
    "If execution authority is unavailable, fail closed.",
    "If project state cannot be safely reconstructed, do not manufacture state.",
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
    Return the complete machine-readable instructions for a new AI session.

    This function does NOT:
        - mutate state
        - execute project commands
        - authorize execution
        - change architecture
        - replace ACRL
    """

    operating_contract = contract()

    return {
        "entrypoint": "AI_AGENT_ENTRYPOINT.py",
        "project": operating_contract.project,
        "project_description": operating_contract.project_description,
        "authority": operating_contract.control_authority,
        "continuity": operating_contract.continuity_system,
        "chat_history_authority": operating_contract.chat_history_authority,
        "source_of_truth": dict(SOURCE_OF_TRUTH),
        "paths": repository_paths(),
        "operating_rules": list(AI_OPERATING_RULES),
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
    """Run a read-only Git command from the canonical Control Center."""

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
    """Normalize common GitHub HTTPS/SSH origins."""

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
        origin = (
            "https://"
            + parsed.hostname.lower()
            + parsed.path
        )

    if origin.endswith(".git"):
        origin = origin[:-4]

    return origin.rstrip("/").lower()


def git_preflight() -> dict[str, Any]:
    """
    Return a read-only local repository identity/preflight report.

    Git synchronization, transaction, commit and remote verification
    remain owned exclusively by ACRL T21.
    """

    result: dict[str, Any] = {
        "canonical_workspace": str(
            CANONICAL_LOCAL_WORKSPACE
        ),
        "canonical_control_center": str(
            CANONICAL_CONTROL_CENTER
        ),
        "current_cwd": str(Path.cwd()),
        "repository_root": "",
        "branch": "",
        "origin": "",
        "local_head": "",
        "cwd_ok": False,
        "control_center_ok": False,
        "repository_root_ok": False,
        "branch_ok": False,
        "origin_ok": False,
        "local_head_ok": False,
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

    result["origin_ok"] = (
        code == 0
        and (
            origin.rstrip("/").removesuffix(".git").lower()
            == EXPECTED_ORIGIN.rstrip(
                "/"
            ).removesuffix(".git").lower()
        )
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
            result["t21_authority_ok"],
        )
    )

    return result


def validate_entrypoint() -> bool:
    """Return True only when structural and repository preflight is clean."""

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
    """Print a compact new-AI startup contract."""

    print("=" * 72)
    print("HOMIO / REOS ΓÇö AI AGENT ENTRYPOINT")
    print("=" * 72)
    print(f"PROJECT        : {PROJECT_NAME}")
    print(f"AUTHORITY      : {CONTROL_CENTER_NAME}")
    print("CONTINUITY     : ACRL")
    print("CHAT HISTORY   : NON-AUTHORITATIVE")
    print("STATE          : REOS_CONTROL_CENTER/data/state.json")
    print("CODE           : Git repository")
    print("VERIFICATION   : Local PowerShell")
    print(f"WORKSPACE      : {CANONICAL_LOCAL_WORKSPACE}")
    print(f"CONTROL CENTER : {CANONICAL_CONTROL_CENTER}")
    print(f"BRANCH         : {EXPECTED_BRANCH}")
    print(f"REPOSITORY     : {REPOSITORY_FULL_NAME}")

    preflight = git_preflight()

    print(f"CWD CHECK      : {preflight['cwd_ok']}")
    print(f"BRANCH CHECK   : {preflight['branch_ok']}")
    print(f"ORIGIN CHECK   : {preflight['origin_ok']}")
    print(
        f"T21 AUTHORITY  : "
        f"{preflight['t21_authority_ok']}"
    )
    print("T07            : New Chat Bootstrap")
    print("T14            : Repository Intelligence Context")
    print("T15            : AI Operator Autonomy")
    print("T18            : Safe Execution Authorization")
    print("T20            : Repair / Patch Verification")
    print("T21            : Git Repository Coordination")
    print("T22            : Commit Execution Checkpoint")
    print("T23            : Evidence Resolution")
    print("T24            : Continuity Recovery")
    print("-" * 72)
    print("RULE           : DISCOVER BEFORE MODIFY")
    print("RULE           : NO DUPLICATE ENGINES")
    print("RULE           : NO DUPLICATE STATE")
    print("RULE           : NO BLIND PATCHING")
    print("RULE           : FAIL CLOSED ON UNCERTAINTY")
    print("-" * 72)
    print("STATUS         :", "READY" if validate_entrypoint() else "VERIFY")
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_startup_context()
