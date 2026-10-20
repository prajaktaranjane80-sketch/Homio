# HOMIO / REOS
# GPT + GitHub Workflow Synchronization, ACRL Audit and Ordered Execution Plan

**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical branch:** `reos-development`  
**Document path:** `REOS_CONTROL_CENTER/architecture/HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md`  
**Document type:** Ordered implementation and verification plan  
**Execution authority:** `REOS_CONTROL_CENTER/data/state.json` and the existing Control Center  
**Status:** PLANNING DOCUMENT — NOT EXECUTION AUTHORITY

---

## 1. Purpose

This document defines one ordered work sequence for:

1. Fixing GPT instructions that are stale, contradictory, or inconsistent with the live repository.
2. Synchronizing GPT, GitHub, the Control Center, ACRL, and GitHub Actions without creating competing authorities.
3. Finding and correcting missing files, incorrect paths, missing regression tests, and incomplete CI coverage.
4. Fixing the platform-wide ACRL audit findings.
5. Preserving already-working code and passing functionality.
6. Verifying every change against its exact GitHub commit and test/CI evidence.
7. Reducing repeated repository scans when starting a new chat or resuming work.

The purpose is to fix the actual problems—not to create another architecture, another state store, another Git sync engine, or duplicate versions of existing modules.

## 2. Canonical authority rules

These rules apply to every phase.

| Concern | Canonical authority |
|---|---|
| Project execution state, active gate and subtask | `REOS_CONTROL_CENTER/data/state.json` |
| Current code and committed history | GitHub `reos-development` |
| Agent-facing workflow policy | `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py` |
| Execution and task control | Existing `REOS_CONTROL_CENTER/reos_control_center.py` and Control Center contracts |
| Authorization | Existing ACRL T18 and applicable project authorization contracts |
| Repair/patch verification | Existing ACRL T20 |
| Git read/write coordination | Existing ACRL T21 |
| Commit/checkpoint coordination | Existing ACRL T22 |
| Evidence resolution | Existing ACRL T23 |
| Cross-chat continuity | Existing ACRL T24 |
| Resume/cache validation | Existing T07 and T14 mechanisms |
| Backend verification | `.github/workflows/backend-ci.yml` |
| Frontend verification | `.github/workflows/frontend-ci.yml` |
| Diagnostic output | `PS Output` and `Frontend Ps Output`; diagnostics only |

Non-negotiable rules:

- Never edit `data/state.json` manually to manufacture a task transition or completion.
- Never let a GPT conversation, Markdown plan, resume manifest, or diagnostic snapshot override canonical state.
- Never assume an old local checkout matches GitHub.
- Never create a new file solely because a stale workspace appears to lack it.
- Never create a second ACRL, Control Center, source-of-truth store, identity engine, dependency graph, evidence engine, or Git synchronization engine.
- Never remove existing passing checks to make CI green.
- Never claim a test passed without identifying the tested commit and actual result.
- Never bypass GitHub permissions, branch protection, rulesets, or approval requirements.
- The Next.js frontend must not import the ACRL runtime or read `data/state.json` as live frontend application data.

## 3. Live baseline captured for this plan

The repository was inspected on the `reos-development` branch during preparation of this document.

- Observed branch HEAD: `719bd3f4ff08c1033fb765be80938d389205a4be`
- Observed `data/state.json` blob SHA: `92296fb10b0c7a37d0fc7fa97c4328f587512150`
- Observed audit-plan blob SHA: `975a007187dae9e957330c594e8348a4135abb18`
- Canonical execution state reports: `CORE-008-T04 — Implement settlement and reconciliation lifecycle`
- Two existing workflows were found: `backend-ci.yml` and `frontend-ci.yml`.
- The existing T14 resume-manifest code, schema, JSON and tests were found.
- Some proposed audit test paths are absent and require a duplicate/equivalence check before creation.
- The audit plan's recorded HEAD is older than the observed branch HEAD.
- A recent backend CI success was found for SHA `dfc967588dcbe4cb29373198f86a37c82833ebb0` (verify the exact SHA against live Actions data before citing it in any formal report). That success is not proof that the currently observed HEAD passed.
- `REOS_CONTROL_CENTER/reos_state.json` contains older metadata than `data/state.json`. Trace references before deciding whether it is a compatibility artifact, derived snapshot, or obsolete file.

**These are historical observations, not permanent constants. Before every implementation batch, fetch the live branch HEAD, state file, exact target paths and relevant test evidence again.**

Useful repository links:

- Repository: https://github.com/prajaktaranjane80-sketch/Homio
- Canonical branch: https://github.com/prajaktaranjane80-sketch/Homio/tree/reos-development
- Canonical state: https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/data/state.json
- EntryPoint: https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py
- GPT workflow: https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/gpt-ps-git-sync.md
- ACRL audit: https://github.com/prajaktaranjane80-sketch/Homio/blob/reos-development/REOS_CONTROL_CENTER/architecture/HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json
- Actions: https://github.com/prajaktaranjane80-sketch/Homio/actions

---

## 4. Target repository structure

This is the existing structure and the intended location of work. It is not a command to recreate folders or replace all listed files.

```text
Homio/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
│
├── HOMIO PowerShell–GitHub Workflow Plan
├── HOMIO_REOS_FIX_EXECUTION_STRUCTURE
│
└── REOS_CONTROL_CENTER/
    ├── AI_AGENT_ENTRYPOINT.py
    ├── gpt-ps-git-sync.md
    ├── reos_control_center.py
    ├── manifest.json
    ├── reos_state.json
    ├── HOMIO_AUTONOMOUS_MASTER_PLAN.json
    ├── GATE_TEMPLATES.json
    ├── requirements-auth.txt
    ├── README.txt
    ├── MANIFEST.txt
    ├── REOS_NEXT_CHAT.txt
    ├── PS Output
    ├── Frontend Ps Output
    ├── Frontend update files
    ├── New chat work
    │
    ├── data/
    │   └── state.json
    │
    ├── architecture/
    │   ├── HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json
    │   ├── HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md
    │   ├── backend/
    │   │   └── plans/
    │   │       └── CORE-001 to CORE-008 Closure,
    │   │           Hardening & Architecture Integrity Active Plan
    │   ├── frontend/
    │   ├── governance/
    │   └── master/
    │
    ├── evidence/
    │   └── CORE-008/
    │       └── T04-settlement-reconciliation-ci-evidence.md
    │
    ├── tets/
    │   ├── test_l3_canonical_authority.py
    │   └── test_ai_agent_entrypoint_contract.py
    │       [PROPOSED: verify no equivalent before ADD]
    │
    ├── AUTONOMY_ENGINE/
    │   ├── core/
    │   │   ├── commission_financial/
    │   │   ├── identity_tenant/
    │   │   ├── lead_ownership/
    │   │   ├── inventory/
    │   │   ├── search_matching/
    │   │   ├── deal_transaction/
    │   │   ├── trust_fraud_governance/
    │   │   └── event_platform/
    │   │
    │   ├── continuity/
    │   │   ├── canonical_truth/
    │   │   └── acrl/
    │   │       ├── T01_Project_DNA/
    │   │       ├── T02_Architecture_Lock/
    │   │       ├── T03_State_Reconstruction/
    │   │       ├── T04_Gate_Subtask_Continuity/
    │   │       ├── T05_Dependency_Authority_Map/
    │   │       ├── T06_Checkpoint_Engine/
    │   │       ├── T07_New_Chat_Bootstrap/
    │   │       ├── T08_Context_Compression/
    │   │       ├── T09_State_Fingerprint/
    │   │       ├── T10_Drift_Detection/
    │   │       ├── T11_Recovery_Fail_Closed/
    │   │       ├── T12_Resume_Safety_Validation/
    │   │       ├── T13_Controller_Integration/
    │   │       ├── T14_Repository_Intelligence_Context/
    │   │       ├── T14_Full_Regression/
    │   │       ├── T15_AI_Operator_Autonomy/
    │   │       ├── T16_Repository_Intelligence_File_Discovery/
    │   │       ├── T17_Change_Impact_Dependency_Analysis/
    │   │       ├── T18_Safe_Execution_Authorization_Guard/
    │   │       ├── T19_Intelligent_Test_Selection_Failure_Diagnosis/
    │   │       ├── T20_Autonomous_Repair_Patch_Verification/
    │   │       ├── T21_Git_Repository_Read_Write_Coordination/
    │   │       ├── T22_Commit_Execution_Checkpoint_Coordination/
    │   │       ├── T23_Reference_Evidence_Resolution_Engine/
    │   │       ├── T24_Cross_Chat_Continuity_Recovery_Engine/
    │   │       ├── T25_Context_Token_Work_Budget_Manager/
    │   │       ├── T26_Autonomous_Execution_Loop_Controller/
    │   │       ├── T27_Dependency_Aware_Work_Scheduler/
    │   │       ├── T28_Conflict_Resolution_Reconciliation_Engine/
    │   │       ├── T29_Human_Decision_Boundary_Controller/
    │   │       ├── T30_Autonomous_Completion_Handoff_Engine/
    │   │       └── runtime_integration/
    │   │
    │   ├── security/
    │   ├── contracts/
    │   ├── runtime/
    │   └── tests/
    │
    └── Frontend/
        ├── package.json
        ├── package-lock.json
        ├── tsconfig.json
        ├── scripts/
        └── src/
            ├── app/
            ├── components/
            ├── features/
            └── lib/
```

Important details:

- `T14_Repository_Intelligence_Context` is the canonical T14 identity in the existing registry.
- `T14_Full_Regression` is retained as compatibility/support. Do not rename or delete it merely to remove the duplicate number.
- A path shown as proposed does not imply the file already exists.
- Do not copy the entire archive or generate replacements for the full tree.
- The document describes the desired work order. It does not authorize changes to the canonical state.

---

## 5. The ordered implementation plan

## Phase 0 — Fresh read-only preflight and instruction reconciliation

**Purpose:** Establish current truth before making any edits.

Required actions:

1. Fetch live `reos-development` HEAD.
2. Fetch `data/state.json` and inspect current gate, current subtask, acceptance criteria and relevant task plan.
3. Read the current EntryPoint and GPT workflow document.
4. Inspect the actual Git tree for every planned target path.
5. Identify duplicates and equivalent tests before declaring a path missing.
6. Check the last relevant Actions runs, including exact SHA, workflow and failed step.
7. Trace all references to `reos_state.json`, `PS Output`, `Frontend Ps Output` and supporting workflow-plan files.
8. Record the current baseline without changing any project state.

Each target file must be marked:

- `ADD`: exact path is absent and no equivalent implementation already exists.
- `UPDATE`: the file exists, owns the responsibility and needs a demonstrated correction.
- `VERIFY`: suspected defect needs a targeted test or code proof before deciding.
- `NO CHANGE`: existing implementation is correct for the requested responsibility.
- `BLOCKED`: cannot proceed because authorization, dependency or evidence is missing.

**Completion criteria:** Every target has a verified path, an action classification and a known owner. No project code or canonical state is mutated by this preflight.

## Phase 1 — Respect the active Control Center task

The committed canonical state currently identifies:

`CORE-008-T04 — Implement settlement and reconciliation lifecycle`

Before making workflow-sync implementation changes as a separate task, establish how the existing Control Center authorizes that cross-cutting task without overwriting or bypassing T04.

The workflow audit and file plan may be prepared now, but this document does not create execution authority. Continue the active task until the existing controller selects or authorizes another task through its prescribed process, unless the project owner formally authorizes a different compliant path.

**Do not change `state.json` to make this plan active. Do not mark any work complete from the existence of this document.**

## Phase 2 — P0 safety and continuity corrections

Audit the current versions first. Several relevant files already contain apparent corrective work, so preserve them unless tests reveal a current defect.

### 2.1 Canonical task registry and read-only proof

Existing paths:

```text
REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/runtime_integration/
├── task_registry.py
├── integration_models.py
├── operational_runtime.py
└── test_full_acrl_spine.py
```

Required checks:

- Every runtime path uses the one canonical T-layer registry.
- T14 compatibility rules are applied consistently.
- Read-only operational proof never self-authorizes or mutates canonical state.
- Missing/invalid required ACRL contracts or modules fail closed.
- Tests prove state-file bytes or content remain unchanged during read-only proof.

Do not execute unsafe legacy proof paths while their behavior remains unverified.

### 2.2 T07 checkpoint coherence

Existing/new paths:

```text
T07_New_Chat_Bootstrap/
├── new_chat_bootstrap.py                 [VERIFY / UPDATE IF NEEDED]
├── test_new_chat_bootstrap.py            [EXISTING]
├── test_fast_resume_and_stale_manifest.py [EXISTING]
└── test_checkpoint_state_coherence.py    [ADD IF STILL MISSING]
```

Required checks:

- Checkpoint gate, task and subtask match independently read canonical state.
- Stale or conflicting checkpoints block resume.
- Unknown authority must not silently produce a valid resume.
- No task is selected solely from chat memory or the checkpoint.

### 2.3 T23 evidence scope

Paths:

```text
T23_Reference_Evidence_Resolution_Engine/
├── evidence_resolver.py                 [UPDATE IF DEFECT CONFIRMED]
└── test_requested_evidence_scope.py      [ADD IF STILL MISSING]
```

Required checks:

- When specific evidence IDs are requested, selection is limited to those IDs.
- Canonical evidence requirements are enforced according to policy.
- Missing or empty selectable evidence returns a typed fail-closed outcome rather than an unhandled `IndexError`.

### 2.4 T24 authoritative continuity

Paths:

```text
T24_Cross_Chat_Continuity_Recovery_Engine/
├── continuity_coordinator.py             [UPDATE IF DEFECT CONFIRMED]
├── continuity_evidence.py                [UPDATE IF DEFECT CONFIRMED]
├── continuity_validation.py              [UPDATE IF DEFECT CONFIRMED]
├── test_authoritative_context_required.py [ADD IF STILL MISSING]
└── test_continuity_freshness.py          [ADD IF STILL MISSING]
```

Required checks:

- Request-supplied expected fingerprints and branch/commit fields are comparison inputs, not proof of those values.
- Recovery requires independently observed authoritative context.
- Stale, conflicting or unknown evidence never becomes current PASS.
- When authoritative context cannot be established, recovery returns unresolved/blocked.

**Phase completion:** All P0 items have targeted regressions and confirmed results for the tested commit.

## Phase 3 — Guarded GitHub synchronization foundations

Implement this phase in dependency order, using existing responsibilities.

### 3.1 T18 authorization

```text
T18_Safe_Execution_Authorization_Guard/
├── authorization_models.py              [UPDATE IF NEEDED]
├── authorization_validation.py           [UPDATE IF NEEDED]
└── test_authenticated_approval_binding.py [ADD IF STILL MISSING]
```

Approval evidence must bind to a trusted principal and the requested operation/scope. Do not build a second authentication or identity engine.

### 3.2 T16/T17 source and impact analysis

```text
T16_Repository_Intelligence_File_Discovery/
├── repository_intelligence.py                 [UPDATE IF NEEDED]
├── repository_discovery/classification.py      [UPDATE IF NEEDED]
└── source_intelligence/
    ├── dependency_graph.py                     [UPDATE IF NEEDED]
    ├── web_source_parser.py                    [ADD AFTER DUPLICATE CHECK]
    └── test_web_source_parser.py               [ADD AFTER DUPLICATE CHECK]

T17_Change_Impact_Dependency_Analysis/
└── impact_dependency.py                        [UPDATE IF NEEDED]
```

Required checks:

- Understand Python and the Next.js source formats used by HOMIO: TS/TSX/JS/JSX and CSS-module imports.
- Resolve the frontend's `@/*` imports using its real TypeScript configuration.
- Reuse one canonical source classifier and dependency graph.
- Trace dependencies before shared-file changes.
- Keep static source analysis separate from frontend runtime behavior.

### 3.3 T20 patch verification

```text
T20_Autonomous_Repair_Patch_Verification/
├── repair_models.py                         [UPDATE IF NEEDED]
├── patch_verification.py                    [UPDATE IF NEEDED]
└── test_non_python_verification_evidence.py [ADD IF STILL MISSING]
```

Required checks:

- Verify the exact source commit, changed paths, patch fingerprint and verification evidence.
- Include the actual command, relevant run identity and result fingerprint when applicable.
- `VERIFIED` means a patch candidate was verified; it does not mean a Git commit exists.
- T21 must revalidate the baseline and final change before reporting a remote write as successful.

### 3.4 T21 classified GitHub API recovery

Existing T21 ownership:

```text
T21_Git_Repository_Read_Write_Coordination/
├── git_authorization.py
├── git_commit.py
├── git_identity.py
├── git_lock.py
├── git_models.py
├── git_policy.py
├── git_provenance.py
├── git_push.py
├── git_read.py
├── git_registry.py
├── git_repository.py
├── git_scope.py
├── git_stage.py
├── git_transaction.py
├── git_validation.py
├── t21.contract.json
├── test_git_commit.py
├── test_git_concurrency.py
├── test_git_read.py
├── test_git_scope.py
├── test_git_security.py
├── test_git_stage.py
├── test_git_transaction.py
├── test_t21_contract.py
├── github_api_error_recovery.py       [ADD IF STILL MISSING]
└── test_github_api_error_recovery.py  [ADD IF STILL MISSING]
```

Do not create a competing T21 coordinator. Integrate error classification into the existing T21 contracts and registry after checking existing error-handling functions.

Required recovery behavior:

| Condition | Required behavior |
|---|---|
| 403 | Stop blind retries; inspect permission, repository access and API scope. |
| 404 | Check authentication, exact owner/repo/ref/path/case and encoding; do not silently switch branches. |
| 409 / stale SHA / 422 | Reread current state and reconcile; never guess a SHA or force-overwrite. |
| Rate limit | Honour server reset/retry information and use bounded retries. |
| Timeout / 5xx | Bounded retry only when safe; resolve ambiguous write outcomes by readback. |
| Successful write | Confirm branch, commit parent, exact path and saved content. |

Never bypass authorization, use unapproved alternate credentials, expose secrets in logs, or force-push around conflicts.

### 3.5 T22 commit/checkpoint coordination

Use existing T22 mechanisms to preserve commit/checkpoint order and required evidence. Do not introduce another checkpoint engine or skip required coordination.

**Phase completion:** Authorization, change verification, Git coordination, classified error handling and commit/checkpoint boundaries are covered by focused tests.

## Phase 4 — GPT and GitHub workflow alignment

Update the existing policy and instructions rather than creating a standalone runner.

### Files

```text
REOS_CONTROL_CENTER/
├── AI_AGENT_ENTRYPOINT.py                  [UPDATE]
├── gpt-ps-git-sync.md                      [UPDATE]
├── tets/
│   ├── test_l3_canonical_authority.py       [EXISTING]
│   └── test_ai_agent_entrypoint_contract.py [ADD IF STILL MISSING]
│
├── architecture/
│   ├── HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json
│   │   [RECONCILE AUDIT EVIDENCE; DO NOT CHANGE STATE AUTHORITY]
│   └── HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md
│       [THIS PLAN]
│
└── reos_control_center.py                  [VERIFY; UPDATE ONLY IF NECESSARY]

Repository root:
├── HOMIO PowerShell–GitHub Workflow Plan   [REVIEW FOR CONFLICTS]
└── HOMIO_REOS_FIX_EXECUTION_STRUCTURE      [REVIEW FOR CONFLICTS]
```

Required GPT behavior:

1. Always read current branch HEAD and canonical state before interpreting the next task.
2. Inspect the requested live paths before deciding which files to add or replace.
3. Classify each target as ADD, UPDATE, VERIFY, NO CHANGE or BLOCKED.
4. Follow the existing active task and its dependencies; do not invent a new task.
5. Use the existing guarded remote GitHub API workflow for approved writes.
6. Preserve a pre-write baseline and abort if the live branch changes unexpectedly.
7. Avoid duplicate files, modules, tests and CI workflows.
8. Read back the resulting remote file and commit before saying it was saved.
9. Report implementation, tests, task acceptance, commit, CI and canonical state transition as separate outcomes.
10. When permission or evidence is insufficient, report the blocker instead of guessing or claiming success.

The EntryPoint defines agent-facing policy; it does not execute Git writes itself.

**Do not create `HOMIO_REMOTE_WORKFLOW_SYNC.ps1` or any other standalone synchronization engine as a competing authority.**

### EntryPoint contract test

The proposed `test_ai_agent_entrypoint_contract.py` must only be added after checking that there is no equivalent test already present elsewhere.

It should verify the intended workflow boundaries: canonical repository/branch, state authority, task-selection authority, exact path and write preflight, separation between T18/T20/T21/T22, no standalone competing runner policy, and truthful reporting of readback/verification.

Prompt text alone cannot guarantee an agent will always comply. Runtime contracts, tests, scoped permissions and verified write procedures provide additional enforcement.

## Phase 5 — Backend and frontend CI synchronization

Do not create a second frontend workflow.

### Existing workflow files

```text
.github/workflows/
├── backend-ci.yml    [UPDATE EXISTING]
└── frontend-ci.yml   [VERIFY AND UPDATE ONLY IF NEEDED]
```

### Backend CI

Preserve the existing checks, dependencies and relevant tests. Then add or correct the coverage needed for:

- Python compilation of the intended backend and ACRL modules.
- Runtime integration regression tests.
- T07/T14 fast-resume and stale-manifest tests.
- T18 authorization and T21 Git/error-recovery tests.
- Relevant T23/T24/T25/T26/T29/T30 tests as those fixes land.
- The EntryPoint contract test once its exact path exists.
- Existing canonical truth, identity/tenant, commission-financial and Control Center regression checks.

Before adding a test path to a workflow, confirm the path exists on the tested commit. A workflow must not fail just because its configuration references a misspelled or missing target.

### Frontend CI

Preserve the existing workflow at `.github/workflows/frontend-ci.yml`. Verify:

- It triggers for frontend source and relevant workflow changes.
- It runs from `REOS_CONTROL_CENTER/Frontend`.
- The lockfile and dependency installation are consistent.
- `npm run verify` actually exists and runs the expected foundation, auth, design-system and feature checks.
- TypeScript, lint and production build checks are included by the canonical verification script or its explicitly required steps.
- No ACRL runtime import or live state-file access is introduced into frontend code.

### CI evidence requirements

- Test/CI results must be tied to the exact commit SHA under examination.
- A successful run on a previous SHA cannot establish PASS for a newer commit.
- A green check alone is not proof that every platform requirement is covered.
- Preserve failed-run links and the failing job/step as diagnostic evidence.
- Do not claim full ACRL PASS until the intended suite actually passes on the relevant current commit.

## Phase 6 — Complete the active CORE-008-T04 task

Do not restart already completed T01–T03 implementation.

### Existing source structure

```text
REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/
├── commission_settlement.py
├── commission_settlement_lifecycle.py
├── commission_settlement_validation.py
├── commission_settlement_integrity.py
├── commission_settlement_provenance.py
├── commission_settlement_snapshot.py
├── commission_settlement_history.py
├── commission_settlement_conflict.py
├── commission_settlement_temporal.py
├── commission_reconciliation.py
├── commission_reconciliation_validation.py
├── commission_closeout.py
├── test_core008_t04_settlement_integrity_linkage.py
└── test_core008_t04_settlement_reconciliation_lifecycle.py
```

These files already exist in the observed branch tree. Their existence does not prove that T04 is complete.

Follow the canonical CORE plan and acceptance criteria to verify:

- Authoritative commission source of truth.
- Traceable deal and ownership attribution.
- Safe fixed-precision monetary values.
- Auditable settlement, reversal and reconciliation.
- Correct approval gates for critical financial actions.
- Security and concurrency regressions.
- Existing T04 linkage and lifecycle tests plus relevant full financial-core regressions.

Use the existing settlement, reconciliation and closeout implementations. Add a new source module only if dependency/ownership analysis proves it is needed.

After the implementation:

1. Run focused tests.
2. Run required adversarial and relevant regression tests.
3. Verify the exact code commit and Actions evidence.
4. Check all required acceptance criteria.
5. Use the existing controller's prescribed state transition.
6. Read the committed state and required handoff/evidence files back from GitHub.
7. Report the next task only from the new canonical state.

## Phase 7 — Remaining ACRL stateful hardening

### T25 — budget and reservation invariants

```text
T25_Context_Token_Work_Budget_Manager/
├── budget_manager.py                  [UPDATE IF NEEDED]
├── budget_validation.py               [UPDATE IF NEEDED]
└── test_reservation_invariants.py     [ADD IF STILL MISSING]
```

Validate negative amounts, booleans where integers are required, invalid numeric inputs, over-capacity reservations, identity mismatches and atomic update failure behavior.

### T26 — execution result binding

```text
T26_Autonomous_Execution_Loop_Controller/
├── loop_models.py                     [UPDATE IF NEEDED]
├── loop_controller.py                 [UPDATE IF NEEDED]
├── loop_validation.py                 [UPDATE IF NEEDED]
└── test_upstream_result_binding.py    [ADD IF STILL MISSING]
```

Bind upstream results to request identity/fingerprint and the relevant budget reservation. Reject mismatched results and replay.

### T29 — human decision boundary

```text
T29_Human_Decision_Boundary_Controller/
├── decision_gate.py                           [UPDATE IF NEEDED]
├── decision_validation.py                    [UPDATE IF NEEDED]
├── decision_store.py                         [UPDATE IF NEEDED]
├── decision_controller.py                    [UPDATE IF NEEDED]
└── test_decision_expiry_and_nonce_replay.py  [ADD IF STILL MISSING]
```

Verify expiry, nonce/replay rejection, atomic state transitions and deterministic concurrent behavior through the existing store.

### T30 — completion handoff

```text
T30_Autonomous_Completion_Handoff_Engine/
├── completion_controller.py             [UPDATE IF NEEDED]
└── test_completion_store_replay.py       [ADD IF STILL MISSING]
```

Ensure the existing completion store/record is correctly wired into the controller lifecycle. Duplicate completion requests must be handled deterministically, and a handoff must use validated persisted completion evidence.

## Phase 8 — Fast resume and incremental audit

Use the existing T07 and T14 system.

```text
T07_New_Chat_Bootstrap/
├── new_chat_bootstrap.py
├── test_new_chat_bootstrap.py
└── test_fast_resume_and_stale_manifest.py

T14_Repository_Intelligence_Context/
├── repository_context.py
├── audit_resume_manifest.py
├── audit_resume_manifest.schema.json
├── audit_resume_manifest.json
├── test_repository_context.py
└── test_audit_resume_manifest.py
```

These paths exist in the observed repository. Audit and test them before changing anything.

Requirements:

- Read fresh live branch HEAD and canonical state before accepting the manifest.
- Validate branch, state identity, audit base, path fingerprints and evidence freshness.
- Reuse a valid manifest to avoid rescanning unchanged files.
- On changes, rescan changed files and affected dependents rather than the entire repository where safe.
- Force a fresh bootstrap when canonical state or authority mismatches.
- Do not let a manifest select the next task or authorize a write.
- Never show expired CI, research or test evidence as current PASS.
- Record meaningful scan counts/cache hits without creating another memory or research engine.

The existing manifest is currently marked `UNINITIALIZED`. Do not fabricate completed audit entries. Initialize it only from actual verified evidence through the authorized mechanism.

---

## 6. Formal completion standard

A phase is not complete because its files exist or because this plan has been saved.

For every implementation batch, record:

1. Exact phase and issue IDs addressed.
2. Exact paths classified as ADD/UPDATE/NO CHANGE.
3. Live baseline SHA before the write.
4. Exact changed paths and confirmed commit SHA.
5. Targeted regression results.
6. Relevant full-suite/CI result and URL for that exact SHA.
7. Any unverified checks or blocked dependencies.
8. Canonical state/acceptance-criterion status, read from the existing authority.
9. Next task selected by the Control Center.

If a test fails, diagnose the failing assertion or step. Do not repeat the same failed operation blindly, loosen a necessary safety check solely to get green CI, or alter canonical state to hide the failure.

## 7. Work order summary

| Sequence | Work | Required outcome |
|---:|---|---|
| 0 | Live GitHub preflight and authority reconciliation | Current state, branch, exact paths and relevant evidence are known |
| 1 | Honour the active canonical task and resolve authorization for cross-cutting work | No invented task or unauthorized state transition |
| 2 | Close/verify P0 registry, read-only proof, T07, T23 and T24 safety findings | Critical authority and continuity regressions pass |
| 3 | T18 → T16/T17 → T20 → T21 → T22 | Secure, evidence-based repository changes and error recovery |
| 4 | Align EntryPoint, GPT sync document and supporting plans | No stale or contradictory workflow instructions |
| 5 | Correct existing backend/frontend CI coverage | Path-safe and SHA-specific verification |
| 6 | Complete CORE-008-T04 according to canonical plan and criteria | Settlement/reconciliation evidence and controller transition |
| 7 | T25 → T26 → T29 → T30 hardening | Reservation, result identity, human decision and completion integrity |
| 8 | Verify T07/T14 incremental audit and resume | Safe continuation without unnecessary full scans |
| 9 | Final evidence reconciliation | Every finding has a verified result or an explicit remaining blocker |

## 8. Final boundaries

- This document is an ordered work plan, not an implementation record.
- Saving this file does not change the canonical execution state.
- Existing passing work must be preserved.
- The plan's proposed changes do not automatically authorize work outside the active Control Center task.
- No changes are considered SAVED until the exact GitHub readback confirms them.
- No work is considered complete until its required tests, acceptance criteria and state transition are confirmed.
- If findings are already fixed at the current HEAD, mark them verified and reuse that evidence instead of implementing them again.
- If repository evidence contradicts this document, stop and reconcile the difference before editing files.

**End of plan.**
