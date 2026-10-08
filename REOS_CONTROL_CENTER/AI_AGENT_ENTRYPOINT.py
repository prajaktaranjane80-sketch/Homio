"""
HOMIO / REOS — AI AGENT ENTRYPOINT
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

2. GitHub repository branch reos-development
   -> canonical implementation source, code, history, architecture
      reference and repository evidence

3. Local PowerShell execution
   -> verification and diagnosis only

4. ACRL
   -> continuity, reconstruction, evidence, checkpoint, drift,
      recovery and AI-operation framework

CHAT HISTORY
------------
Chat history is communication only.
It is NOT project memory.

A new GPT session MUST NOT assume that previous chat context is:
    - available
    - correct
    - current
    - authoritative

IMPORTANT
---------
This entrypoint does not contain a copy of the project state.

It tells an AI HOW TO DISCOVER the authoritative state and HOW TO WORK
inside the existing REOS / ACRL system.

The implementation workflow must protect against:
    - stale local workspaces
    - duplicate files
    - duplicate routes
    - duplicate components
    - duplicate engines
    - unnecessary reopening of completed layers
    - blind replacement
    - guessed repository structure
    - accidental PowerShell code mutation
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
CANONICAL_CONTROL_CENTER = (
    CANONICAL_LOCAL_WORKSPACE / CONTROL_CENTER_NAME
)

REPOSITORY_FULL_NAME = "prajaktaranjane80-sketch/Homio"

EXPECTED_BRANCH = "reos-development"

EXPECTED_ORIGIN = (
    "https://github.com/prajaktaranjane80-sketch/Homio.git"
)

# Canonical implementation source.
CANONICAL_CODE_SOURCE = (
    "GitHub repository branch reos-development"
)

# Manual owner-controlled development workflow.
IMPLEMENTATION_WRITE_INTERFACE = (
    "Manual GitHub file save on branch reos-development"
)

# PowerShell is verification/diagnosis only.
POWERSHELL_WRITE_ALLOWED = False
POWERSHELL_IS_VERIFICATION_ONLY = True

# PowerShell Output is evidence only.
PS_OUTPUT_IS_EVIDENCE_ONLY = True

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    "__pycache__/",
    "*.pyc",
    "*.pyo",
)

STATE_PATH = (
    CONTROL_CENTER_PATH
    / "data"
    / "state.json"
)

AUTONOMY_ENGINE_PATH = (
    CONTROL_CENTER_PATH / "AUTONOMY_ENGINE"
)

ACRL_PATH = (
    AUTONOMY_ENGINE_PATH
    / "continuity"
    / "acrl"
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
        "GitHub repository branch reos-development"
    )

    implementation_write_interface: str = (
        IMPLEMENTATION_WRITE_INTERFACE
    )

    current_verification: str = (
        "Local PowerShell verification and diagnosis only"
    )

    continuity_system: str = "ACRL"

    chat_history_authority: str = "NON_AUTHORITATIVE"

    control_authority: str = "REOS_CONTROL_CENTER"

    execution_authority: str = (
        "REOS Control Center and applicable ACRL authorization, "
        "repair-verification, evidence and checkpoint boundaries"
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
    "Treat GitHub branch reos-development as the canonical code and implementation source.",
    "Treat chat history as communication only, never as project truth.",
    "Treat local PowerShell as verification and diagnosis only.",
    "Do not use PowerShell to create, replace, patch, reset, merge or push project code.",
    "Before changing code, reconstruct the current repository state.",
    "Before proposing a file change, inspect the exact target path on the canonical GitHub branch.",
    "Before creating a new file, confirm that the target path is actually absent on the canonical branch.",
    "Before creating a new component, route or module, confirm that an existing component, route or module does not already own the responsibility.",
    "Classify every requested file action as ADD, REPLACE or NO CHANGE before providing implementation instructions.",
    "Do not create a duplicate file merely because a stale local workspace does not contain the file.",
    "Do not create a duplicate route when an existing route already owns the experience.",
    "Do not create a duplicate component when an existing component already owns the responsibility.",
    "Do not reopen a completed feature layer unless repository evidence shows a real dependency, regression or required integration change.",
    "When a new layer depends on a completed layer, reuse the completed layer instead of rebuilding it.",
    "Do not assume that a local checkout is current merely because it exists.",
    "Do not allow stale local repository state to override canonical GitHub repository evidence.",
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
    "Do not blindly patch from assumptions.",
    "Use targeted repository evidence before making a change.",
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
# DEVELOPMENT WORKFLOW CONTRACT
# ---------------------------------------------------------------------------

DEVELOPMENT_WORKFLOW_RULES: tuple[str, ...] = (
    "GitHub branch reos-development is the canonical implementation source.",
    "Manual GitHub file saving is the approved owner-controlled implementation write workflow.",
    "PowerShell is verification and diagnosis only.",
    "PowerShell MUST NOT be used to write, patch, reset, merge or push project code.",
    "Before every requested change, inspect the canonical GitHub repository state.",
    "Every requested file must be classified as ADD, REPLACE or NO CHANGE.",
    "ADD means the exact target path is absent on the canonical branch and no existing owner satisfies the responsibility.",
    "REPLACE means the exact target path exists and the requested change belongs in that existing file.",
    "NO CHANGE means the existing implementation already satisfies the requested responsibility or no repository evidence justifies modification.",
    "A completed layer must not be rebuilt merely because a dependent layer is being started.",
    "A new layer must reuse completed-layer routes, components and contracts wherever the architecture allows.",
    "A stale local workspace must never be used as proof that a canonical GitHub file is missing.",
    "The AI must provide exact repository path, ADD/REPLACE/NO CHANGE action, anchor or location, and complete file content for manual GitHub editing.",
    "When a full replacement is required, the AI must provide the complete replacement file rather than an inferred patch.",
    "When only a small verified change is required, the AI may still provide complete replacement content when the owner is safer using full-file replacement.",
    "After a manual GitHub save, the remote branch and changed file must be independently verified before PASS is declared.",
    "Local PowerShell verification may be used only after the canonical GitHub state is established.",
)


# ---------------------------------------------------------------------------
# REMOTE GIT SYNCHRONIZATION CONTRACT
# ---------------------------------------------------------------------------

REMOTE_GIT_SYNCHRONIZATION_RULES: tuple[str, ...] = (
    "REOS_CONTROL_CENTER remains the project control authority.",
    "REOS_CONTROL_CENTER/data/state.json remains the canonical project state.",
    "GitHub branch reos-development remains the canonical code source.",
    "Manual GitHub file saving is the owner-controlled code implementation workflow.",
    "Local PowerShell is verification and diagnosis only.",
    "PowerShell MUST NOT perform repository code writes.",
    "AI_AGENT_ENTRYPOINT.py is a descriptive repository contract and MUST NOT execute Git writes.",
    "ACRL T18 remains the execution-authorization boundary where applicable.",
    "ACRL T20 remains the repair and patch-verification boundary where applicable.",
    "ACRL T21 remains the Git repository coordination boundary for ACRL-controlled Git transactions.",
    "ACRL T22 remains the immutable checkpoint boundary where required.",
    "ACRL T23 remains the authority for missing, stale or conflicting evidence resolution.",
    "ACRL T24 remains the authority for continuity and recovery snapshots.",
    "A remote write is successful only after independent branch, commit and file evidence verification.",
    "The active REOS branch MUST be verified before repository work is considered authoritative.",
    "A failed, ambiguous or conflicting operation MUST fail closed.",
    "Do not create a second Git synchronization engine.",
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
    "Canonical local workspace is D:\\HOMIO.",
    "Canonical Control Center is D:\\HOMIO\\REOS_CONTROL_CENTER.",
    "Expected repository is prajaktaranjane80-sketch/Homio.",
    "Expected branch is reos-development.",
    "Expected origin resolves to the canonical GitHub repository.",
    "GitHub reos-development is the implementation source of truth.",
    "Local workspace may be stale and must not override canonical GitHub evidence.",
    "Current working directory is used only for read-only verification.",
    "Generated Python caches are artifacts, never project source or state.",
    "PS Output is evidence only.",
    "AI_AGENT_ENTRYPOINT.py does not own Git synchronization.",
    "AI_AGENT_ENTRYPOINT.py does not perform implementation writes.",
    "ACRL T21 remains the Git coordination authority for ACRL-controlled transactions.",
    "T07 remains the new-chat bootstrap authority.",
    "T14 remains the repository-intelligence context authority.",
    "T15 remains the AI-operator boundary authority.",
    "T18 remains the execution-authorization authority.",
    "T20 remains the repair-verification authority.",
    "T22 remains the immutable checkpoint authority.",
    "T23 remains the evidence-resolution authority.",
    "T24 remains the continuity/recovery authority.",
)


# ---------------------------------------------------------------------------
# FILE CHANGE CLASSIFICATION
# ---------------------------------------------------------------------------

FILE_CHANGE_CLASSIFICATION: tuple[str, ...] = (
    "ADD = exact target path is absent from canonical GitHub branch reos-development and no existing owner performs the required responsibility.",
    "REPLACE = exact target path already exists and the required responsibility belongs in that existing file.",
    "NO CHANGE = exact target path already exists and repository evidence shows that changing it is unnecessary.",
    "Existing route/component/module ownership takes precedence over creating a new duplicate.",
    "A missing file in a stale local checkout is NOT sufficient evidence for ADD.",
    "A new feature layer does NOT automatically justify changes to a completed previous layer.",
    "A previous layer may be changed only when a verified dependency, integration requirement or regression requires it.",
)


# ---------------------------------------------------------------------------
# EXECUTION / IMPLEMENTATION WORKFLOW
# ---------------------------------------------------------------------------

EXECUTION_WORKFLOW: tuple[str, ...] = (
    "1. Discover canonical project state from REOS_CONTROL_CENTER/data/state.json.",
    "2. Verify the active branch and canonical GitHub repository reference.",
    "3. Inspect the exact requested target paths on canonical GitHub.",
    "4. Inspect existing related routes, components, modules and verifiers.",
    "5. Determine responsibility ownership before creating anything new.",
    "6. Classify every requested file as ADD, REPLACE or NO CHANGE.",
    "7. Resolve architecture and dependency ownership before implementation.",
    "8. Apply applicable ACRL authorization and repair-verification boundaries.",
    "9. Prepare exact implementation instructions for the non-developer owner.",
    "10. Save implementation changes manually on canonical GitHub branch reos-development.",
    "11. Independently verify the remote branch and changed files after the manual GitHub save.",
    "12. Use local PowerShell only for read-only verification and diagnosis.",
    "13. Run focused verification for the changed scope.",
    "14. Run relevant regression verification before declaring success.",
    "15. Resolve evidence through T23 when evidence is missing, stale or conflicting.",
    "16. Preserve checkpoint / continuity information through the applicable ACRL boundary.",
    "17. Update canonical project state only through the existing REOS Control Center workflow.",
    "18. Never report PASS without independent verification evidence.",
)


# ---------------------------------------------------------------------------
# REQUIRED NEW-SESSION WORKFLOW
# ---------------------------------------------------------------------------

NEW_SESSION_WORKFLOW: tuple[str, ...] = (
    "1. Identify this repository as HOMIO / REOS.",
    "2. Read this entrypoint.",
    "3. Discover the existing ACRL T07 New Chat Bootstrap.",
    "4. Reconstruct current project state from REOS_CONTROL_CENTER.",
    "5. Verify canonical GitHub branch reos-development.",
    "6. Inspect the active gate, task and subtask from canonical state.",
    "7. Inspect relevant architecture and dependency authority.",
    "8. Inspect the exact canonical GitHub paths relevant to the active work.",
    "9. Inspect existing routes, modules, components and tests before proposing additions.",
    "10. Classify required file actions as ADD, REPLACE or NO CHANGE.",
    "11. Do not infer missing files from a stale local workspace.",
    "12. Determine the smallest valid architecture-consistent change.",
    "13. Prepare exact GitHub manual-save instructions for the owner.",
    "14. Verify the remote GitHub result.",
    "15. Use PowerShell only for verification or diagnosis.",
    "16. Run relevant regression tests.",
    "17. Update project state only through the existing Control Center workflow.",
    "18. Preserve checkpoint / continuity information when required.",
    "19. Report evidence, result and next controlled step.",
)


# ---------------------------------------------------------------------------
# SOURCE OF TRUTH MAP
# ---------------------------------------------------------------------------

SOURCE_OF_TRUTH: dict[str, str] = {
    "project_state": (
        "REOS_CONTROL_CENTER/data/state.json"
    ),
    "code_and_history": (
        "GitHub repository branch reos-development"
    ),
    "implementation_write_interface": (
        "Manual GitHub file save on branch reos-development"
    ),
    "current_execution_evidence": (
        "Local PowerShell verification and diagnosis"
    ),
    "ps_output": "Evidence only",
    "continuity": (
        "AUTONOMY_ENGINE/continuity/acrl"
    ),
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
    "The AI must inspect the canonical GitHub branch before instructing the owner to change a file.",
    "The AI must classify every requested file as ADD, REPLACE or NO CHANGE.",
    "The AI must provide the exact repository path for every requested file change.",
    "The AI must clearly state ADD, REPLACE or NO CHANGE for every requested file.",
    "The AI must provide an exact anchor, section or location when a targeted change is appropriate.",
    "The AI must provide complete replacement content when a full file replacement is required.",
    "The AI must not require the owner to construct code from inferred patches.",
    "The AI must not provide PowerShell commands for project code creation or replacement.",
    "The AI must reserve PowerShell instructions for read-only verification and diagnosis.",
    "The AI must avoid asking the owner to perform unnecessary manual code editing.",
    "The AI must verify the repository state before instructing the owner to replace a file.",
    "The AI must never hide structural uncertainty behind a generic recommendation.",
    "If repository evidence is insufficient, the AI must request targeted evidence rather than guess.",
)


# ---------------------------------------------------------------------------
# CHANGE DECISION RULE
# ---------------------------------------------------------------------------

CHANGE_DECISION_RULES: tuple[str, ...] = (
    "FIRST: inspect the current canonical GitHub repository state.",
    "SECOND: determine whether an existing file, route, component or module already owns the required responsibility.",
    "THIRD: classify the requested action as ADD, REPLACE or NO CHANGE.",
    "FOURTH: determine whether the existing owner can be minimally extended.",
    "FIFTH: add a new file or module only when no existing owner exists and architecture permits it.",
    "SIXTH: verify the change against completed-layer boundaries before implementation.",
    "NEVER: create a duplicate module merely because discovery is inconvenient.",
    "NEVER: create a duplicate route when an existing route owns the experience.",
    "NEVER: create a duplicate component when an existing component owns the responsibility.",
    "NEVER: treat a stale local checkout as proof that a file is missing.",
    "NEVER: reopen a completed layer without repository evidence.",
    "NEVER: create a parallel source of truth.",
    "NEVER: create a parallel execution path.",
)


# ---------------------------------------------------------------------------
# FAILURE / RECOVERY RULES
# ---------------------------------------------------------------------------

FAILURE_RULES: tuple[str, ...] = (
    "If canonical repository state is unclear, reconstruct it before editing.",
    "If the exact target path has not been checked on canonical GitHub, do not classify it as ADD.",
    "If architecture authority is unclear, stop before architectural change.",
    "If local and remote repository evidence differs, treat canonical GitHub state as implementation authority and use local PowerShell only to diagnose the difference.",
    "If a file exists remotely but not locally, do not recreate it merely to repair the local checkout.",
    "If tests fail, diagnose the actual failure before patching.",
    "If an existing implementation is approved and green, do not redesign it without evidence.",
    "If a proposed change creates duplicate responsibility, reject the change.",
    "If a proposed change unnecessarily reopens a completed layer, reject the change.",
    "If execution authority is unavailable for a change that requires it, fail closed.",
    "If project state cannot be safely reconstructed, do not manufacture state.",
    "If a remote manual GitHub save cannot be independently verified, do not report PASS.",
)


# ---------------------------------------------------------------------------
# DISCOVERY HELPERS
# ---------------------------------------------------------------------------

def repository_paths() -> dict[str, str]:
    """Return important repository paths without reading or mutating state."""

    return {
        "control_center": str(
            CONTROL_CENTER_PATH
        ),
        "state": str(STATE_PATH),
        "autonomy_engine": str(
            AUTONOMY_ENGINE_PATH
        ),
        "acrl": str(ACRL_PATH),
        "t07": str(ACRL_ENTRYPOINT),
        "t14": str(ACRL_REPOSITORY_CONTEXT),
        "t15": str(ACRL_OPERATOR_AUTONOMY),
        "t18": str(ACRL_EXECUTION_AUTHORIZATION),
        "t20": str(ACRL_REPAIR_VERIFICATION),
        "t21": str(
            ACRL_GIT_REPOSITORY_COORDINATION
        ),
        "t22": str(
            ACRL_COMMIT_CHECKPOINT_COORDINATION
        ),
        "t23": str(
            ACRL_EVIDENCE_RESOLUTION
        ),
        "t24": str(
            ACRL_CONTINUITY_RECOVERY
        ),
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
        "project_description": (
            operating_contract.project_description
        ),
        "authority": operating_contract.control_authority,
        "continuity": operating_contract.continuity_system,
        "chat_history_authority": (
            operating_contract.chat_history_authority
        ),
        "canonical_code_source": CANONICAL_CODE_SOURCE,
        "implementation_write_interface": (
            IMPLEMENTATION_WRITE_INTERFACE
        ),
        "powershell_verification_only": (
            POWERSHELL_IS_VERIFICATION_ONLY
        ),
        "powershell_write_allowed": (
            POWERSHELL_WRITE_ALLOWED
        ),
        "source_of_truth": dict(SOURCE_OF_TRUTH),
        "paths": repository_paths(),
        "operating_rules": list(
            AI_OPERATING_RULES
        ),
        "development_workflow_rules": list(
            DEVELOPMENT_WORKFLOW_RULES
        ),
        "file_change_classification": list(
            FILE_CHANGE_CLASSIFICATION
        ),
        "repository_preflight_rules": list(
            REPOSITORY_PREFLIGHT_RULES
        ),
        "git_preflight": git_preflight(),
        "new_session_workflow": list(
            NEW_SESSION_WORKFLOW
        ),
        "execution_workflow": list(
            EXECUTION_WORKFLOW
        ),
        "change_decision_rules": list(
            CHANGE_DECISION_RULES
        ),
        "remote_git_synchronization_rules": list(
            REMOTE_GIT_SYNCHRONIZATION_RULES
        ),
        "failure_rules": list(
            FAILURE_RULES
        ),
        "non_developer_owner_contract": list(
            NON_DEVELOPER_OWNER_CONTRACT
        ),
    }


def _run_git(*args: str) -> tuple[int, str, str]:
    """
    Run a read-only Git command from the canonical Control Center.
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
    """Normalize common GitHub HTTPS/SSH origins."""

    from urllib.parse import urlsplit

    origin = value.strip()

    if origin.startswith("git@github.com:"):
        origin = (
            "https://github.com/"
            + origin.split(":", 1)[1]
        )

    elif origin.startswith("ssh://git@github.com/"):
        origin = (
            "https://github.com/"
            + origin.split(
                "ssh://git@github.com/",
                1,
            )[1]
        )

    if origin.startswith("https://"):
        parsed = urlsplit(origin)
        hostname = (
            parsed.hostname.lower()
            if parsed.hostname
            else ""
        )
        origin = (
            "https://"
            + hostname
            + parsed.path
        )

    if origin.endswith(".git"):
        origin = origin[:-4]

    return origin.rstrip("/").lower()


def git_preflight() -> dict[str, Any]:
    """
    Return a read-only local repository identity/preflight report.

    Git synchronization, transaction, commit and remote verification
    remain owned by the applicable repository workflow boundaries.
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

    normalized_origin = _normalize_origin(
        origin
    )

    normalized_expected_origin = _normalize_origin(
        EXPECTED_ORIGIN
    )

    result["origin_ok"] = (
        code == 0
        and normalized_origin
        == normalized_expected_origin
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
    """
    Return True only when structural and local read-only
    repository preflight is clean.
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

    return bool(
        git_preflight()["ready"]
    )


# ---------------------------------------------------------------------------
# HUMAN-READABLE STARTUP
# ---------------------------------------------------------------------------

def print_startup_context() -> None:
    """Print a compact new-AI startup contract."""

    print("=" * 72)
    print("HOMIO / REOS — AI AGENT ENTRYPOINT")
    print("=" * 72)

    print(f"PROJECT        : {PROJECT_NAME}")
    print(
        f"AUTHORITY      : {CONTROL_CENTER_NAME}"
    )
    print("CONTINUITY     : ACRL")
    print("CHAT HISTORY   : NON-AUTHORITATIVE")
    print(
        "STATE          : "
        "REOS_CONTROL_CENTER/data/state.json"
    )
    print(
        "CODE SOURCE    : "
        "GitHub / reos-development"
    )
    print(
        "WRITE METHOD   : "
        "Manual GitHub file save"
    )
    print(
        "POWERSHELL     : "
        "Verification / diagnosis only"
    )
    print(
        f"WORKSPACE      : "
        f"{CANONICAL_LOCAL_WORKSPACE}"
    )
    print(
        f"CONTROL CENTER : "
        f"{CANONICAL_CONTROL_CENTER}"
    )
    print(
        f"BRANCH         : "
        f"{EXPECTED_BRANCH}"
    )
    print(
        f"REPOSITORY     : "
        f"{REPOSITORY_FULL_NAME}"
    )

    preflight = git_preflight()

    print(
        f"CWD CHECK      : "
        f"{preflight['cwd_ok']}"
    )
    print(
        f"BRANCH CHECK   : "
        f"{preflight['branch_ok']}"
    )
    print(
        f"ORIGIN CHECK   : "
        f"{preflight['origin_ok']}"
    )
    print(
        f"T21 AUTHORITY  : "
        f"{preflight['t21_authority_ok']}"
    )

    print(
        "T07            : New Chat Bootstrap"
    )
    print(
        "T14            : Repository Intelligence Context"
    )
    print(
        "T15            : AI Operator Autonomy"
    )
    print(
        "T18            : Safe Execution Authorization"
    )
    print(
        "T20            : Repair / Patch Verification"
    )
    print(
        "T21            : Git Repository Coordination"
    )
    print(
        "T22            : Commit Execution Checkpoint"
    )
    print(
        "T23            : Evidence Resolution"
    )
    print(
        "T24            : Continuity Recovery"
    )

    print("-" * 72)

    print(
        "RULE           : "
        "AUDIT BEFORE MODIFY"
    )
    print(
        "RULE           : "
        "ADD / REPLACE / NO CHANGE"
    )
    print(
        "RULE           : "
        "CANONICAL GITHUB STATE FIRST"
    )
    print(
        "RULE           : "
        "NO DUPLICATE FILES"
    )
    print(
        "RULE           : "
        "NO DUPLICATE ROUTES"
    )
    print(
        "RULE           : "
        "NO DUPLICATE ENGINES"
    )
    print(
        "RULE           : "
        "NO BLIND PATCHING"
    )
    print(
        "RULE           : "
        "POWERSHELL WRITE = FORBIDDEN"
    )
    print(
        "RULE           : "
        "FAIL CLOSED ON UNCERTAINTY"
    )

    print("-" * 72)

    print(
        "STATUS         :",
        "READY"
        if validate_entrypoint()
        else "VERIFY",
    )

    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_startup_context()
