# HOMIO / REOS — B4 RESEARCH & CONTINUITY REGISTER

**Document ID:** B4-RCR-001  
**Version:** 1.1  
**Project:** HOMIO / REOS  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Canonical task:** `BACKEND-001-B4`  
**Scope:** B4 PostgreSQL Integration — Backend Only  
**Status:** ACTIVE  
**Purpose:** Persistent research memory, source references, investigation deduplication and implementation continuity.

---

# 1. PRIMARY OBJECTIVE

Prevent unnecessary repeated research, duplicate searches, repeated audits, redundant file inspections and restarting previously completed investigations across HOMIO / REOS development sessions.

This register must preserve:

1. What was searched.
2. Why it was searched.
3. Which exact files and sources were inspected.
4. Which commit and blob SHAs were used.
5. What was discovered.
6. What decisions were established.
7. What implementation was actually completed.
8. What tests and evidence confirmed the result.
9. Which investigations are reusable.
10. Which conditions would require a new investigation.
11. What work is currently in progress.
12. What the next exact implementation action is.

**MANDATORY: Every new B4 session must consult this register before starting research or implementation.**

The objective is implementation-first engineering, not repeated rediscovery.

---

# 2. THREE PRIMARY DOCUMENTS AND AUTHORITY

## 2.1 B4 Work Plan

Path:

`REOS_CONTROL_CENTER/B4 ka work plan`

Responsibilities:

- B4 implementation scope.
- Phase order.
- Acceptance criteria.
- Required source files.
- Required migrations.
- Exit conditions.
- Evidence requirements.
- Guarded completion process.

This is the single authoritative B4 execution plan.

## 2.2 HOMIO Backend Structure

Path:

`REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure`

Responsibilities:

- Unified backend architecture.
- Component and module ownership.
- API and database architecture.
- Existing implementation boundaries.
- Dependencies.
- Security and reliability requirements.

This is the backend technical master.

## 2.3 B4 Research & Continuity Register

Path:

`REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-search-reference-register.md`

Responsibilities:

- Search history.
- Research references.
- Source SHA tracking.
- Findings and decisions.
- Verified investigation reuse.
- CI failure history.
- Current working context.
- Phase progress.
- Cross-chat continuity.

This register does not replace or override the two master documents.

## 2.4 Execution-state authority

Path:

`REOS_CONTROL_CENTER/data/state.json`

`state.json` remains the sole machine-readable task, execution and gate authority.

At each new session, read the relevant task and authorization fields once. Do not conduct a complete state audit unless a specific problem requires it.

This register cannot declare a task complete or change its authorized status.

---

# 3. LAST VERIFIED REPOSITORY SNAPSHOT

Initial references observed on 25 November 2026:

| Item | Reference |
|---|---|
| Repository | `prajaktaranjane80-sketch/Homio` |
| Branch | `reos-development` |
| HEAD | `567a92ebf0120ad0689fc6b709cd454a2b413f55` |
| B4 Work Plan SHA | `84c94c82ac5b0fde7c7bdf94acca235402c465ab` |
| Backend Structure SHA | `f8d9cd456568cc6c8eaae0caf764123a7e859ba6` |
| state.json SHA | `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b` |

These values are a historical baseline, not permanent current values.

Task authority at that snapshot:

- `execution.current_task`: `BACKEND-001-B4: PostgreSQL integration`
- `execution.current_subtask`: `BACKEND-001-B4`
- `execution.status`: `CONTROL_CENTER_DRIVEN`
- `gate_plans.BACKEND-001.current_subtask`: `BACKEND-001-B4`
- `gate_plans.BACKEND-001.subtasks[4].status`: `CURRENT`

The first incomplete implementation phase has not been proven by this snapshot alone.

Determine it using the saved implementation checkpoints and the exit conditions in the B4 Work Plan.

Never assume that a new session means B4 must restart from Phase 1.

---

# 4. MANDATORY SESSION START — MINIMUM RESEARCH

Every B4 session must follow this exact sequence.

## Step 1 — Verify live branch

Read the current `reos-development` HEAD once.

Record the SHA.

Do not repeatedly fetch the branch during the same session unless a new commit or concurrent change requires it.

## Step 2 — Verify task authorization

Read `REOS_CONTROL_CENTER/data/state.json` once.

Check only:

- Current task.
- Current subtask.
- Execution status.
- Relevant B4 gate status.

Do not perform a full state or governance audit by default.

## Step 3 — Read this register

Identify:

- Last implementation checkpoint.
- Current active work.
- Existing source references.
- Verified findings.
- Existing decisions.
- Open issues.
- First incomplete B4 phase.
- Next action.

## Step 4 — Compare master SHA values

Compare the live blob SHAs of:

1. `REOS_CONTROL_CENTER/B4 ka work plan`
2. `REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure`

Rules:

- If a blob SHA is unchanged, reuse its saved reference.
- Do not reread the entire unchanged document.
- If the B4 plan changes, inspect only the changed or relevant sections.
- If Backend Structure changes, inspect only the changed or relevant architecture sections.
- Do not reread both documents when only one changed.

## Step 5 — Compare implementation references

Check only source paths relevant to the current B4 phase.

A new branch HEAD does not automatically invalidate every previous research record.

A source finding is reusable when its relevant source blob SHA and technical conditions remain unchanged.

## Step 6 — Continue

Identify the first incomplete phase and perform its exact next implementation action.

Do not start another broad audit.

---

# 5. PRE-SEARCH GATE — REQUIRED BEFORE EVERY NEW INVESTIGATION

Before searching anything, the assistant must answer these questions internally and record meaningful investigations in this register.

**A. What exact question am I trying to answer?**

**B. Why is this information required for the current B4 implementation phase?**

**C. Has the same question already been investigated?**

**D. Is the source path already recorded?**

**E. Is the existing source blob SHA unchanged?**

**F. Is there already a verified finding or decision?**

**G. What specific new evidence justifies another search?**

Decision:

- Existing verified answer + unchanged relevant source = REUSE.
- Source changed = TARGETED RECHECK.
- New failure = TARGETED INVESTIGATION.
- No actual implementation need = DO NOT SEARCH.
- Missing evidence = SEARCH ONLY THE REQUIRED SCOPE.

**A search must not be performed simply because a new chat has started.**

---

# 6. SEARCH CATEGORIES AND RESEARCH BOUNDARIES

Every meaningful search must be classified.

| Search category | Scope | Default rule |
|---|---|---|
| Repository search | File and folder discovery | Search exact missing paths only |
| Code search | Functions and implementations | Search only current owner and dependency |
| Schema search | Tables, columns and relations | Reuse verified schema references |
| Migration search | Ordering, checksums and history | Reuse migration manifest and recorded results |
| Dependency search | Module and package dependencies | Recheck only on relevant dependency changes |
| Test search | Unit, integration and contract tests | Inspect only current acceptance criterion |
| CI search | Workflow runs and failure logs | Inspect the relevant run and failing step |
| Git history search | Commit and change history | Inspect only relevant changed commits |
| Security search | Tenant, permissions and access boundaries | Use only when current phase requires it |
| Governance check | Task state and transition authorization | Brief task gate check only |
| ACRL continuity | Recovery and development continuity | Consult only when actual continuity evidence is needed |

Full repository scans, repeated architecture reviews, old chat history searches and full ACRL audits are not default session activities.

---

# 7. SEARCH DEDUPLICATION KEY

Each investigation must have a reusable identity.

Use this logical key:

`Research Question + Search Scope + Acceptance Criterion + Relevant Source Paths + Relevant Source Blob SHAs`

For CI failures, use:

`Workflow + Job + Step + Error Signature + Tested Commit SHA + Relevant Source Blob SHAs`

Before repeating an investigation, compare its key with the saved register.

If the same key is already VERIFIED and no invalidation condition exists:

**Do not perform the search again. Reuse the saved result.**

A changed unrelated file must not invalidate an investigation whose relevant dependencies remain unchanged.

A new run ID alone does not prove that the root cause needs to be investigated again.

---

# 8. PERSISTENT SOURCE REFERENCE CACHE

Every meaningful source inspection must have a traceable reference.

| Reference ID | Exact source path | Blob SHA | Commit SHA | Relevant section | Finding | Status |
|---|---|---|---|---|---|---|
| B4-S001 | `REOS_CONTROL_CENTER/B4 ka work plan` | `84c94c82ac5b0fde7c7bdf94acca235402c465ab` | `567a92ebf0120ad0689fc6b709cd454a2b413f55` | Part N, Part R | Authoritative B4 execution phases and continuity rules | VERIFIED |
| B4-S002 | `REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure` | `f8d9cd456568cc6c8eaae0caf764123a7e859ba6` | `567a92ebf0120ad0689fc6b709cd454a2b413f55` | Backend architecture | Unified backend ownership and architecture | VERIFIED |
| B4-S003 | `REOS_CONTROL_CENTER/data/state.json` | `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b` | `567a92ebf0120ad0689fc6b709cd454a2b413f55` | Execution and B4 gate | B4 was CURRENT at recorded snapshot | SNAPSHOT |

For every newly inspected source, record:

- Unique reference ID.
- Exact repository path.
- Repository URL, when useful.
- Blob SHA.
- Commit SHA.
- Relevant line range or section.
- Purpose of inspection.
- Finding.
- Reuse condition.
- Invalidation condition.

Do not copy entire files into the register.

Preserve concise findings and exact source references.

---

# 9. RESEARCH HISTORY LOG

Every meaningful investigation must be appended here.

## Mandatory record format

### B4-RXXX — Investigation title

**Date:**

**Search category:**

**Research question:**

**Why required for the current phase:**

**B4 acceptance criterion:**

**Search scope:**

**Exact search query or inspection target:**

**Sources inspected:**

| Path / URL | Commit SHA | Blob SHA | Relevant section |
|---|---|---|---|

**Finding:**

**Technical conclusion:**

**Implementation consequence:**

**Verification evidence:**

**Status:**

**Deduplication key:**

**Reuse rule:**

**Reopen only when:**

Do not mark research VERIFIED unless the conclusion is supported by actual source references and sufficient evidence.

A file being read is not a verified technical finding.

A search result is not implementation evidence.

A planned test is not a passing test.

---

# 10. TECHNICAL DECISION REGISTER

Preserve established architectural decisions.

| Decision ID | Decision | Reason | Reopen only when |
|---|---|---|---|
| B4-D001 | Upgrade the existing unified backend, not a parallel backend. | Preserve canonical architecture and owners. | Approved architecture changes. |
| B4-D002 | Reuse the existing PostgreSQL transaction and tenant-context owner. | Avoid duplicate persistence and tenant authorities. | Approved ownership changes. |
| B4-D003 | Keep historical migrations 00000001–00000004 immutable. | Preserve migration history and checksums. | Approved migration-governance action. |
| B4-D004 | New schema work must be additive and follow the B4 plan. | Preserve historical schema integrity. | Approved B4 plan changes. |
| B4-D005 | ACRL is development continuity and recovery, not production security runtime. | Preserve security boundaries. | Approved architecture changes. |
| B4-D006 | Reuse the existing guarded Control Center transition. | Avoid another state or approval engine. | Governing transition contract changes. |
| B4-D007 | Reuse verified research while relevant source SHA and conditions remain unchanged. | Prevent repeated investigation. | A documented invalidation trigger occurs. |

New decisions require actual technical evidence.

Do not create a decision merely because an option was discussed.

---

# 11. B4 PHASE TRACKER

Use the nine phases defined by Part N of the B4 Work Plan.

| Phase | Workstream | Status | Completion evidence |
|---|---|---|---|
| P1 | Shared PostgreSQL test foundation | UNKNOWN | Exact real PostgreSQL test evidence |
| P2 | Physical schema and traceability | UNKNOWN | Migration and catalog evidence |
| P3 | Audit database boundary | UNKNOWN | Tenant binding, append-only and permission tests |
| P4 | Migration integrity | UNKNOWN | Ordering, checksums, replay and concurrency evidence |
| P5 | Tenant and transaction proof | UNKNOWN | Real tenant isolation and transaction tests |
| P6 | Sessions, audit and Redis | UNKNOWN | Integration and security test evidence |
| P7 | Financial persistence | UNKNOWN | Financial precision and ledger evidence |
| P8 | Recovery and operations | UNKNOWN | Independent backup/restore evidence |
| P9 | Guarded B4 completion | UNKNOWN | Exact-SHA CI, required evidence and guarded state transition |

Allowed statuses:

- NOT_STARTED
- IN_PROGRESS
- VERIFIED
- BLOCKED
- SUPERSEDED

Do not mark a phase VERIFIED unless its actual exit conditions in the B4 Work Plan have been satisfied.

Update only the relevant phase when evidence changes.

Do not repeat completed phase research.

---

# 12. RECORDED SCHEMA-RELATED ACTIVITY TITLES

The following activity titles have been observed in the ongoing B4 work history.

They must be retained as research-continuity clues.

They are not proof of completion.

| Activity title | Current evidence status |
|---|---|
| Resolved schema scope | UNVERIFIED |
| Defined safe assertions | UNVERIFIED |
| Strengthened schema coverage, implemented catalog checks, and parsed evidence | UNVERIFIED |
| Finalized catalog coverage and planned schema checks | UNVERIFIED |
| Expanded PostgreSQL schema integrity tests and validated migration manifests | UNVERIFIED |
| Expanded Homio database integrity tests with migration schema validation | UNVERIFIED |
| Planned catalog checks and audited physical schema | UNVERIFIED |
| Strengthened PostgreSQL schema integration tests and constraint validation | UNVERIFIED |
| Reviewed schema hardening | UNVERIFIED |
| Reviewed reconstructed PostgreSQL schema integration tests | UNVERIFIED |
| Reviewed schema controls and continued verification | UNVERIFIED |

For each activity, connect the title to:

- Exact source paths.
- Commit SHA.
- Blob SHA.
- Actual implementation change.
- Tests performed.
- Final evidence.

If two titles describe the same work, link both to one investigation record rather than starting two investigations.

Never treat repeated activity titles as a reason to repeat the work.

Never infer implementation completion from a title alone.

---

# 13. CURRENT WORK OWNERSHIP AND CROSS-CHAT COLLISION CONTROL

The project may be worked on across multiple ChatGPT sessions while the user saves changes through GitHub Web Editor.

To avoid conflicting replacements, maintain one active working record.

## Active work record

**Session reference:**  
**Current B4 phase:**  
**Current objective:**  
**Starting HEAD:**  
**Target file paths:**  
**Files currently being changed:**  
**Last verified source SHA:**  
**Owner save status:**  
**Last updated checkpoint:**  
**Next action:**  
**Session status:** ACTIVE / PAUSED / CLOSED

Rules:

1. Do not propose competing replacements for a file already recorded as actively being changed in another session.
2. Before changing a target file, compare its live blob SHA.
3. If the file changed, inspect the actual new contents before preparing a replacement.
4. Do not overwrite a concurrent change using stale content.
5. The user remains the GitHub Web Editor owner and saves supplied replacements.
6. The assistant must not claim that a file was saved without remote readback.

This is an advisory coordination record, not a technical Git lock.

Only one active implementation owner should modify the same target file at a time.

---

# 14. CI FAILURE MEMORY AND ROOT-CAUSE DEDUPLICATION

For every meaningful CI failure, record:

| Field | Required information |
|---|---|
| Failure ID | Unique B4-FXXX |
| Workflow | Exact workflow name |
| Run ID | Exact GitHub Actions run |
| Tested SHA | Exact commit SHA |
| Failed job | Job name |
| Failed step | Exact step |
| Error signature | Normalized error |
| Relevant file | Exact source path |
| Blob SHA | Exact source version |
| Root cause | Proven technical cause |
| Fix | Actual change |
| Verification | Exact passing test/run |
| Status | OPEN / FIXED / VERIFIED / SUPERSEDED |

Rules:

- Same error signature and same relevant source SHA: reuse the existing diagnosis.
- New run ID with unchanged source and same failure: do not automatically restart the investigation.
- New source SHA: inspect only the relevant changed dependency.
- New failure signature: perform a targeted investigation.
- Skipped guarded transitions are not automatically test failures.
- A passing infrastructure step is not proof of B4 completion.

Never declare a root cause fixed without evidence.

---

# 15. INVALIDATION AND STALENESS RULES

A previous research reference becomes STALE only when its relevant evidence is invalidated.

Examples:

| Change | Required action |
|---|---|
| Unrelated source file changed | Keep existing finding |
| Relevant source blob SHA changed | Recheck only affected finding |
| B4 Work Plan blob SHA changed | Inspect changed/relevant plan sections |
| Backend Structure blob SHA changed | Inspect changed/relevant architecture |
| New CI failure appears | Investigate that failure only |
| Existing failure repeats with same relevant source SHA | Reuse existing diagnosis |
| Current task changes in state.json | Follow the new authorized task |
| New acceptance criterion is introduced | Investigate the new requirement |
| Previously passing test regresses | Inspect the changed dependency and failure |

Do not mark every previous reference STALE merely because HEAD changes.

Preserve old evidence and decisions for traceability.

Use SUPERSEDED when a newer authoritative decision replaces an older one.

---

# 16. IMPLEMENTATION CHECKPOINT

Every meaningful implementation bundle must create or update a checkpoint.

### B4-CP-XXX

**Date:**

**Starting HEAD:**

**Ending HEAD:**

**Authorized task:**

**B4 phase:**

**Objective:**

**Research references reused:**

**New research performed and why:**

**Files inspected:**

| Path | Blob SHA | Purpose |
|---|---|---|

**Files changed:**

| Path | New blob SHA | Change |
|---|---|---|

**Existing owners reused:**

**Files explicitly left unchanged:**

**Root cause resolved:**

**Tests executed:**

- Passed:
- Failed:
- Skipped:

**CI workflow:**

**Run ID and URL:**

**Tested commit SHA:**

**Remote readback:**

**Remaining blockers:**

**Next exact action:**

**Investigations that must not be repeated:**

Only record actual completed work.

Never record intended work as completed work.

---

# 17. MANDATORY UPDATE POLICY

Update this register whenever:

1. A new meaningful investigation is completed.
2. A source reference is established.
3. A technical decision is proven.
4. A finding becomes stale or superseded.
5. A root cause is fixed.
6. A B4 phase satisfies its exit criteria.
7. A new exact-SHA CI result is verified.
8. The active work ownership changes.
9. A new implementation checkpoint is completed.

Preserve previous records.

Do not erase history to make the register appear cleaner.

The register should be updated after a meaningful implementation checkpoint, not after every trivial read or tool call.

Use complete-file replacements when supplying revisions to the repository owner.

The assistant must never claim the register has been saved or updated until the owner has saved it and exact live GitHub readback has confirmed it.

---

# 18. PROHIBITED REPEATED WORK

Unless an invalidation trigger exists, do not:

- Restart a full B4 audit.
- Repeat a full repository scan.
- Repeat an unchanged schema discovery.
- Repeat an unchanged physical schema audit.
- Rebuild an already verified source inventory.
- Repeat a migration inventory without a relevant change.
- Repeat an architecture review when master SHA is unchanged.
- Repeat a dependency scan without a relevant dependency change.
- Reconstruct old chat history without a specific missing reference.
- Repeat an unchanged ACRL audit.
- Repeat an unchanged CI root-cause investigation.
- Replan an already established assertion.
- Expand tests without a specific uncovered acceptance criterion.
- Create duplicate backend owners.
- Create a second task-state authority.
- Create a second approval or transition engine.
- Create another research or continuity framework.
- Modify frontend UI during backend-only B4 work.
- Claim success without exact source and test evidence.

**When saved research is sufficient, reuse it. When implementation is possible, implement. When a new failure appears, investigate only its root cause.**

---

# 19. REQUIRED SESSION EXECUTION ORDER

Every future B4 session must follow:

1. Read this register.
2. Verify live branch HEAD once.
3. Read the current task gate in state.json once.
4. Compare the two master document blob SHAs.
5. Check active work ownership.
6. Reuse unchanged verified source references.
7. Identify the first incomplete B4 phase.
8. Perform the pre-search gate.
9. Inspect only the exact files needed.
10. Implement the actual root-cause solution.
11. Execute relevant tests.
12. Verify exact commit SHA, blob SHAs and Actions evidence.
13. Update the implementation checkpoint and register.

Do not follow:

`START OVER → FULL RESEARCH → FULL AUDIT → REPEAT SCHEMA SEARCH → REPEAT PLANNING → REPEAT REVIEW`

Follow:

`REFERENCE → VERIFY → REUSE → IMPLEMENT → TEST → FIX → VERIFY → RECORD`

---

# 20. FINAL ENGINEERING RULE

HOMIO / REOS B4 has:

- One authoritative B4 Work Plan.
- One authoritative Backend Structure master.
- One persistent B4 Research & Continuity Register.
- One existing unified backend implementation.
- One existing state and guarded completion authority.

The register exists to preserve engineering knowledge and prevent repeated research.

It must never become another architecture, task manager, approval engine or runtime system.

**Search only when required. Search only the necessary scope. Save the exact reference. Reuse it until invalidated. Continue from the first incomplete implementation phase.**

**B4 objective: Complete the approved PostgreSQL integration with secure tenant isolation, deterministic migrations, durable persistence, recovery proof and guarded Control Center completion.**
