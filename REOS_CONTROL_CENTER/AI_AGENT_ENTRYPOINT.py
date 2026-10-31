"""
HOMIO / REOS — AI AGENT ENTRYPOINT
==================================

First-read operating contract and repository reference index for every new
GPT/AI session working on HOMIO / REOS.

MANDATORY STARTUP:
1. Read this file.
2. Refresh the live GitHub branch and repository HEAD.
3. Read REOS_CONTROL_CENTER/data/state.json and verify its integrity.
4. Declare BACKEND, FRONTEND or SHARED_INTEGRATION.
5. Read the selected workstream's existing master reference.
6. Inspect exact files, ownership, tests and evidence before editing.

This file is an agent policy and navigation index. It is NOT:
- a second Control Center or state store;
- an execution planner or task-authorization engine;
- a replacement for ACRL T07/T14/T18/T20/T21/T22/T23/T24;
- a replacement for backend, frontend or AI implementation plans;
- a Git synchronization runner;
- a source of live state or current CI results.

CANONICAL AUTHORITIES:
- Execution state: REOS_CONTROL_CENTER/data/state.json
- Code and history: GitHub branch reos-development
- Task transitions: existing REOS Control Center
- T07: new-chat bootstrap
- T14: repository intelligence and fast-resume assessment
- T15: AI operator autonomy boundary
- T18: execution authorization
- T20: patch and repair verification
- T21: Git repository coordination
- T22: commit and checkpoint coordination
- T23: evidence resolution
- T24: continuity and recovery

Chat history, memory, handoff packets, old continuity snapshots and plans
provide context only. They never override live state.json or live GitHub.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ===========================================================================
# 1. REPOSITORY IDENTITY
# ===========================================================================

PROJECT_NAME = "HOMIO / REOS"
PROJECT_DESCRIPTION = (
    "Global AI Real Estate OS + International Brokerage + SaaS."
)

REPOSITORY_FULL_NAME = "prajaktaranjane80-sketch/Homio"
EXPECTED_BRANCH = "reos-development"
EXPECTED_ORIGIN = (
    "https://github.com/prajaktaranjane80-sketch/Homio.git"
)

CONTROL_CENTER_NAME = "REOS_CONTROL_CENTER"
CONTROL_CENTER_PATH = Path(__file__).resolve().parent

CANONICAL_LOCAL_WORKSPACE = Path(r"D:\HOMIO")
CANONICAL_CONTROL_CENTER = (
    CANONICAL_LOCAL_WORKSPACE / CONTROL_CENTER_NAME
)

STATE_RELATIVE_PATH = "REOS_CONTROL_CENTER/data/state.json"
ENTRYPOINT_RELATIVE_PATH = "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"

CANONICAL_CODE_SOURCE = (
    "GitHub repository branch reos-development"
)

# Default owner working method:
# The assistant supplies complete file content and exact repository path.
# The owner saves through the GitHub web editor.
# The assistant verifies the resulting branch, commit and file readback.
#
# Direct agent-side GitHub writes are disabled by default. A one-off exception
# requires explicit owner authorization in the current turn and all applicable
# ACRL authorization and repository-coordination checks.

IMPLEMENTATION_WRITE_INTERFACE = (
    "Owner-controlled GitHub web editor saves with complete replacement "
    "content and independent post-save readback verification."
)

POWERSHELL_WRITE_ALLOWED = False
POWERSHELL_IS_VERIFICATION_ONLY = True
POWERSHELL_REMOTE_GITHUB_API_WRITE_ALLOWED = False
POWERSHELL_LOCAL_WORKTREE_WRITE_ALLOWED = False
POWERSHELL_LOCAL_GIT_MUTATION_ALLOWED = False
POWERSHELL_WRITE_MODE = "OWNER_CONTROLLED_GITHUB_WEB_UI_ONLY"

PS_OUTPUT_IS_EVIDENCE_ONLY = True

GENERATED_ARTIFACT_PATTERNS: tuple[str, ...] = (
    "__pycache__/",
    "*.pyc",
    "*.pyo",
)


# ===========================================================================
# 2. ACRL PATH OWNERSHIP
# ===========================================================================

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

STATE_PATH = CONTROL_CENTER_PATH / "data" / "state.json"


# ===========================================================================
# 3. OPERATING CONTRACT
# ===========================================================================

@dataclass(frozen=True)
class REOSAgentOperatingContract:
    """
    Descriptive repository contract.

    It does not authorize tasks, mutate state or replace the Control Center.
    """

    project: str = PROJECT_NAME

    project_description: str = PROJECT_DESCRIPTION

    authoritative_state: str = STATE_RELATIVE_PATH

    authoritative_code_reference: str = (
        "GitHub repository branch reos-development"
    )

    implementation_write_interface: str = (
        IMPLEMENTATION_WRITE_INTERFACE
    )

    current_verification: str = (
        "Live GitHub readback, exact file verification, focused tests and "
        "GitHub Actions evidence bound to the exact tested commit SHA."
    )

    continuity_system: str = "ACRL"

    chat_history_authority: str = "NON_AUTHORITATIVE"

    control_authority: str = "REOS_CONTROL_CENTER"

    execution_authority: str = (
        "REOS Control Center plus applicable ACRL authorization, "
        "repair-verification, Git coordination, evidence and checkpoint "
        "boundaries."
    )

    ai_role: str = (
        "Architecture-aware engineering operator and repository auditor"
    )


# ===========================================================================
# 4. DOCUMENT REGISTRY — SINGLE STARTING INDEX
# ===========================================================================

# These are pointers to existing owner documents.
# Do not copy their entire content into this file.
# Always fetch their current content and blob SHA from live GitHub.

DOCUMENT_REGISTRY: dict[str, dict[str, str]] = {

    "agent_entrypoint": {
        "path": (
            "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"
        ),
        "role": (
            "First-read operating policy, source registry, workstream "
            "routing and cross-chat synchronization."
        ),
        "authority": "AGENT_POLICY_NOT_EXECUTION_AUTHORITY",
    },

    "execution_state": {
        "path": (
            "REOS_CONTROL_CENTER/data/state.json"
        ),
        "role": (
            "Current gate, task, subtask, dependencies, acceptance criteria, "
            "recorded evidence and task transitions."
        ),
        "authority": "SOLE_CANONICAL_EXECUTION_STATE",
    },

    "control_center": {
        "path": (
            "REOS_CONTROL_CENTER/reos_control_center.py"
        ),
        "role": (
            "Existing state validation, task transitions, handoff and "
            "checkpoint coordination."
        ),
        "authority": "CANONICAL_STATE_MUTATION_INTERFACE",
    },

    "handoff_packet": {
        "path": (
            "REOS_CONTROL_CENTER/packets/NEW_CHAT_PACKET.txt"
        ),
        "role": (
            "Generated convenience snapshot. Compare its task fields with "
            "live state.json before use."
        ),
        "authority": "NON_AUTHORITATIVE_DERIVED_SNAPSHOT",
    },

    "acrl_t07": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T07_New_Chat_Bootstrap/new_chat_bootstrap.py"
        ),
        "role": (
            "New-chat bootstrap and restart-payload validation."
        ),
        "authority": "CONTINUITY_NOT_EXECUTION_AUTHORITY",
    },

    "acrl_t14": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T14_Repository_Intelligence_Context"
        ),
        "role": (
            "Repository context, audited-path knowledge and fast-resume "
            "assessment. Cached data must be refreshed and validated."
        ),
        "authority": "DERIVED_CONTEXT_ONLY",
    },

    "acrl_t15": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T15_AI_Operator_Autonomy"
        ),
        "role": "AI operator autonomy boundaries.",
        "authority": "EXECUTION_BOUNDARY",
    },

    "acrl_t18": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T18_Safe_Execution_Authorization_Guard"
        ),
        "role": "Execution authorization.",
        "authority": "AUTHORIZATION_BOUNDARY",
    },

    "acrl_t20": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T20_Autonomous_Repair_Patch_Verification"
        ),
        "role": "Patch and repair verification.",
        "authority": "PATCH_VERIFICATION_BOUNDARY",
    },

    "acrl_t21": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T21_Git_Repository_Read_Write_Coordination"
        ),
        "role": "GitHub repository coordination and conflict safety.",
        "authority": "GIT_COORDINATION_BOUNDARY",
    },

    "acrl_t22": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T22_Commit_Execution_Checkpoint_Coordination"
        ),
        "role": "Commit and checkpoint coordination.",
        "authority": "CHECKPOINT_BOUNDARY",
    },

    "acrl_t23": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T23_Reference_Evidence_Resolution_Engine"
        ),
        "role": "Evidence resolution.",
        "authority": "EVIDENCE_BOUNDARY",
    },

    "acrl_t24": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T24_Cross_Chat_Continuity_Recovery_Engine"
        ),
        "role": "Cross-chat continuity and recovery.",
        "authority": "CONTINUITY_RECOVERY_BOUNDARY",
    },

    "backend_master": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/backend/plans/"
            "HOMIO_Backend_Structure"
        ),
        "role": (
            "Backend-only architecture, backend gap closure, APIs, "
            "database, business logic, server-side security, AI, "
            "automation, backend integration contracts and production "
            "acceptance."
        ),
        "authority": "BACKEND_REFERENCE_NOT_TASK_AUTHORITY",
    },

    "frontend_master": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/frontend/plans/"
            "HOMIO_FRONTEND_MASTER_EXECUTION_PLAN.md"
        ),
        "role": (
            "Frontend pages, user experience, UI/UX, design system, "
            "components, content, CSS, responsive behaviour and "
            "frontend engineering."
        ),
        "authority": "FRONTEND_REFERENCE_NOT_TASK_AUTHORITY",
    },

    "frontend_legacy_coordination": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/frontend/plans/"
            "HOMIO_FRONTEND_EXECUTION_PLAN.json"
        ),
        "role": (
            "Earlier F01-F05 and APP-001 coordination snapshot. "
            "Revalidate it against current source files and state."
        ),
        "authority": "SUPPORTING_SNAPSHOT_NOT_CURRENT_STATE",
    },

    "h360_gap_reference": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/"
            "HOMIO_360_DEGREE_GAP_CLOSURE_EXECUTION_STRUCTURE.md"
        ),
        "role": (
            "Existing 360-degree gap-closure reference. Do not create "
            "or run a competing successor master without canonical "
            "adoption."
        ),
        "authority": "SUPPORTING_GAP_REFERENCE",
    },

    "workflow_sync_reference": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/"
            "HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md"
        ),
        "role": (
            "Historical workflow and ACRL execution-order reference. "
            "Use only where consistent with current state and source."
        ),
        "authority": "SUPPORTING_PLAN_NOT_TASK_AUTHORITY",
    },

    "ai001_blueprint": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/"
            "AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md"
        ),
        "role": (
            "AI-001 platform architecture, agents, context, controls "
            "and implementation reference."
        ),
        "authority": "AI_REFERENCE_NOT_TASK_AUTHORITY",
    },

    "core_closure_plan": {
        "path": (
            "REOS_CONTROL_CENTER/architecture/backend/plans/"
            "CORE-001 to CORE-008 Closure, Hardening & Architecture "
            "Integrity Active Plan"
        ),
        "role": (
            "Existing CORE-001 through CORE-008 closure and "
            "architecture-hardening reference."
        ),
        "authority": "CORE_REFERENCE_NOT_TASK_AUTHORITY",
    },

    "frontend_chat_packet": {
        "path": (
            "REOS_CONTROL_CENTER/new chat work reference"
        ),
        "role": (
            "APP-001/frontend continuation prompt only. It is not a "
            "universal project, backend or execution authority."
        ),
        "authority": "FRONTEND_CHAT_CONTEXT_ONLY",
    },

    "continuity_state": {
        "path": (
            "REOS_CONTROL_CENTER/PROJECT_CONTINUITY/continuity_state.json"
        ),
        "role": (
            "Continuity principles and historical context only. Its "
            "current_position and repository snapshot may be stale."
        ),
        "authority": "CONTINUITY_CONTEXT_ONLY",
    },

    "legacy_state_snapshot": {
        "path": (
            "REOS_CONTROL_CENTER/reos_state.json"
        ),
        "role": (
            "Legacy state snapshot. Never substitute it for data/state.json."
        ),
        "authority": "NON_AUTHORITATIVE_LEGACY",
    },

    "backend_ci": {
        "path": (
            ".github/workflows/backend-ci.yml"
        ),
        "role": (
            "Backend, EntryPoint contract and ACRL CI wiring."
        ),
        "authority": "CI_CONFIGURATION",
    },

    "frontend_ci": {
        "path": (
            ".github/workflows/frontend-ci.yml"
        ),
        "role": "Frontend CI wiring.",
        "authority": "CI_CONFIGURATION",
    },

    "entrypoint_contract_test": {
        "path": (
            "REOS_CONTROL_CENTER/tets/"
            "test_ai_agent_entrypoint_contract.py"
        ),
        "role": (
            "Automated contract regression for this EntryPoint."
        ),
        "authority": "TEST_EVIDENCE",
    },
}


# ===========================================================================
# 5. WORKSTREAM ROUTING AND OWNERSHIP
# ===========================================================================

WORKSTREAM_ROUTING: dict[str, dict[str, Any]] = {

    "BACKEND": {
        "master_reference": (
            DOCUMENT_REGISTRY["backend_master"]["path"]
        ),

        "owns": (
            "Backend services and runtime.",
            "REST APIs and versioned request/response/OpenAPI contracts.",
            "Authentication, authorization, sessions and tenant enforcement.",
            "Database, migrations, persistence and data integrity.",
            "CORE business rules, inventory, search and leads.",
            "AI gateway, retrieval, agents and tool execution.",
            "Events, queues, workers and durable workflows.",
            "Server-side security, privacy, integrations and rate limits.",
            "Backend unit, API, contract, integration and resilience testing.",
            "Deployment, monitoring, backup, restore, rollback and operations.",
        ),

        "excludes": (
            "Frontend page layouts and visual UI.",
            "CSS and visual design tokens.",
            "Animations and visual effects.",
            "Responsive presentation and frontend visual polish.",
            "Frontend component implementation.",
        ),

        "integration_rule": (
            "Backend is the sole owner of API request/response semantics, "
            "OpenAPI and versioned server contracts. Frontend consumes "
            "those contracts. Backend does not own frontend visual delivery."
        ),
    },

    "FRONTEND": {
        "master_reference": (
            DOCUMENT_REGISTRY["frontend_master"]["path"]
        ),

        "owns": (
            "Frontend pages, routes, layouts and user journeys.",
            "Components and design system.",
            "Theme, CSS, content and visual interactions.",
            "Responsive behaviour and accessibility.",
            "Frontend API clients and adapters consuming backend contracts.",
            "Frontend CI and browser/UI verification.",
        ),

        "excludes": (
            "Duplicate backend domain or business rules.",
            "Direct database access or persistence ownership.",
            "Independent authorization that bypasses backend enforcement.",
            "Invented API routes or undocumented request/response semantics.",
        ),

        "integration_rule": (
            "Frontend consumes the backend-owned versioned contract. "
            "Until a contract exists, isolate mock data behind an adapter "
            "and label that dependency provisional. Do not invent production "
            "API behaviour."
        ),
    },

    "SHARED_INTEGRATION": {
        "master_reference": (
            "Backend-owned API contract + frontend consumer; "
            "coordinate using the existing H360 reference."
        ),

        "owns": (
            "Versioned API compatibility and consumer/provider checks.",
            "Authentication and tenant-context handoff compatibility.",
            "Cross-system business journey verification after both sides exist.",
            "Browser E2E and complete integration evidence.",
        ),

        "excludes": (
            "Creating a second API source of truth.",
            "Moving backend business logic into the frontend.",
            "Changing either workstream source without an authorized task.",
            "Creating a duplicate integration framework.",
        ),

        "integration_rule": (
            "Shared verification coordinates both workstreams. It is not "
            "a third implementation owner and does not duplicate either "
            "workstream's source files."
        ),
    },
}


# ===========================================================================
# 6. CROSS-CHAT SYNCHRONIZATION RULES
# ===========================================================================

CROSS_CHAT_SYNC_RULES: tuple[str, ...] = (

    "Every chat must declare BACKEND, FRONTEND or SHARED_INTEGRATION "
    "before implementation.",

    "Separate chats are not separate repositories. All work shares the "
    "same reos-development branch, state.json and commit history.",

    "Separate plans do not grant separate task authorization. Implementation "
    "must match live state or an explicitly approved parallel-work "
    "authorization.",

    "Do not infer that a backend task is authorized merely because "
    "HOMIO_Backend_Structure exists.",

    "Do not infer that a frontend task is authorized merely because "
    "a frontend plan or continuation prompt exists.",

    "Backend chat must not modify Frontend UI/UX source.",

    "Frontend chat must not move business rules, persistence or backend "
    "authorization into the frontend.",

    "Backend is the single owner of API request/response and OpenAPI "
    "semantics. Frontend is a consumer, not a second contract owner.",

    "Do not invent API routes, fields, enums, errors or workflow states. "
    "Audit the exact contract owner and repository paths first.",

    "Parallel changes are allowed only when their tasks are authorized "
    "and their file ownership is disjoint.",

    "Never allow two chats to edit or replace the same path at the same time.",

    "Before every save, re-fetch live branch HEAD and exact target blob SHA.",

    "If branch HEAD or target blob changed since review, stop and refresh "
    "before preparing replacement content.",

    "After every owner save, re-fetch branch HEAD, commit parent and exact "
    "changed-file content.",

    "Each chat records changed paths and resulting commit SHA in its handoff.",

    "The next chat must refresh live GitHub before relying on any handoff.",

    "Never mark another chat's work complete from a summary. Verify exact "
    "files, tests and Actions evidence.",

    "A shared integration decision is recorded once and referenced by "
    "both tracks. Do not maintain competing copies.",

)


# ===========================================================================
# 7. EVIDENCE AND CI VERIFICATION RULES
# ===========================================================================

EVIDENCE_VERIFICATION_RULES: tuple[str, ...] = (

    "A commit is not tested merely because a prior commit passed.",

    "A GitHub Actions run proves only the exact head_sha recorded by that run.",

    "Before reporting CI PASS, verify repository, branch, workflow name, "
    "run ID, conclusion, tested SHA, required jobs/steps and relevant artifacts.",

    "The tested SHA must equal the commit being claimed as verified. "
    "Otherwise label the evidence historical or parent-commit evidence.",

    "Skipped, cancelled, neutral, missing or path-filter-omitted checks "
    "are not PASS.",

    "A passing development workflow does not prove production deployment, "
    "operational SLOs or release approval.",

    "Use the existing production readiness gate and fresh operational "
    "evidence. Never weaken its fail-closed logic.",

    "Backend production completion requires all 18 blockers in "
    "HOMIO_Backend_Structure to be closed with environment-specific "
    "evidence and accountable approval.",

    "Do not aggregate overlapping suites as unique tests without deduplicating them.",

    "After every GitHub UI save, verify exact file readback and inspect "
    "Actions for the resulting commit SHA.",

)


# ===========================================================================
# 8. CANONICAL AUTHORITY AND SOURCE-OF-TRUTH MAP
# ===========================================================================

SOURCE_OF_TRUTH: dict[str, str] = {

    "project_state": (
        DOCUMENT_REGISTRY["execution_state"]["path"]
    ),

    "code_and_history": (
        "GitHub repository branch reos-development"
    ),

    "agent_policy": (
        DOCUMENT_REGISTRY["agent_entrypoint"]["path"]
    ),

    "control_center": (
        DOCUMENT_REGISTRY["control_center"]["path"]
    ),

    "backend_workstream": (
        DOCUMENT_REGISTRY["backend_master"]["path"]
    ),

    "frontend_workstream": (
        DOCUMENT_REGISTRY["frontend_master"]["path"]
    ),

    "cross_chat_coordination": (
        "AI_AGENT_ENTRYPOINT.py / CROSS_CHAT_SYNC_RULES"
    ),

    "handoff_packet": (
        DOCUMENT_REGISTRY["handoff_packet"]["path"]
    ),

    "backend_ci": (
        DOCUMENT_REGISTRY["backend_ci"]["path"]
    ),

    "frontend_ci": (
        DOCUMENT_REGISTRY["frontend_ci"]["path"]
    ),

    "continuity": (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl"
    ),

    "chat_history": "NON_AUTHORITATIVE",

    "legacy_state_snapshot": (
        "NON_AUTHORITATIVE; never replace data/state.json"
    ),

    "ps_output": "Evidence only",

    "current_execution_evidence": (
        "Verified live GitHub branch, exact commit, exact target content, "
        "focused tests and relevant Actions evidence."
    ),
}


# ===========================================================================
# 9. NEW-SESSION READ ORDER
# ===========================================================================

NEW_SESSION_READ_ORDER: tuple[str, ...] = (

    "1. Read AI_AGENT_ENTRYPOINT.py for agent policy, document registry "
    "and workstream routing.",

    "2. Fetch the live GitHub branch reos-development and record its "
    "current HEAD SHA.",

    "3. Fetch REOS_CONTROL_CENTER/data/state.json, record its blob SHA "
    "and read the active gate, task, subtask, dependencies and criteria.",

    "4. Validate state integrity through the existing Control Center boundary. "
    "Do not manually patch state.json.",

    "5. Reuse ACRL T07 bootstrap and T14 repository context. Refresh their "
    "inputs and reject stale evidence.",

    "6. Read NEW_CHAT_PACKET.txt only as a derived snapshot. Compare its "
    "task fields with live state.json.",

    "7. Read approved architecture and the selected workstream master plan.",

    "8. Consult the counterpart workstream plan only for API, auth, tenant "
    "and integration boundaries.",

    "9. Inspect exact target source files, callers, contracts, tests, "
    "CI path filters and recent commits.",

    "10. Apply applicable T15/T18/T20/T21/T22/T23/T24 boundaries.",

    "11. Implement only the authorized scope and disjoint file set.",

    "12. Verify the exact saved commit, target readback, focused tests, "
    "Actions result and residual blockers.",

)


# ===========================================================================
# 10. AGENT OPERATING RULES
# ===========================================================================

AI_OPERATING_RULES: tuple[str, ...] = (

    "Treat REOS_CONTROL_CENTER as the project control authority.",

    "Treat data/state.json as canonical machine-readable project state.",

    "Treat GitHub branch reos-development as the canonical code source.",

    "Treat chat history as communication only, never as project truth.",

    "Refresh live GitHub branch HEAD and state.json at the start of every "
    "new chat and before every implementation batch.",

    "Never treat chat memory, old handoff packets, continuity_state.json "
    "current_position, reos_state.json or cached manifests as current "
    "execution authority.",

    "Do not infer or activate a parallel backend/frontend task from a plan. "
    "Only canonical Control Center state and approved authorization can "
    "establish task authority.",

    "Keep backend and frontend ownership separate.",

    "Backend owns API contracts; frontend consumes approved versioned contracts.",

    "Never modify another workstream's source files as a side effect of "
    "the current task.",

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

    "Local preflight is optional diagnostics only. It is not live GitHub proof.",

    "Do not claim tests or CI passed without evidence for the exact tested SHA.",

    "Run focused verification and relevant regressions before declaring success.",

    "When evidence conflicts or is insufficient, stop and report the blocker.",

)


# ===========================================================================
# 11. DEVELOPMENT AND OWNER WORKFLOW
# ===========================================================================

DEVELOPMENT_WORKFLOW_RULES: tuple[str, ...] = (

    "This entrypoint defines agent-facing workflow policy; it does not "
    "execute writes or authorize tasks.",

    "GitHub branch reos-development is the canonical code source.",

    "The owner-controlled GitHub web editor is the default save interface.",

    "Direct agent-side GitHub API writes are disabled by default.",

    "Local worktree source writes and local Git mutations are forbidden "
    "under the current owner working agreement.",

    "Do not require the owner to create or repair a local worktree, install "
    "tools, download artifacts or run PowerShell unless the owner explicitly "
    "changes the working agreement.",

    "Supporting work plans cannot override the Control Center or state.json.",

    "Inspect canonical GitHub state before every requested change.",

    "Classify files as ADD, REPLACE, VERIFY, NO CHANGE or BLOCKED.",

    "ADD requires the exact path to be absent on the canonical branch and "
    "no existing owner for the responsibility.",

    "REPLACE requires the exact path to exist and own the requested responsibility.",

    "Never recreate a file merely because a local workspace is stale.",

    "A full replacement request requires complete replacement content, "
    "not an inferred patch.",

    "Provide exact repository paths and complete file content.",

    "After the owner saves, independently verify branch, commit parent "
    "and exact changed-file content.",

    "T18 authorization, T20 patch verification and T21 Git coordination "
    "remain separate responsibilities.",

    "Never treat T20 VERIFIED as proof that a Git commit occurred.",

    "The existing backend-ci.yml workflow must run the EntryPoint "
    "contract regression.",

    "The contract test must not be silently skipped if its file is missing.",

    "Do not create, download, invoke or rely on a standalone runner as "
    "a competing workflow authority.",

)


# ===========================================================================
# 12. REMOTE GIT SYNCHRONIZATION CONTRACT
# ===========================================================================

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

    "Before the owner edits a GitHub file, capture live branch HEAD and "
    "the exact target blob SHA.",

    "The owner saves only the intended target file through the GitHub web editor.",

    "After the save, independently read back branch HEAD, commit parent "
    "and exact target content.",

    "If branch HEAD or target blob changed since review, stop and refresh "
    "before preparing replacement content.",

    "Never force-update, force-push, reset, rebase or overwrite a newer "
    "branch state.",

    "A failed, ambiguous or conflicting save must fail closed.",

    "Do not use a local cached upstream ref as proof of live remote HEAD.",

    "Remote readback and exact target-content verification are separate evidence.",

    "Report PASS only after exact branch, new commit, parent and file "
    "content are verified.",

)


# ===========================================================================
# 13. REPOSITORY PREFLIGHT CONTRACT
# ===========================================================================

REPOSITORY_PREFLIGHT_RULES: tuple[str, ...] = (

    "The expected repository is prajaktaranjane80-sketch/Homio.",

    "The expected branch is reos-development.",

    "The expected origin resolves to the canonical GitHub repository.",

    "The local D:\\HOMIO preflight is optional diagnostics only.",

    "Do not ask the owner to repair a local checkout as a prerequisite "
    "for the GitHub-web workflow.",

    "A local workspace may be stale and must not override canonical "
    "GitHub evidence.",

    "Local worktree content is not a source for remote writes.",

    "Inspect staged, modified, deleted and untracked files if a local "
    "preflight is explicitly requested.",

    "Inspect configured upstream without fetching or mutating the repository.",

    "Report ahead/behind counts against the local upstream-tracking ref.",

    "Missing status evidence or malformed count evidence fails local-ready status.",

    "Any dirty worktree fails local-ready status.",

    "Missing upstream fails local-ready status.",

    "Any nonzero ahead or behind count fails local-ready status.",

    "A clean local preflight does not establish that live remote HEAD is current.",

    "Obtain live GitHub readback independently; local preflight cannot "
    "replace remote verification.",

    "PS Output, old continuity snapshots and frontend diagnostics are evidence only.",

    "Never mutate state.json directly.",

)


# ===========================================================================
# 14. FILE CHANGE CLASSIFICATION
# ===========================================================================

FILE_CHANGE_CLASSIFICATION: tuple[str, ...] = (

    "ADD: exact path is absent on canonical branch and no existing owner "
    "has the responsibility.",

    "REPLACE: exact path exists and owns the requested responsibility.",

    "NO CHANGE: repository evidence does not justify modification.",

    "VERIFY: inspect evidence without changing the target.",

    "BLOCKED: required authority, dependency or evidence is missing.",

    "Existing routes, components and modules take precedence over duplicates.",

    "A stale local checkout is not proof that a GitHub file is missing.",

    "A completed layer is reopened only for a verified dependency, "
    "integration need or regression.",

)


# ===========================================================================
# 15. EXECUTION WORKFLOW
# ===========================================================================

EXECUTION_WORKFLOW: tuple[str, ...] = (

    "1. Declare the workstream: BACKEND, FRONTEND or SHARED_INTEGRATION.",

    "2. Read canonical state from REOS_CONTROL_CENTER/data/state.json.",

    "3. Verify live GitHub branch reos-development and current repository HEAD.",

    "4. Inspect exact requested paths and existing responsibility owners.",

    "5. Classify every requested file action.",

    "6. Resolve applicable architecture, task and dependency constraints.",

    "7. Confirm that the current task is authorized by the Control Center.",

    "8. Apply required ACRL authorization and patch-verification boundaries.",

    "9. Provide complete implementation content for owner-approved changes.",

    "10. Let the owner save through GitHub web editor under the default agreement.",

    "11. Verify branch, commit parent and exact changed-file content.",

    "12. Run focused tests and relevant regression checks.",

    "13. Inspect CI for the exact commit SHA.",

    "14. Resolve missing or conflicting evidence through applicable ACRL boundaries.",

    "15. Change canonical state only through the existing Control Center workflow.",

    "16. Never report PASS without independent verification evidence.",

)


# ===========================================================================
# 16. REQUIRED NEW-SESSION WORKFLOW
# ===========================================================================

NEW_SESSION_WORKFLOW: tuple[str, ...] = (

    "1. Identify HOMIO / REOS and declare BACKEND, FRONTEND or SHARED_INTEGRATION.",

    "2. Read this EntryPoint and use its document registry and workstream routing.",

    "3. Independently fetch live reos-development HEAD, branch metadata and repository tree.",

    "4. Fetch data/state.json, record its blob SHA and read current gate, task, "
    "subtask, dependencies and acceptance criteria.",

    "5. Validate state integrity through the existing Control Center boundary.",

    "6. Treat state.json as the only execution-state authority. A plan does "
    "not authorize a new or parallel task.",

    "7. Reuse ACRL T07 bootstrap and T14 repository context; refresh inputs "
    "and reject stale evidence.",

    "8. Read NEW_CHAT_PACKET.txt only as a derived snapshot and compare it "
    "with live state.json.",

    "9. Read approved architecture and the selected workstream master plan.",

    "10. Consult the counterpart workstream plan only for API, auth, tenant "
    "and integration boundaries.",

    "11. Inspect exact target files, source owners, callers, contracts, "
    "tests, workflow path filters and relevant commits.",

    "12. Declare allowed paths, excluded paths, shared dependencies and "
    "whether canonical state authorizes implementation.",

    "13. Apply T15/T18/T20/T21/T22/T23/T24 boundaries as applicable.",

    "14. Provide complete replacement content and exact GitHub paths.",

    "15. Refresh live HEAD and target blob after every save.",

    "16. Run focused tests and relevant regression CI on the exact saved SHA.",

    "17. Record test scope, run ID, tested SHA, artifacts, evidence and residual risks.",

    "18. Advance state only through the existing Control Center transition.",

    "19. Report verified position and the first valid next step without "
    "inventing, skipping or reopening tasks.",

)


# ===========================================================================
# 17. OWNER WORKING CONTRACT
# ===========================================================================

NON_DEVELOPER_OWNER_CONTRACT: tuple[str, ...] = (

    "The owner is not required to write or debug implementation code manually.",

    "Provide exact repository paths and clearly label each file action.",

    "Inspect canonical GitHub before instructing the owner to replace a file.",

    "Provide complete replacement content when full replacement is required.",

    "Do not require the owner to construct a patch from inferred fragments.",

    "Avoid unnecessary manual steps and unverified standalone sync scripts.",

    "Do not hide uncertainty behind a generic recommendation.",

    "Request targeted evidence when repository evidence is insufficient.",

    "Do not provide local-worktree instructions unless explicitly requested.",

    "After owner saves, verify the exact live file rather than assuming success.",

)


# ===========================================================================
# 18. CHANGE DECISION RULES
# ===========================================================================

CHANGE_DECISION_RULES: tuple[str, ...] = (

    "FIRST: inspect the current canonical GitHub repository state.",

    "SECOND: inspect canonical state.json and task authorization.",

    "THIRD: inspect existing ownership of the responsibility.",

    "FOURTH: classify the requested action.",

    "FIFTH: determine whether the existing owner can be safely extended.",

    "SIXTH: verify completed-layer boundaries before implementation.",

    "SEVENTH: inspect impact on the other workstream and shared API contracts.",

    "NEVER: create duplicate modules, routes, components or sources of truth.",

    "NEVER: treat a stale local checkout as proof a file is missing.",

    "NEVER: reopen a completed layer without repository evidence.",

    "NEVER: treat this EntryPoint as authorization to bypass the Control Center.",

)


# ===========================================================================
# 19. FAILURE AND RECOVERY RULES
# ===========================================================================

FAILURE_RULES: tuple[str, ...] = (

    "If canonical repository state is unclear, reconstruct it before editing.",

    "If state.json cannot be fetched or validated, do not implement.",

    "If the exact target path has not been checked, do not classify it as ADD.",

    "If architecture authority is unclear, stop before architectural change.",

    "If local and remote evidence differs, treat canonical GitHub as code authority.",

    "If an old handoff conflicts with state.json, state.json wins.",

    "If continuity_state.json conflicts with state.json, state.json wins.",

    "If reos_state.json conflicts with data/state.json, data/state.json wins.",

    "If a T14 cache is uninitialized, stale or invalid, do not mark it sealed manually.",

    "If tests fail, diagnose the actual failure before changing implementation.",

    "If an approved implementation is green, do not redesign it without evidence.",

    "If a change introduces duplicate responsibility, reject it.",

    "If execution authority is required but unavailable, fail closed.",

    "If project state cannot be safely reconstructed, do not manufacture state.",

    "If remote writes or manual saves cannot be independently verified, "
    "do not report PASS.",

    "If two chats changed the same target path, stop and reconcile before "
    "preparing another replacement.",

)


# ===========================================================================
# 20. HISTORICAL AUDIT SNAPSHOT — NOT LIVE AUTHORITY
# ===========================================================================

# This records what was inspected before this EntryPoint replacement.
# Every new session MUST refresh the values independently.
# Never use this snapshot as current state or current CI proof.

LAST_AUDIT_SNAPSHOT: dict[str, str] = {

    "captured_at": "2026-10-31",

    "branch": "reos-development",

    "branch_head_before_entrypoint_update": (
        "ef823a14b96182730c9a50bc970063ca01f699ff"
    ),

    "entrypoint_blob_sha_before_update": (
        "5531e8a30b067fab4723316034e8d8fbcef5565e"
    ),

    "state_json_blob_sha": (
        "6242f63371a725ea99447c218bbbeb46a0c5eddd"
    ),

    "backend_structure_blob_sha": (
        "b4f45c14e19987deba48d73dcab702ee96ebb68e"
    ),

    "frontend_master_blob_sha": (
        "40be4077f1d61f620f815cef82ef01324ccd76a3"
    ),

    "h360_reference_blob_sha": (
        "dce6733f437337756ac2d2885848b01896afeb3b"
    ),

    "current_gate_at_review": "APP-001",

    "current_task_at_review": "APP-001-T01",

    "latest_backend_actions_run_at_review": "41070089623",

    "latest_backend_actions_tested_sha_at_review": (
        "00629507a57de742c4419439945ca658a4bb1d43"
    ),

    "latest_backend_actions_conclusion_at_review": "success",

    "actions_status_for_head_before_entrypoint_update": (
        "No combined status checks recorded for ef823a14."
    ),

    "backend_production_readiness_at_review": (
        "NOT_READY; 18 blockers remain in backend master specification."
    ),

    "t14_manifest_at_review": (
        "UNINITIALIZED source template; do not manually seal."
    ),

    "continuity_state_warning": (
        "continuity_state.json current_position points to an old main-branch "
        "and CORE-004 snapshot; use its continuity rules only."
    ),

    "latest_actions_warning": (
        "The passing backend Actions run above tested 00629507, not "
        "ef823a14. It is historical evidence for that exact older SHA."
    ),

}


# ===========================================================================
# 21. SOURCE-OF-TRUTH AND DOCUMENT DISCOVERY HELPERS
# ===========================================================================

def repository_paths() -> dict[str, str]:
    """
    Return important repository paths.

    This helper performs no network access, state mutation or Git operation.
    """

    return {

        "control_center": str(CONTROL_CENTER_PATH),

        "state": str(STATE_PATH),

        "autonomy_engine": str(AUTONOMY_ENGINE_PATH),

        "acrl": str(ACRL_PATH),

        "agent_entrypoint": str(
            CONTROL_CENTER_PATH / "AI_AGENT_ENTRYPOINT.py"
        ),

        "t07": str(ACRL_ENTRYPOINT),

        "t14": str(ACRL_REPOSITORY_CONTEXT),

        "t15": str(ACRL_OPERATOR_AUTONOMY),

        "t18": str(ACRL_EXECUTION_AUTHORIZATION),

        "t20": str(ACRL_REPAIR_VERIFICATION),

        "t21": str(ACRL_GIT_REPOSITORY_COORDINATION),

        "t22": str(ACRL_COMMIT_CHECKPOINT_COORDINATION),

        "t23": str(ACRL_EVIDENCE_RESOLUTION),

        "t24": str(ACRL_CONTINUITY_RECOVERY),

        "handoff_packet": str(
            CONTROL_CENTER_PATH / "packets" / "NEW_CHAT_PACKET.txt"
        ),

        "backend_master": DOCUMENT_REGISTRY["backend_master"]["path"],

        "frontend_master": DOCUMENT_REGISTRY["frontend_master"]["path"],

        "h360_reference": DOCUMENT_REGISTRY["h360_gap_reference"]["path"],

        "workflow_sync_reference": (
            DOCUMENT_REGISTRY["workflow_sync_reference"]["path"]
        ),

        "ai001_blueprint": DOCUMENT_REGISTRY["ai001_blueprint"]["path"],

        "core_closure_plan": DOCUMENT_REGISTRY["core_closure_plan"]["path"],

        "backend_ci": DOCUMENT_REGISTRY["backend_ci"]["path"],

        "frontend_ci": DOCUMENT_REGISTRY["frontend_ci"]["path"],

        "entrypoint_contract_test": (
            DOCUMENT_REGISTRY["entrypoint_contract_test"]["path"]
        ),

    }


def contract() -> REOSAgentOperatingContract:
    """Return the descriptive repository-level AI operating contract."""

    return REOSAgentOperatingContract()


def startup_instructions() -> dict[str, Any]:
    """
    Return machine-readable instructions for a new AI session.

    This function:
    - does not fetch remote GitHub data;
    - does not mutate state;
    - does not execute project commands;
    - does not authorize a task;
    - does not replace ACRL.

    Live repository and state refresh are mandatory instructions for the
    agent, not hidden network operations performed by this module.
    """

    operating_contract = contract()

    return {

        "entrypoint": ENTRYPOINT_RELATIVE_PATH,

        "project": operating_contract.project,

        "project_description": operating_contract.project_description,

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

        "document_registry": {
            key: dict(value)
            for key, value in DOCUMENT_REGISTRY.items()
        },

        "workstream_routing": {
            key: dict(value)
            for key, value in WORKSTREAM_ROUTING.items()
        },

        "cross_chat_sync_rules": list(CROSS_CHAT_SYNC_RULES),

        "evidence_verification_rules": list(
            EVIDENCE_VERIFICATION_RULES
        ),

        "new_session_read_order": list(
            NEW_SESSION_READ_ORDER
        ),

        "last_audit_snapshot": dict(LAST_AUDIT_SNAPSHOT),

        "paths": repository_paths(),

        "operating_rules": list(AI_OPERATING_RULES),

        "development_workflow_rules": list(
            DEVELOPMENT_WORKFLOW_RULES
        ),

        "file_change_classification": list(
            FILE_CHANGE_CLASSIFICATION
        ),

        "repository_preflight_rules": list(
            REPOSITORY_PREFLIGHT_RULES
        ),

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

        "failure_rules": list(FAILURE_RULES),

        "non_developer_owner_contract": list(
            NON_DEVELOPER_OWNER_CONTRACT
        ),

        "local_preflight_is_diagnostic_only": True,

        "live_github_refresh_required": True,

        "canonical_state_refresh_required": True,

        "workstream_declaration_required": True,

        "plan_documents_authorize_tasks": False,

    }


# ===========================================================================
# 22. READ-ONLY LOCAL GIT DIAGNOSTICS
# ===========================================================================

def _run_git(*args: str) -> tuple[int, str, str]:
    """
    Run one read-only Git command for optional local diagnostics.

    No fetch, checkout, clean, commit, pull, push, reset, merge or
    ref-update command is issued.
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
        origin = (
            "https://github.com/"
            + origin.split(":", 1)[1]
        )

    elif origin.startswith("ssh://git@github.com/"):
        origin = (
            "https://github.com/"
            + origin.split("ssh://git@github.com/", 1)[1]
        )

    if origin.startswith("https://"):
        parsed = urlsplit(origin)

        hostname = (
            parsed.hostname.lower()
            if parsed.hostname
            else ""
        )

        origin = "https://" + hostname + parsed.path

    if origin.endswith(".git"):
        origin = origin[:-4]

    return origin.rstrip("/").lower()


def git_preflight() -> dict[str, Any]:
    """
    Return optional local repository diagnostics.

    This function does not establish live GitHub state.

    Ahead/behind counts use the local cached upstream-tracking ref only.
    The caller must independently verify live GitHub HEAD.

    This diagnostic is not required for the owner's GitHub-web workflow.
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

        "diagnostic_only": True,

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

    normalized_expected_origin = _normalize_origin(
        EXPECTED_ORIGIN
    )

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

    # A local tracking ref is never live remote proof.
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
    Return True only when required local architecture paths exist and the
    optional local Git preflight is clean.

    This is not a live GitHub readiness check.
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


# ===========================================================================
# 23. HUMAN-READABLE STARTUP
# ===========================================================================

def print_startup_context() -> None:
    """Print agent policy and optional local diagnostic status."""

    print("=" * 72)

    print("HOMIO / REOS — AI AGENT ENTRYPOINT")

    print("=" * 72)

    print(f"PROJECT        : {PROJECT_NAME}")

    print(f"AUTHORITY      : {CONTROL_CENTER_NAME}")

    print("CONTINUITY     : ACRL")

    print("CHAT HISTORY   : NON-AUTHORITATIVE")

    print("STATE          : REOS_CONTROL_CENTER/data/state.json")

    print("CODE SOURCE    : GitHub / reos-development")

    print("WRITE METHOD   : Owner-controlled GitHub Web UI")

    print(f"BRANCH         : {EXPECTED_BRANCH}")

    print(f"REPOSITORY     : {REPOSITORY_FULL_NAME}")

    print("WORKSTREAMS    : BACKEND / FRONTEND / SHARED_INTEGRATION")

    print("API OWNERSHIP  : BACKEND OWNS / FRONTEND CONSUMES")

    print("-" * 72)

    preflight = git_preflight()

    print("LOCAL PREFLIGHT: DIAGNOSTIC ONLY")

    print(f"CWD CHECK      : {preflight['cwd_ok']}")

    print(f"ROOT CHECK     : {preflight['repository_root_ok']}")

    print(f"BRANCH CHECK   : {preflight['branch_ok']}")

    print(f"ORIGIN CHECK   : {preflight['origin_ok']}")

    print(f"WORKTREE CLEAN : {preflight['clean_worktree']}")

    print(f"UPSTREAM SET   : {preflight['upstream_configured']}")

    print(f"AHEAD BY       : {preflight['ahead_by']}")

    print(f"BEHIND BY      : {preflight['behind_by']}")

    print("LIVE REMOTE    : MUST BE VERIFIED INDEPENDENTLY")

    print("STATE          : MUST BE REFRESHED FROM LIVE GITHUB")

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

    print("RULE           : LIVE STATE BEFORE TASK SELECTION")

    print("RULE           : DECLARE WORKSTREAM")

    print("RULE           : BACKEND / FRONTEND OWNERSHIP SEPARATE")

    print("RULE           : API CONTRACTS BACKEND-OWNED")

    print("RULE           : NO DUPLICATE FILES OR ENGINES")

    print("RULE           : OWNER SAVES VIA GITHUB WEB UI")

    print("RULE           : REFRESH HEAD AND TARGET SHA BEFORE SAVE")

    print("RULE           : VERIFY EXACT COMMIT AND ACTIONS")

    print("RULE           : FAIL CLOSED ON UNCERTAINTY")

    print("-" * 72)

    print(
        "LOCAL STATUS   :",
        "READY"
        if preflight["ready"]
        else "NOT VERIFIED / OPTIONAL LOCAL PREFLIGHT",
    )

    print("=" * 72)


# ===========================================================================
# 24. CLI
# ===========================================================================

if __name__ == "__main__":
    print_startup_context()
