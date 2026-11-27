"""
HOMIO / REOS — AI AGENT ENTRYPOINT
==================================

First-read operating contract and repository reference index for every new
GPT/AI session working on HOMIO / REOS.

MANDATORY STARTUP:
0. Discover available engineering skills and invoke using-superpowers.
1. Read this file and use its existing document registry.
2. Refresh the live GitHub branch and repository HEAD.
3. Read REOS_CONTROL_CENTER/data/state.json and verify its integrity.
4. Declare BACKEND, FRONTEND or SHARED_INTEGRATION.
5. Read the selected workstream's existing master reference.
6. Retrieve and validate reusable T14 continuity evidence when available.
7. Use existing T16 repository discovery and T23 evidence resolution owners.
8. Inspect only invalidated or task-relevant source paths before editing.
9. Follow existing authorization, Git, checkpoint and human-decision owners.
10. Verify exact saved content, tests and Actions evidence.

This file is an agent policy and navigation index. It is NOT:
- a second Control Center or state store;
- an execution planner or task-authorization engine;
- a replacement for ACRL T07/T14/T16/T17/T18/T19/T20/T21/T22/T23/T24/T25-
  T30;
- a replacement for backend, frontend or AI implementation plans;
- a Git synchronization runner;
- a source of live state or current CI results;
- a new repository research database or evidence registry.

CANONICAL AUTHORITIES:
- Execution state: REOS_CONTROL_CENTER/data/state.json
- Code and history: GitHub branch reos-development
- Task transitions: existing REOS Control Center
- T07: new-chat bootstrap
- T14: repository intelligence and fast-resume assessment
- T15: AI operator autonomy boundary
- T16: repository intelligence and file discovery
- T17: change-impact and dependency analysis
- T18: execution authorization
- T19: intelligent test selection and failure diagnosis
- T20: patch and repair verification
- T21: Git repository coordination
- T22: commit and checkpoint coordination
- T23: evidence resolution
- T24: continuity and recovery
- T25: context, token and work-budget management
- T26: bounded execution-loop control
- T27: dependency-aware work scheduling
- T28: conflict resolution and reconciliation
- T29: human decision boundary
- T30: completion proof and handoff

Chat history, memory, handoff packets, old continuity snapshots and plans
provide context only. They never override live state.json or live GitHub.

EFFICIENCY PRINCIPLE:
Reuse validated evidence and existing owners. Refresh only what changed.
Never skip a required authority, integrity, security or acceptance check merely
to reduce reads or token usage.
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

# Existing owner-controlled activation point for the EntryPoint contract
# regression. This is a reference to the existing ACRL runtime path, not a
# new runner or a second CI orchestration layer.
ACRL_RUNTIME_RESUME_SCRIPT_RELATIVE_PATH = (
    ".github/actions/homio-backend-ci/verification/scripts/"
    "acrl_runtime_resume.sh"
)

ENTRYPOINT_CONTRACT_TEST_RELATIVE_PATH = (
    "REOS_CONTROL_CENTER/tets/test_ai_agent_entrypoint_contract.py"
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
# 1A. ENGINEERING SKILL ORCHESTRATION — SUPERPOWERS
# ===========================================================================

# Superpowers is an agent-runtime skill provider.
#
# It is NOT:
# - a Python package dependency;
# - an ACRL layer;
# - a project task authority;
# - a state-management engine;
# - a GitHub synchronization runner.
#
# This policy instructs a HOMIO engineering agent to discover and invoke
# available Superpowers skills at session start and route work to the
# appropriate skill workflow.
#
# Skill invocation is performed by the agent runtime. This module does not
# pretend to activate external plugins through Python code.

ENGINEERING_SKILL_PROVIDER = "Superpowers"

ENGINEERING_SKILL_ENTRYPOINT = "using-superpowers"

ENGINEERING_SKILL_ROUTING: dict[str, tuple[str, ...]] = {

    "new_feature_or_behavior": (
        "brainstorming",
        "test-driven-development",
    ),

    "architecture_or_design_change": (
        "brainstorming",
        "writing-plans",
    ),

    "bug_or_test_failure": (
        "systematic-debugging",
        "test-driven-development",
    ),

    "approved_plan_execution": (
        "executing-plans",
        "test-driven-development",
    ),

    "review_feedback": (
        "receiving-code-review",
    ),

    "major_implementation_review": (
        "requesting-code-review",
    ),

    "completion_and_release_claim": (
        "verification-before-completion",
    ),

}

ENGINEERING_SKILL_WORKFLOW_RULES: tuple[str, ...] = (

    "At the start of every HOMIO engineering session, discover the "
    "currently available agent skills.",

    "Invoke using-superpowers before the first engineering response "
    "or action, including clarification, repository inspection and debugging.",

    "Read the current skill instructions before applying a skill. "
    "Do not rely on remembered or outdated skill instructions.",

    "Select task-specific skills from ENGINEERING_SKILL_ROUTING "
    "before performing the corresponding work.",

    "For new functionality or behavior changes, use brainstorming "
    "before implementation and respect its design-approval boundary.",

    "For bugs, unexpected behavior and failed tests, use "
    "systematic-debugging before proposing or applying a fix.",

    "For implementation changes, use test-driven-development before "
    "production code changes unless the skill explicitly permits an exception.",

    "Use writing-plans only after the applicable design approval boundary.",

    "Use executing-plans only for an approved implementation plan.",

    "Use verification-before-completion before claiming any implementation "
    "is fixed, complete, passing or production-ready.",

    "Use requesting-code-review for major changes and receiving-code-review "
    "when review feedback is supplied.",

    "If Superpowers is unavailable in the current agent runtime, use the "
    "equivalent disciplined engineering workflow and report that the "
    "external skill provider was unavailable.",

    "Never claim a skill was invoked unless its instructions were actually "
    "loaded and followed.",

    "Superpowers skill execution is session-local workflow metadata. "
    "Do not persist plugin activation state in state.json, T07 restart "
    "payloads or T14 repository manifests.",

    "Superpowers does not grant task authorization, approve architecture, "
    "mutate canonical state or override ACRL boundaries.",

    "Do not add a repository-side plugin API, Python dependency, "
    "standalone skill runner or duplicate orchestration engine.",

)


# ===========================================================================
# 2. ACRL PATH OWNERSHIP
# ===========================================================================

AUTONOMY_ENGINE_PATH = CONTROL_CENTER_PATH / "AUTONOMY_ENGINE"
ACRL_PATH = AUTONOMY_ENGINE_PATH / "continuity" / "acrl"

ACRL_T03_STATE_RECONSTRUCTION = (
    ACRL_PATH / "T03_State_Reconstruction"
)

ACRL_T07_PATH = ACRL_PATH / "T07_New_Chat_Bootstrap"

ACRL_ENTRYPOINT = (
    ACRL_T07_PATH / "new_chat_bootstrap.py"
)

ACRL_T08_CONTEXT_COMPRESSION = (
    ACRL_PATH / "T08_Context_Compression"
)

ACRL_T09_STATE_FINGERPRINT = (
    ACRL_PATH / "T09_State_Fingerprint"
)

ACRL_T12_RESUME_SAFETY = (
    ACRL_PATH / "T12_Resume_Safety_Validation"
)

ACRL_REPOSITORY_CONTEXT = (
    ACRL_PATH / "T14_Repository_Intelligence_Context"
)

ACRL_T14_FULL_REGRESSION = (
    ACRL_PATH / "T14_Full_Regression"
)

ACRL_OPERATOR_AUTONOMY = (
    ACRL_PATH / "T15_AI_Operator_Autonomy"
)

ACRL_T16_REPOSITORY_DISCOVERY = (
    ACRL_PATH / "T16_Repository_Intelligence_File_Discovery"
)

ACRL_T17_CHANGE_IMPACT = (
    ACRL_PATH / "T17_Change_Impact_Dependency_Analysis"
)

ACRL_EXECUTION_AUTHORIZATION = (
    ACRL_PATH / "T18_Safe_Execution_Authorization_Guard"
)

ACRL_T19_TEST_SELECTION = (
    ACRL_PATH / "T19_Intelligent_Test_Selection_Failure_Diagnosis"
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

ACRL_T25_CONTEXT_BUDGET = (
    ACRL_PATH / "T25_Context_Token_Work_Budget_Manager"
)

ACRL_T26_EXECUTION_LOOP = (
    ACRL_PATH / "T26_Autonomous_Execution_Loop_Controller"
)

ACRL_T27_WORK_SCHEDULER = (
    ACRL_PATH / "T27_Dependency_Aware_Work_Scheduler"
)

ACRL_T28_CONFLICT_RECONCILIATION = (
    ACRL_PATH / "T28_Conflict_Resolution_Reconciliation_Engine"
)

ACRL_T29_HUMAN_DECISION = (
    ACRL_PATH / "T29_Human_Decision_Boundary_Controller"
)

ACRL_T30_COMPLETION_HANDOFF = (
    ACRL_PATH / "T30_Autonomous_Completion_Handoff_Engine"
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
#
# This registry is navigation only. It does not own repository content,
# task state, evidence storage, execution or approvals.

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

    "acrl_t03": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T03_State_Reconstruction"
        ),
        "role": (
            "Existing state reconstruction and independently supplied "
            "state evidence."
        ),
        "authority": "STATE_RECONSTRUCTION_BOUNDARY",
    },

    "acrl_t07": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T07_New_Chat_Bootstrap/new_chat_bootstrap.py"
        ),
        "role": (
            "New-chat bootstrap, restart-payload validation and "
            "checkpoint/state coherence."
        ),
        "authority": "CONTINUITY_NOT_EXECUTION_AUTHORITY",
    },

    "acrl_t08": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T08_Context_Compression"
        ),
        "role": (
            "Existing context compression owner. Compression must preserve "
            "authority, evidence identity, blockers and recovery boundaries."
        ),
        "authority": "CONTEXT_COMPRESSION_BOUNDARY",
    },

    "acrl_t09": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T09_State_Fingerprint"
        ),
        "role": (
            "Existing state fingerprint and integrity support."
        ),
        "authority": "STATE_FINGERPRINT_BOUNDARY",
    },

    "acrl_t12": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T12_Resume_Safety_Validation"
        ),
        "role": (
            "Existing resume safety validation. No stale or conflicting "
            "continuity input may bypass it."
        ),
        "authority": "RESUME_SAFETY_BOUNDARY",
    },

    "acrl_t14": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T14_Repository_Intelligence_Context"
        ),
        "role": (
            "Repository context, audited-path knowledge, research/CI "
            "evidence cache and fast-resume assessment. Cache is derived, "
            "disposable and non-authoritative."
        ),
        "authority": "DERIVED_CONTEXT_ONLY",
    },

    "acrl_t14_full_regression": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T14_Full_Regression"
        ),
        "role": (
            "Existing complete ACRL regression owner. A focused test pass "
            "does not replace required full regression."
        ),
        "authority": "REGRESSION_TEST_OWNER",
    },

    "acrl_t15": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T15_AI_Operator_Autonomy"
        ),
        "role": "AI operator autonomy boundaries.",
        "authority": "EXECUTION_BOUNDARY",
    },

    "acrl_t16": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T16_Repository_Intelligence_File_Discovery"
        ),
        "role": (
            "Read-only repository discovery, file classification, source "
            "topology, dependency/import intelligence and deterministic "
            "repository snapshots."
        ),
        "authority": "REPOSITORY_DISCOVERY_OWNER",
    },

    "acrl_t17": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T17_Change_Impact_Dependency_Analysis"
        ),
        "role": (
            "Existing change-impact and dependency analysis before "
            "choosing the targeted re-audit scope."
        ),
        "authority": "CHANGE_IMPACT_BOUNDARY",
    },

    "acrl_t18": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T18_Safe_Execution_Authorization_Guard"
        ),
        "role": "Execution authorization.",
        "authority": "AUTHORIZATION_BOUNDARY",
    },

    "acrl_t19": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T19_Intelligent_Test_Selection_Failure_Diagnosis"
        ),
        "role": (
            "Read-only impact-based test selection, failure classification, "
            "root-cause candidates and deterministic diagnostics."
        ),
        "authority": "TEST_SELECTION_AND_DIAGNOSIS_OWNER",
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
        "role": (
            "Resolve supplied evidence identities, provenance, freshness, "
            "fingerprints and authority. It does not perform general GitHub "
            "search or invent missing references."
        ),
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

    "acrl_t25": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T25_Context_Token_Work_Budget_Manager"
        ),
        "role": (
            "Bounded context, token and work-budget calculation and "
            "reservation. It cannot execute or authorize project work."
        ),
        "authority": "RESOURCE_BUDGET_BOUNDARY",
    },

    "acrl_t26": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T26_Autonomous_Execution_Loop_Controller"
        ),
        "role": (
            "Bounded loop progression, retry limits, checkpoint gates, "
            "progress and safe-stop decisions. It does not execute commands."
        ),
        "authority": "BOUNDED_LOOP_CONTROL_ONLY",
    },

    "acrl_t27": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T27_Dependency_Aware_Work_Scheduler"
        ),
        "role": (
            "Deterministic dependency-aware work scheduling. It does not "
            "execute scheduled work or authorize it."
        ),
        "authority": "SCHEDULING_ONLY",
    },

    "acrl_t28": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T28_Conflict_Resolution_Reconciliation_Engine"
        ),
        "role": (
            "Conflict classification, evidence-based precedence and "
            "reconciliation. It cannot override a required human decision."
        ),
        "authority": "RECONCILIATION_BOUNDARY",
    },

    "acrl_t29": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T29_Human_Decision_Boundary_Controller"
        ),
        "role": (
            "Determine and enforce when a human decision is required. "
            "The agent cannot create or infer human approval."
        ),
        "authority": "HUMAN_DECISION_BOUNDARY",
    },

    "acrl_t30": {
        "path": (
            "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
            "T30_Autonomous_Completion_Handoff_Engine"
        ),
        "role": (
            "Completion proof quorum, residual-work detection, dependency "
            "closure and continuity-preserving handoff."
        ),
        "authority": "COMPLETION_PROOF_AND_HANDOFF_BOUNDARY",
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
            ENTRYPOINT_CONTRACT_TEST_RELATIVE_PATH
        ),
        "role": (
            "Automated regression for EntryPoint identity, ownership, "
            "continuity, session efficiency, evidence reuse, diagnostics "
            "and owner-save contracts."
        ),
        "authority": "TEST_EVIDENCE",
    },
}


# ===========================================================================
# 4A. ACRL OWNER MAP — REUSE, DO NOT DUPLICATE
# ===========================================================================

# This is a routing map only. It does not create a new execution layer.
# Each responsibility remains with its existing ACRL owner.

ACRL_OWNER_ROUTING: dict[str, str] = {

    "bootstrap": "acrl_t07",

    "resume_and_repository_context": "acrl_t14",

    "operator_autonomy": "acrl_t15",

    "repository_discovery_and_snapshot": "acrl_t16",

    "change_impact_and_dependencies": "acrl_t17",

    "execution_authorization": "acrl_t18",

    "test_selection_and_failure_diagnosis": "acrl_t19",

    "repair_and_patch_verification": "acrl_t20",

    "git_repository_coordination": "acrl_t21",

    "commit_and_checkpoint": "acrl_t22",

    "evidence_identity_and_resolution": "acrl_t23",

    "cross_chat_continuity_and_recovery": "acrl_t24",

    "context_token_and_work_budget": "acrl_t25",

    "bounded_execution_loop_control": "acrl_t26",

    "dependency_aware_scheduling": "acrl_t27",

    "conflict_reconciliation": "acrl_t28",

    "human_decision_boundary": "acrl_t29",

    "completion_proof_and_handoff": "acrl_t30",

}


# ===========================================================================
# 4B. SESSION EFFICIENCY POLICY — EXISTING OWNERS ONLY
# ===========================================================================

# These constants describe how the agent must use existing sources.
# They are not a runtime cache, registry, search engine, scheduler or authority.

SESSION_EFFICIENCY_RULES: tuple[str, ...] = (

    "Reuse-first: check existing source registry, exact references and "
    "current evidence before starting another broad search.",

    "One live authority refresh per session baseline: independently obtain "
    "the current reos-development HEAD and state.json blob SHA before "
    "selecting work.",

    "Task-specific reads: read the exact active task, its acceptance "
    "criteria, its selected master reference and only the source owners "
    "that affect the authorized task.",

    "Preserve original architecture: do not remove original EntryPoint "
    "sections, public function names, workstream boundaries or existing "
    "document registry entries merely to shorten context.",

    "T14 first: retrieve the current externally generated T14 resume "
    "artifact when the exact run artifact is available.",

    "T14 decisions: FAST_RESUME permits reuse of still-valid audited "
    "context; TARGETED_REAUDIT limits work to changed paths, dependents, "
    "affected findings and stale evidence; FULL_AUDIT_REQUIRED requires "
    "a new complete baseline; INVALID_MANIFEST is rejected.",

    "T14 cache never has task authority. Live state.json, GitHub HEAD, "
    "file blob SHAs and current execution evidence must be independently "
    "observed.",

    "T14 initialisation: an absent, UNINITIALIZED, malformed, stale or "
    "invalid manifest does not get manually sealed by the agent. Use the "
    "existing CI cache-generation and artifact-publication process.",

    "T16 one-snapshot rule: create or retrieve one deterministic repository "
    "discovery snapshot for one investigation batch and reuse it while "
    "its repository identity, branch, HEAD and relevant path fingerprints "
    "remain unchanged.",

    "T16 invalidation: do not reuse a snapshot after repository, branch, "
    "HEAD, tracked-path content, symlink boundary or relevant repository "
    "inventory has changed.",

    "T17 impact rule: use the existing change-impact/dependency analysis "
    "to identify affected owners and dependents instead of re-reading "
    "unrelated repository modules.",

    "T23 evidence rule: resolve supplied exact evidence identities through "
    "the existing T23 engine. T23 does not perform general GitHub search, "
    "invent evidence URLs or turn a search result into proof.",

    "Research reuse: reuse a research reference only when its exact identity, "
    "retrieval time, source URL, scope and freshness are available and "
    "remain applicable to the current question.",

    "Research refresh: a changed source, changed task scope, expired "
    "evidence, conflicting result or missing evidence identity requires "
    "a targeted fresh lookup rather than silent reuse.",

    "No duplicate search: do not repeat a lookup already completed in the "
    "same investigation batch unless its source changed, its scope was "
    "insufficient or its evidence could not be resolved.",

    "No fake memory: model memory, conversation history and summaries "
    "may identify likely references but do not prove current repository "
    "state, file contents, run conclusions or task status.",

    "CI deduplication: identify a failure by repository, branch, workflow, "
    "run ID, attempt, tested SHA, job, failing step and normalized error "
    "signature before deciding whether it is a new failure.",

    "CI retry rule: do not repeat a workflow run merely because the user "
    "re-shared its Actions URL. First inspect the existing run, attempt, "
    "jobs and tested SHA. Retry only when the failure classification and "
    "current task justify a rerun.",

    "Failure learning: reuse a verified root-cause diagnosis for the same "
    "unchanged error signature and code SHA. Re-evaluate when the SHA, "
    "failing step, environment or error signature changes.",

    "T19 test selection: use the smallest relevant deterministic test set "
    "for early diagnosis, then run the required existing owner/domain "
    "regressions and complete mandated suites before completion claims.",

    "T19 limitation: test selection and failure diagnosis are read-only. "
    "They do not run tests, repair code, authorize changes or declare "
    "a task complete.",

    "Implementation-first after evidence: once task authority, ownership, "
    "target content and required dependencies are established, stop "
    "repeating broad research and perform the authorized work.",

    "Batch coherent changes by ownership and dependency. Do not split "
    "one logical replacement into repeated micro-edits when one complete "
    "replacement is required.",

    "No hidden implementation: a read-only audit or a proposed replacement "
    "does not mean a file was changed, saved, read back or tested.",

    "Context discipline: keep essential authority, exact paths, blob SHAs, "
    "evidence IDs, blockers and current decisions. Compress repeated "
    "narrative rather than deleting technical requirements.",

    "T25 budget: use the existing T25 resource budget owner where the "
    "runtime exposes it. Never assume actual remaining model tokens, "
    "increase budgets implicitly or use memory as budget authority.",

    "T26-T30 boundaries: loop control, scheduling, reconciliation, human "
    "decisions and completion handoff retain their existing boundaries. "
    "None becomes a second project executor or state authority.",

    "State-change reset: a changed state.json blob SHA invalidates a prior "
    "task selection and resume conclusion. Re-bootstrap from the new live "
    "state before continuing.",

    "Branch-change reset: a changed branch HEAD requires exact target "
    "readback and evidence invalidation analysis before preparing another "
    "replacement.",

    "One authority per responsibility: do not add another research store, "
    "resume cache, test selector, evidence engine, checkpoint engine, "
    "session manager, orchestration engine or handoff registry.",

    "Never trade required verification, security, privacy, authorization "
    "or acceptance criteria for fewer reads or shorter output.",

)


# ===========================================================================
# 4C. T14 RESUME DECISION CONTRACT
# ===========================================================================

T14_RESUME_DECISIONS: tuple[str, ...] = (
    "FAST_RESUME",
    "TARGETED_REAUDIT",
    "FULL_AUDIT_REQUIRED",
    "INVALID_MANIFEST",
)

T14_RESUME_RULES: tuple[str, ...] = (

    "A T14 manifest is a derived non-authoritative cache, never canonical "
    "project state or task authorization.",

    "Use only the existing external Actions cache/artifact contract. "
    "Do not create a second cache location or commit a sealed runtime "
    "manifest into the repository.",

    "Identify the exact artifact by the existing "
    "homio-acrl-audit-resume-<HEAD-SHA>-<RUN-ID>-<ATTEMPT> naming contract.",

    "Verify the artifact run ID, attempt, repository, branch and tested "
    "HEAD before reading its manifest as a candidate for reuse.",

    "Independently fetch live branch HEAD and the exact state.json blob SHA.",

    "Independently verify working-tree cleanliness where the T14 input "
    "contract requires it. Do not infer cleanliness from a prior run.",

    "Supply independently observed changed paths, deleted paths, "
    "current path blob SHAs, delta base commit and current execution "
    "position to T14 assessment.",

    "FAST_RESUME is permitted only when the manifest is valid and its "
    "repository, branch, HEAD, state SHA, path identities, current position "
    "and evidence freshness all match the live snapshot.",

    "TARGETED_REAUDIT is permitted only when T14 identifies the exact "
    "invalidated paths, dependent closure, affected findings or stale "
    "evidence. Re-audit those affected responsibilities and retain the "
    "unaffected verified baseline.",

    "FULL_AUDIT_REQUIRED applies when the manifest is absent, uninitialized, "
    "invalid, unverifiable, based on a different state SHA, has an unproven "
    "HEAD delta, or cannot establish complete live repository identity.",

    "INVALID_MANIFEST is not a degraded FAST_RESUME. Reject its contents "
    "as reusable evidence and follow the returned full-audit requirement.",

    "Never treat manifest position_snapshot as current task authority. "
    "Use the live state.json execution position.",

    "Never use stale CI evidence as proof for a new commit SHA.",

    "Never manually change audit_resume_manifest.json status to SEALED. "
    "Do not manually seal, edit or promote the derived manifest; only the "
    "existing CI-owned cache-generation process may produce its status.",

    "Only the existing CI cache-generation process may build, validate "
    "and publish the external derived artifact.",

    "If the exact artifact cannot be retrieved, report that limitation "
    "and continue only with an independently supported live baseline.",

)


# ===========================================================================
# 4D. RESEARCH AND EVIDENCE REUSE CONTRACT
# ===========================================================================

RESEARCH_REUSE_RULES: tuple[str, ...] = (

    "Before a fresh search, inspect the existing source registry and the "
    "evidence already available in the current investigation context.",

    "Store no new research index in this EntryPoint. Use the existing "
    "T14 research_evidence cache and T23 evidence resolution owner.",

    "A reusable research record must have an exact evidence identity, "
    "canonical source URL, source scope, retrieval timestamp and any "
    "required source/version identity.",

    "Do not invent evidence identities, source URLs, citations, retrieval "
    "timestamps or source provenance. Report an unresolved reference instead "
    "of fabricating missing evidence.",

    "A prior search result is not automatically valid for a different "
    "task, a changed source, a new HEAD or a changed acceptance criterion.",

    "Reuse exact search results within the same investigation batch. "
    "Do not re-run identical searches merely to reconfirm already "
    "resolved facts.",

    "Perform a targeted refresh when evidence is stale, conflicting, "
    "incomplete or insufficient for a claim.",

    "Use T23 to resolve a supplied evidence identity and its provenance. "
    "If the identity does not resolve, report the missing reference instead "
    "of fabricating a substitute.",

    "Distinguish source code evidence, architecture evidence, test evidence, "
    "Actions evidence, state-transition evidence and human approval.",

    "An Actions URL is a locator, not a PASS result. Verify the run, "
    "attempt, workflow, job conclusion and exact tested SHA.",

    "A historical passing run must remain historical when it tests a "
    "different SHA from the current branch HEAD.",

    "A search performed in an earlier chat may be reused only after "
    "freshness, source identity and scope are checked.",

)


# ===========================================================================
# 4E. CI FAILURE DEDUPLICATION CONTRACT
# ===========================================================================

CI_FAILURE_DEDUPLICATION_RULES: tuple[str, ...] = (

    "Inspect the current backend-ci run before repeating an analysis "
    "already performed for that same run and attempt.",

    "Record failure identity using repository, branch, workflow path, "
    "workflow run ID, attempt, tested head_sha, job name, failed step "
    "and normalized error signature.",

    "Classify failures as application/source regression, test regression, "
    "workflow/action configuration, dependency/build, runner/environment, "
    "external service or Control Center/governance failure.",

    "Do not classify a skipped guarded transition as a test failure when "
    "its guard was not satisfied. Report it as skipped/not applicable.",

    "Do not combine separate attempts without preserving their individual "
    "run evidence and tested commit identities.",

    "When the same unchanged SHA and same error signature recur, reuse "
    "the verified diagnosis and investigate the unresolved cause instead "
    "of repeating generic research.",

    "When source SHA or error signature changes, re-evaluate the root cause "
    "and select tests using T19 and impact data from T17.",

    "Do not rerun an entire workflow merely to obtain a newer timestamp "
    "when the existing run already proves the exact requested commit.",

    "Do not rerun only failed jobs unless the current task, workflow policy "
    "and evidence state permit that retry.",

    "Never claim CI PASS based only on workflow status text, a green badge, "
    "a prior run or an unverified Actions URL.",

)


# ===========================================================================
# 4F. CONTEXT AND WORK-BUDGET CONTRACT
# ===========================================================================

CONTEXT_BUDGET_RULES: tuple[str, ...] = (

    "Use T25 as the existing context, token and work-budget owner where "
    "available. This EntryPoint does not calculate or reserve budgets.",

    "Do not claim knowledge of the runtime's exact remaining model-token "
    "capacity unless that value is explicitly available.",

    "Do not increase budgets implicitly, infer unused capacity or bypass "
    "the existing T25 budget decision and reservation boundaries.",

    "Prioritize live authority, current task, acceptance criteria, source "
    "ownership, exact references, failing tests, evidence and blockers.",

    "Compress repeated explanations, old narrative and duplicated search "
    "results before compressing technical requirements or evidence identity.",

    "Do not discard original architecture decisions, security conditions, "
    "dependency order, ownership boundaries or required tests to save tokens.",

    "Use a concise investigation summary only after exact source and "
    "evidence identity have been preserved.",

    "When the current context cannot safely hold the required task evidence, "
    "use the existing T24/T25 continuity and budget boundaries rather than "
    "silently dropping required context.",

    "Never allow budget exhaustion to authorize incomplete verification, "
    "unreviewed changes or task advancement.",

)


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

    "Reuse the existing T24 continuity and T30 handoff owners. Do not create "
    "another chat-handoff registry.",

)


# ===========================================================================
# 7. EVIDENCE AND CI VERIFICATION RULES
# ===========================================================================

EVIDENCE_VERIFICATION_RULES: tuple[str, ...] = (

    "A commit is not tested merely because a prior commit passed.",

    "A GitHub Actions run proves only the exact head_sha recorded by that run.",

    "Before reporting CI PASS, verify repository, branch, workflow name, "
    "run ID, attempt, conclusion, tested SHA, required jobs/steps and "
    "relevant artifacts.",

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

    "Use T23 to resolve supplied evidence identity, provenance and freshness. "
    "A URL alone is not proof.",

    "Keep state-transition evidence separate from implementation/test evidence.",

    "Keep human approval evidence separate from AI-generated summaries.",

    "A successful test suite does not itself complete the Control Center task.",

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

    "resume_assessment": (
        "ACRL T14_Repository_Intelligence_Context"
    ),

    "repository_discovery": (
        "ACRL T16_Repository_Intelligence_File_Discovery"
    ),

    "change_impact": (
        "ACRL T17_Change_Impact_Dependency_Analysis"
    ),

    "test_selection_and_diagnosis": (
        "ACRL T19_Intelligent_Test_Selection_Failure_Diagnosis"
    ),

    "evidence_resolution": (
        "ACRL T23_Reference_Evidence_Resolution_Engine"
    ),

    "context_and_work_budget": (
        "ACRL T25_Context_Token_Work_Budget_Manager"
    ),

    "loop_and_schedule_control": (
        "ACRL T26 and T27"
    ),

    "conflict_and_human_decisions": (
        "ACRL T28 and T29"
    ),

    "completion_and_handoff": (
        "ACRL T30_Autonomous_Completion_Handoff_Engine"
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

    "0. Discover available engineering skills and invoke using-superpowers "
    "before the first engineering response or action.",

    "1. Read AI_AGENT_ENTRYPOINT.py once for policy, document registry, "
    "workstream routing, efficiency rules and owner boundaries.",

    "2. Fetch the live GitHub branch reos-development and record its "
    "current HEAD SHA. Do not infer it from memory or an earlier chat.",

    "3. Fetch REOS_CONTROL_CENTER/data/state.json, record its blob SHA "
    "and read the active gate, task, subtask, dependencies and criteria.",

    "4. Validate state integrity through the existing Control Center boundary. "
    "Do not manually patch state.json.",

    "5. Reuse the existing T07 bootstrap and inspect its restart/checkpoint "
    "coherence only when relevant to the current resume.",

    "6. Retrieve the exact current external T14 resume artifact when available. "
    "Validate its run identity, HEAD, state SHA and current source evidence.",

    "7. Apply the T14 FAST_RESUME, TARGETED_REAUDIT, FULL_AUDIT_REQUIRED "
    "or INVALID_MANIFEST decision. Never decide cache validity by intuition.",

    "8. Read NEW_CHAT_PACKET.txt only as a derived snapshot. Compare its "
    "task fields with live state.json.",

    "9. Read the selected workstream's master reference and only the "
    "approved architecture references needed by that task.",

    "10. Use T16 for one repository-discovery snapshot per investigation "
    "batch. Reuse it while its source identity and fingerprints remain valid.",

    "11. Use T17 to resolve changed-path impact and dependent closure when "
    "source changes affect multiple owners.",

    "12. Use T23 to resolve supplied exact evidence identities. Do not "
    "repeat broad research when valid evidence is already available.",

    "13. Inspect exact target source paths, callers, contracts and ownership. "
    "Read unrelated files only when dependency evidence requires them.",

    "14. Use T19 to select the smallest relevant deterministic diagnostic "
    "test set, then preserve mandatory owner regression requirements.",

    "15. Apply T15/T18/T20/T21/T22/T23/T24/T25-T30 boundaries as applicable.",

    "16. Implement only the authorized scope and disjoint file set.",

    "17. Verify exact saved content, focused tests, required regressions, "
    "Actions result and residual blockers against the same tested SHA.",

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

    "Use T16 for repository discovery and source topology.",

    "Use T17 for change impact and dependency closure.",

    "Use T19 for read-only test selection and failure diagnosis.",

    "Use T23 for evidence identity and provenance resolution.",

    "Use T25 for explicit context, token and work-budget boundaries.",

    "Respect T15 AI Operator Autonomy boundaries.",

    "Respect architecture locks and Control Center authority.",

    "Never directly modify authoritative state to manufacture completion.",

    "Never self-authorize execution or self-approve governance changes.",

    "Do not assume a local checkout matches the live GitHub branch.",

    "Local preflight is optional diagnostics only. It is not live GitHub proof.",

    "Do not claim tests or CI passed without evidence for the exact tested SHA.",

    "Run focused verification and relevant regressions before declaring success.",

    "When evidence conflicts or is insufficient, stop and report the blocker.",

    "Do not repeat completed repository searches without a freshness, scope "
    "or evidence-resolution reason.",

    "Once an exact owner, target path and valid evidence have been established, "
    "perform the authorized implementation instead of extending generic audits.",

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
    "contract regression through the existing ACRL runtime verification "
    "script at .github/actions/homio-backend-ci/verification/scripts/"
    "acrl_runtime_resume.sh.",

    "The existing ACRL runtime script must execute "
    "tets/test_ai_agent_entrypoint_contract.py as a required regression "
    "before its other ACRL runtime regression groups.",

    "The EntryPoint contract test must not be silently skipped if its file "
    "is missing or fails. The existing fail-fast execution boundary must "
    "remain enabled.",

    "Do not create, download, invoke or rely on a standalone runner as "
    "a competing workflow authority.",

    "For a coherent full-file replacement, supply the complete file and "
    "retain unrelated original responsibilities unless evidence justifies "
    "a change.",

    "Do not send repeated micro-edits for one logical replacement when "
    "a complete replacement is required.",

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

    "T07, T14, T16, T17, T19 and T25-T30 responsibilities must be reused "
    "rather than duplicated.",

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

    "4. Retrieve and validate the current T14 resume artifact when available.",

    "5. Determine the required audit scope from the T14 assessment decision.",

    "6. Inspect exact requested paths and existing responsibility owners.",

    "7. Use T16/T17 for one discovery snapshot and targeted dependency impact.",

    "8. Use T23 to resolve supplied evidence references and freshness.",

    "9. Use T19 to select relevant tests and diagnose known failures.",

    "10. Classify every requested file action.",

    "11. Resolve applicable architecture, task and dependency constraints.",

    "12. Confirm that the current task is authorized by the Control Center.",

    "13. Apply required ACRL authorization and patch-verification boundaries.",

    "14. Provide complete implementation content for owner-approved changes.",

    "15. Let the owner save through GitHub web editor under the default agreement.",

    "16. Verify branch, commit parent and exact changed-file content.",

    "17. Run focused tests and relevant regression checks.",

    "18. Inspect CI for the exact commit SHA.",

    "19. Resolve missing or conflicting evidence through applicable ACRL boundaries.",

    "20. Change canonical state only through the existing Control Center workflow.",

    "21. Never report PASS without independent verification evidence.",

)


# ===========================================================================
# 16. REQUIRED NEW-SESSION WORKFLOW
# ===========================================================================

NEW_SESSION_WORKFLOW: tuple[str, ...] = (

    "0. Discover available engineering skills and invoke using-superpowers "
    "before any engineering response or action.",

    "1. Identify HOMIO / REOS and declare BACKEND, FRONTEND or SHARED_INTEGRATION.",

    "2. Read this EntryPoint and use its existing document registry, "
    "workstream routing and session-efficiency rules.",

    "3. Independently fetch live reos-development HEAD, branch metadata "
    "and repository identity.",

    "4. Fetch data/state.json, record its blob SHA and read current gate, "
    "task, subtask, dependencies and acceptance criteria.",

    "5. Validate state integrity through the existing Control Center boundary.",

    "6. Treat state.json as the only execution-state authority. A plan does "
    "not authorize a new or parallel task.",

    "7. Reuse ACRL T07 bootstrap and T14 repository context; refresh inputs "
    "and reject stale evidence.",

    "8. Retrieve the exact current external T14 artifact when available. "
    "Validate its source run, attempt, HEAD and state blob SHA.",

    "9. Use the T14 result to choose FAST_RESUME, TARGETED_REAUDIT or "
    "FULL_AUDIT_REQUIRED. Reject INVALID_MANIFEST.",

    "10. Read NEW_CHAT_PACKET.txt only as a derived snapshot and compare it "
    "with live state.json.",

    "11. Read approved architecture and the selected workstream master plan.",

    "12. Consult the counterpart workstream plan only for API, auth, tenant "
    "and integration boundaries.",

    "13. Use T16 for one repository snapshot per investigation batch and "
    "T17 for the affected dependency closure.",

    "14. Use T23 to resolve exact evidence identities and reuse valid "
    "research/CI evidence. Do not repeat identical broad searches.",

    "15. Inspect exact target files, source owners, callers, contracts, "
    "tests, workflow path filters and relevant commits.",

    "16. Use T19 to select relevant tests and classify existing failure "
    "evidence before repeating diagnostics.",

    "17. Declare allowed paths, excluded paths, shared dependencies and "
    "whether canonical state authorizes implementation.",

    "18. Apply T15/T18/T20/T21/T22/T23/T24/T25-T30 boundaries as applicable.",

    "19. Provide complete replacement content and exact GitHub paths.",

    "20. Refresh live HEAD and target blob after every save.",

    "21. Run focused tests, owner regressions and required full regression "
    "CI on the exact saved SHA.",

    "22. Record test scope, run ID, attempt, tested SHA, artifacts, evidence "
    "and residual risks.",

    "23. Advance state only through the existing Control Center transition.",

    "24. Report verified position and the first valid next step without "
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

    "Do not ask the owner to repeat a reference, path or evidence link that "
    "is already available and still valid in the current investigation.",

    "Do not send fragmented edits when the requested deliverable is a "
    "complete file replacement.",

)


# ===========================================================================
# 18. CHANGE DECISION RULES
# ===========================================================================

CHANGE_DECISION_RULES: tuple[str, ...] = (

    "FIRST: inspect the current canonical GitHub repository state.",

    "SECOND: inspect canonical state.json and task authorization.",

    "THIRD: retrieve and validate reusable T14 context when available.",

    "FOURTH: inspect existing ownership of the responsibility.",

    "FIFTH: classify the requested action.",

    "SIXTH: use T16/T17 to identify the exact affected source and dependencies.",

    "SEVENTH: use T23 to resolve existing evidence before repeating searches.",

    "EIGHTH: use T19 to select tests and inspect failure diagnosis.",

    "NINTH: determine whether the existing owner can be safely extended.",

    "TENTH: verify completed-layer boundaries before implementation.",

    "ELEVENTH: inspect impact on the other workstream and shared API contracts.",

    "NEVER: create duplicate modules, routes, components or sources of truth.",

    "NEVER: treat a stale local checkout as proof a file is missing.",

    "NEVER: reopen a completed layer without repository evidence.",

    "NEVER: treat this EntryPoint as authorization to bypass the Control Center.",

    "NEVER: repeat a completed search without an identified freshness, "
    "scope, integrity or evidence-resolution reason.",

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

    "If a T14 artifact cannot establish current HEAD or state SHA, reject "
    "its reuse and follow the appropriate re-audit decision.",

    "If T16 source identity or snapshot fingerprint changed, refresh the "
    "repository discovery snapshot before relying on it.",

    "If T23 cannot resolve an evidence identity, do not invent a URL or citation.",

    "If T19 selects no safe test set, do not guess a test command; report "
    "the missing impact/evidence input.",

    "If T25 reports budget exhaustion, do not silently ignore it or "
    "increase limits.",

    "If tests fail, diagnose the actual failure before changing implementation.",

    "If an approved implementation is green, do not redesign it without evidence.",

    "If a change introduces duplicate responsibility, reject it.",

    "If execution authority is required but unavailable, fail closed.",

    "If project state cannot be safely reconstructed, do not manufacture state.",

    "If remote writes or manual saves cannot be independently verified, "
    "do not report PASS.",

    "If two chats changed the same target path, stop and reconcile before "
    "preparing another replacement.",

    "If an Actions run is already available for the exact SHA and attempt, "
    "inspect its evidence before initiating a redundant rerun.",

    "If a previously diagnosed CI error has the same tested SHA and "
    "normalized error signature, reuse its diagnosis rather than repeating "
    "generic research.",

    "If the tested SHA or failure signature changed, perform a fresh "
    "root-cause analysis.",

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

        "t03": str(ACRL_T03_STATE_RECONSTRUCTION),

        "t07": str(ACRL_ENTRYPOINT),

        "t08": str(ACRL_T08_CONTEXT_COMPRESSION),

        "t09": str(ACRL_T09_STATE_FINGERPRINT),

        "t12": str(ACRL_T12_RESUME_SAFETY),

        "t14": str(ACRL_REPOSITORY_CONTEXT),

        "t14_full_regression": str(ACRL_T14_FULL_REGRESSION),

        "t15": str(ACRL_OPERATOR_AUTONOMY),

        "t16": str(ACRL_T16_REPOSITORY_DISCOVERY),

        "t17": str(ACRL_T17_CHANGE_IMPACT),

        "t18": str(ACRL_EXECUTION_AUTHORIZATION),

        "t19": str(ACRL_T19_TEST_SELECTION),

        "t20": str(ACRL_REPAIR_VERIFICATION),

        "t21": str(ACRL_GIT_REPOSITORY_COORDINATION),

        "t22": str(ACRL_COMMIT_CHECKPOINT_COORDINATION),

        "t23": str(ACRL_EVIDENCE_RESOLUTION),

        "t24": str(ACRL_CONTINUITY_RECOVERY),

        "t25": str(ACRL_T25_CONTEXT_BUDGET),

        "t26": str(ACRL_T26_EXECUTION_LOOP),

        "t27": str(ACRL_T27_WORK_SCHEDULER),

        "t28": str(ACRL_T28_CONFLICT_RECONCILIATION),

        "t29": str(ACRL_T29_HUMAN_DECISION),

        "t30": str(ACRL_T30_COMPLETION_HANDOFF),

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
    - does not replace ACRL;
    - does not activate external plugins through Python.

    Live repository, state and skill refresh are instructions for the agent,
    not hidden network or plugin operations performed by this module.
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

        "acrl_owner_routing": dict(ACRL_OWNER_ROUTING),

        "session_efficiency_rules": list(
            SESSION_EFFICIENCY_RULES
        ),

        "t14_resume_decisions": list(
            T14_RESUME_DECISIONS
        ),

        "t14_resume_rules": list(
            T14_RESUME_RULES
        ),

        "research_reuse_rules": list(
            RESEARCH_REUSE_RULES
        ),

        "ci_failure_deduplication_rules": list(
            CI_FAILURE_DEDUPLICATION_RULES
        ),

        "context_budget_rules": list(
            CONTEXT_BUDGET_RULES
        ),

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

        "engineering_skill_provider": ENGINEERING_SKILL_PROVIDER,

        "engineering_skill_entrypoint": ENGINEERING_SKILL_ENTRYPOINT,

        "engineering_skill_routing": {
            key: list(value)
            for key, value in ENGINEERING_SKILL_ROUTING.items()
        },

        "engineering_skill_workflow_rules": list(
            ENGINEERING_SKILL_WORKFLOW_RULES
        ),

        "engineering_skill_discovery_required": True,

        "engineering_skill_execution_is_project_authority": False,

        "entrypoint_contract_regression": {
            "required": True,
            "test_path": ENTRYPOINT_CONTRACT_TEST_RELATIVE_PATH,
            "activation_script": (
                ACRL_RUNTIME_RESUME_SCRIPT_RELATIVE_PATH
            ),
            "activation_owner": (
                "Existing ACRL runtime verification path"
            ),
            "standalone_runner_allowed": False,
            "missing_or_failing_test_is_blocking": True,
        },

        "local_preflight_is_diagnostic_only": True,

        "live_github_refresh_required": True,

        "canonical_state_refresh_required": True,

        "workstream_declaration_required": True,

        "plan_documents_authorize_tasks": False,

        "t14_manifest_is_non_authoritative": True,

        "t16_one_snapshot_per_investigation_batch": True,

        "t23_resolves_supplied_evidence_not_general_search": True,

        "t19_analysis_is_read_only": True,

        "t25_budget_manager_is_not_execution_authority": True,

        "t26_loop_control_is_not_execution_authority": True,

        "t27_scheduler_is_not_execution_authority": True,

        "t28_reconciliation_cannot_bypass_human_boundary": True,

        "t29_human_approval_cannot_be_inferred": True,

        "t30_completion_requires_proof_quorum": True,

        "no_duplicate_research_orchestration_layer": True,

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

    print("SKILLS         : SUPERPOWERS DISCOVERY / TASK-SPECIFIC ROUTING")

    print("ENTRYPOINT TEST: REQUIRED EXISTING ACRL RUNTIME REGRESSION")

    print(
        "TEST ACTIVATION:",
        ACRL_RUNTIME_RESUME_SCRIPT_RELATIVE_PATH,
    )

    print(
        "TEST PATH      :",
        ENTRYPOINT_CONTRACT_TEST_RELATIVE_PATH,
    )

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
        ("T03", "State Reconstruction"),
        ("T07", "New Chat Bootstrap"),
        ("T08", "Context Compression"),
        ("T09", "State Fingerprint"),
        ("T12", "Resume Safety Validation"),
        ("T14", "Repository Intelligence Context"),
        ("T15", "AI Operator Autonomy"),
        ("T16", "Repository Intelligence / File Discovery"),
        ("T17", "Change Impact / Dependency Analysis"),
        ("T18", "Safe Execution Authorization"),
        ("T19", "Intelligent Test Selection / Failure Diagnosis"),
        ("T20", "Repair / Patch Verification"),
        ("T21", "Git Repository Coordination"),
        ("T22", "Commit / Checkpoint Coordination"),
        ("T23", "Evidence Resolution"),
        ("T24", "Continuity / Recovery"),
        ("T25", "Context / Token / Work Budget"),
        ("T26", "Bounded Execution Loop Control"),
        ("T27", "Dependency-Aware Scheduling"),
        ("T28", "Conflict Reconciliation"),
        ("T29", "Human Decision Boundary"),
        ("T30", "Completion Proof / Handoff"),
    ):

        print(f"{layer:14}: {title}")

    print("-" * 72)

    print("RULE           : SUPERPOWERS SKILL DISCOVERY BEFORE ENGINEERING")

    print("RULE           : TASK-SPECIFIC SKILL ROUTING")

    print("RULE           : LIVE STATE BEFORE TASK SELECTION")

    print("RULE           : T14 RESUME DECISION BEFORE BROAD RE-AUDIT")

    print("RULE           : T16 ONE SNAPSHOT PER INVESTIGATION BATCH")

    print("RULE           : T17 IMPACT-BASED TARGETED RE-AUDIT")

    print("RULE           : T23 EXACT EVIDENCE RESOLUTION")

    print("RULE           : T19 TARGETED TEST SELECTION")

    print("RULE           : REUSE VERIFIED CI FAILURE DIAGNOSIS")

    print("RULE           : DECLARE WORKSTREAM")

    print("RULE           : BACKEND / FRONTEND OWNERSHIP SEPARATE")

    print("RULE           : API CONTRACTS BACKEND-OWNED")

    print("RULE           : NO DUPLICATE FILES OR ENGINES")

    print("RULE           : OWNER SAVES VIA GITHUB WEB UI")

    print("RULE           : REFRESH HEAD AND TARGET SHA BEFORE SAVE")

    print("RULE           : ENTRYPOINT REGRESSION IS REQUIRED")

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
