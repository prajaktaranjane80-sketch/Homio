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
        "Existing REOS execution authorization / executor boundary"
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
        "new_session_workflow": list(NEW_SESSION_WORKFLOW),
        "change_decision_rules": list(CHANGE_DECISION_RULES),
        "failure_rules": list(FAILURE_RULES),
        "non_developer_owner_contract": list(
            NON_DEVELOPER_OWNER_CONTRACT
        ),
    }


def validate_entrypoint() -> bool:
    """
    Validate only the structural entrypoint assumptions.

    This is intentionally read-only.
    It does not assert that every referenced implementation exists
    locally; local repository verification remains authoritative.
    """

    if not CONTROL_CENTER_PATH.is_dir():
        return False

    if not AUTONOMY_ENGINE_PATH.is_dir():
        return False

    if not ACRL_PATH.is_dir():
        return False

    return True


# ---------------------------------------------------------------------------
# HUMAN-READABLE STARTUP
# ---------------------------------------------------------------------------

def print_startup_context() -> None:
    """Print a compact new-AI startup contract."""

    print("=" * 72)
    print("HOMIO / REOS — AI AGENT ENTRYPOINT")
    print("=" * 72)
    print(f"PROJECT        : {PROJECT_NAME}")
    print(f"AUTHORITY      : {CONTROL_CENTER_NAME}")
    print("CONTINUITY     : ACRL")
    print("CHAT HISTORY   : NON-AUTHORITATIVE")
    print("STATE          : REOS_CONTROL_CENTER/data/state.json")
    print("CODE           : Git repository")
    print("VERIFICATION   : Local PowerShell")
    print("T07            : New Chat Bootstrap")
    print("T14            : Repository Intelligence Context")
    print("T15            : AI Operator Autonomy")
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
