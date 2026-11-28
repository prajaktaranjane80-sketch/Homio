# HOMIO / REOS — PROJECT KNOWLEDGE, RESEARCH REUSE, CODE COMPLIANCE & AUTOMATIC CONTINUITY
## Consolidated Engineering Implementation Contract — Version 2.0

**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical source branch:** `reos-development`  
**Generated reference branch:** `reos-project-reference`  
**Design authority:** `REOS_CONTROL_CENTER/Project Foundation work`  
**Execution authority:** `REOS_CONTROL_CENTER/data/state.json`

> This document is an implementation and handoff guide. It is NOT a third project-reference authority. HOMIO / REOS will have exactly two primary project-reference files.

---

# PART 1 — THE NON-NEGOTIABLE OBJECTIVE

The system exists to eliminate unnecessary repeated engineering work.

It must prevent the assistant from repeatedly:

- Researching the same repository architecture.
- Searching for the same source files.
- Reading unchanged modules again.
- Reconstructing the same dependency relationships.
- Rechecking code that has already passed the same valid verification.
- Investigating a previously diagnosed CI error again without new evidence.
- Rebuilding the same project context in every new chat.
- Asking the user for the same repository links, paths or previous task information.
- Repeating a full project audit when only one file changed.
- Repeating work that already has valid source and verification evidence.

The objective is not to eliminate necessary engineering checks.

The objective is to reuse verified knowledge and perform only the checks that actual changes require.

**Target operating principle:**

Research once → verify → preserve evidence → detect changes → reuse unchanged findings → reverify only affected scope.

## Success criteria

A new chat must be able to understand the verified current project position from the two reference files and the minimum live authority check.

It must not need the user to provide old repository URLs, old Actions links, previous file paths or previous research summaries when the connected GitHub repository is accessible.

It must not need to read all 2,390 source files to understand where the current task stands.

It must identify the exact files that need reading for the next task.

It must know which earlier findings and tests are still valid.

It must know whether assistant-supplied coding was saved and whether the saved version was actually verified.

It must never present old verification as current after a relevant source change.

---

# PART 2 — TWO PRIMARY REFERENCE FILES

## REFERENCE 01: Stable operating and authority reference

**Exact path:**

`REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`

### Purpose

The EntryPoint defines how an AI engineering session operates HOMIO / REOS.

It owns:

1. Canonical repository identity.
2. Canonical branch identity.
3. Authority order.
4. Existing file and module ownership.
5. ACRL owner routing.
6. Startup instructions.
7. New-chat repository discovery instructions.
8. Atlas retrieval and validation instructions.
9. Research reuse policy.
10. Coding compliance requirements.
11. Evidence freshness rules.
12. Change-impact and selective-reverification rules.
13. Security restrictions.
14. Full-file replacement and readback requirements.
15. Context-loss recovery instructions.
16. Human approval boundaries.
17. Prohibition on duplicate engines.
18. Prohibition on unauthorized state transitions.

### Stable-file rule

The EntryPoint is not a copy of the complete repository index.

It must not be regenerated on every source push.

It should change only when:

- Stable project identity changes.
- Permanent authority rules change.
- Existing owner responsibilities change.
- Startup integration changes.
- The reference architecture itself changes.

Dynamic file paths, SHAs, code relationships, test results, workflow results and project knowledge belong in the generated Atlas.

The Atlas must contain the current EntryPoint blob SHA, so any actual EntryPoint change automatically invalidates only the affected policy and startup findings.

---

## REFERENCE 02: Automatically generated technical and knowledge reference

**Exact path on `reos-project-reference`:**

`REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json`

### Purpose

The Atlas contains the changing technical position of the entire tracked repository.

It must include:

1. Complete repository inventory.
2. Exact file paths and Git blob SHAs.
3. File modes and classification.
4. Source-code symbol information.
5. Existing module ownership.
6. Architecture-document relationships.
7. Requirement-to-code-to-test mapping.
8. API, schema and contract references.
9. Dependency graph.
10. Test-to-source mapping.
11. GitHub workflow relationships.
12. Reusable workflow and composite action relationships.
13. Previous verified research.
14. Research-query fingerprints.
15. Actual coding-compliance evidence.
16. CI run identity and conclusions.
17. CI failure memory.
18. Evidence freshness.
19. Change history and affected dependencies.
20. Internal file-link synchronization.
21. External dependency verification metadata.
22. Current task-specific Session Pack.

The Atlas is generated from exact GitHub source snapshots.

It is never manually maintained as a second state authority.

### Important boundary

The Session Pack, research index, compliance index and failure memory are all sections inside the same Atlas JSON.

They are not separate project-reference files.

---

# PART 3 — FINAL REPOSITORY FILE STRUCTURE

```text
REPOSITORY: prajaktaranjane80-sketch/Homio
BRANCH: reos-development

REOS_CONTROL_CENTER/
│
├── AI_AGENT_ENTRYPOINT.py
│   └── PRIMARY REFERENCE 01
│       Stable rules, authority, navigation and startup
│
├── HOMIO_PROJECT_REFERENCE_ATLAS.json
│   └── PRIMARY REFERENCE 02
│       Generated only on reos-project-reference
│
├── Project Foundation work
│   └── Original design and architecture authority
│
├── data/
│   └── state.json
│       Sole execution-state and task authority
│
├── architecture/
│   └── PROJECT_REFERENCE_ATLAS_IMPLEMENTATION_PLAN.md
│       This implementation and continuity guide
│
├── contracts/
│   └── project_reference_atlas.schema.json
│       Strict Atlas schema
│
└── AUTONOMY_ENGINE/
    │
    ├── research/
    │   ├── research_cache.py
    │   ├── research_gate.py
    │   ├── research_policy.py
    │   ├── source_policy.json
    │   └── test_bridge_v5.py
    │
    └── continuity/
        └── acrl/
            │
            ├── T02_Architecture_Lock/
            │   └── Existing architecture authority and drift
            │
            ├── T07_New_Chat_Bootstrap/
            │   └── Existing startup and fast-resume owner
            │
            ├── T09_State_Fingerprint/
            │   └── Existing canonical state identity
            │
            ├── T10_Drift_Detection/
            │   └── Existing drift detection
            │
            ├── T14_Repository_Intelligence_Context/
            │   ├── audit_resume_manifest.py
            │   └── repository_context.py
            │
            ├── T16_Repository_Intelligence_File_Discovery/
            │   ├── repository_intelligence.py
            │   ├── contract_graph.py
            │   ├── source_intelligence/
            │   │   └── dependency_graph.py
            │   ├── symbol_intelligence/
            │   │   └── snapshot.py
            │   └── project_reference_atlas/
            │       ├── project_reference_atlas.py
            │       ├── update_entrypoint_atlas_reference.py
            │       └── test_project_reference_atlas.py
            │
            ├── T17_Change_Impact_Dependency_Analysis/
            │   └── change_impact_analysis.py
            │
            ├── T19_Intelligent_Test_Selection_Failure_Diagnosis/
            │   ├── failure_diagnosis.py
            │   └── selection_engine.py
            │
            ├── T20_Autonomous_Repair_Patch_Verification/
            │   ├── patch_verification.py
            │   └── existing repair and authorization owners
            │
            ├── T21_Git_Repository_Read_Write_Coordination/
            │   └── Existing Git scope and transaction ownership
            │
            ├── T23_Reference_Evidence_Resolution_Engine/
            │   └── Existing evidence identity and resolution owners
            │
            ├── T24_Cross_Chat_Continuity_Recovery_Engine/
            │   ├── continuity_coordinator.py
            │   ├── continuity_snapshot.py
            │   └── existing recovery and validation owners
            │
            ├── T25_Context_Token_Work_Budget_Manager/
            │   └── Existing context-budget ownership
            │
            ├── T28_Conflict_Resolution_Reconciliation_Engine/
            │   └── Existing authority conflict ownership
            │
            ├── T29_Human_Decision_Boundary_Controller/
            │   └── Existing human approval boundary
            │
            └── T30_Autonomous_Completion_Handoff_Engine/
                ├── handoff_builder.py
                └── existing completion and proof owners

.github/
└── workflows/
    └── homio-project-reference-atlas.yml
        └── Atlas generation, validation and publication
```

No new standalone scanner, query engine, resume database, dependency engine, failure engine, evidence registry or task manager is permitted.

---

# PART 4 — EXISTING FIVE ATLAS IMPLEMENTATION FILES

## File 1 — Atlas generator

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/project_reference_atlas.py`

Responsibilities:

- Exact Git tree inventory.
- File path and blob SHA index.
- Classification and ownership.
- Symbol and module map.
- Documentation references.
- Architecture and requirement index.
- Dependency graph.
- Workflow graph.
- Test relationship map.
- Previous Atlas comparison.
- Changed path detection.
- Research and knowledge index assembly.
- Compliance traceability.
- Failure memory.
- Evidence freshness.
- Session Pack generation.
- Schema and integrity validation.

Current known defect:

`_load_entrypoint_literals(root)` attempts all-or-nothing literal evaluation of the EntryPoint registries.

A single dynamic entry can erase otherwise valid registry entries.

Fix:

- Safe per-entry AST parsing.
- Safe known constant resolution.
- Safe literal dictionary lookup resolution.
- Explicit unresolved expressions.
- Never execute arbitrary repository code.
- Preserve independently resolved entries.

The generator must use T16's existing `symbol_intelligence` and `contract_graph` owners rather than build a separate symbol or contract engine.

## File 2 — EntryPoint updater

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/update_entrypoint_atlas_reference.py`

Responsibilities:

- Preserve the existing EntryPoint.
- Add exactly one managed Atlas contract.
- Validate startup position.
- Enforce idempotency.
- Prevent duplicate owner routing.
- Generate complete replacement content.
- Validate required project identity and reference constants.
- Keep user approval and GitHub Web Editor workflow intact.

It must not rewrite stable policy on every commit.

## File 3 — Regression tests

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/test_project_reference_atlas.py`

Responsibilities:

- Generator correctness.
- Registry extraction.
- File inventory.
- Symbol coverage.
- Dependency mapping.
- Requirement-to-code-to-test links.
- Research reuse.
- Evidence freshness.
- Code compliance.
- Link synchronization.
- Failure memory.
- Session Pack.
- Exact-SHA protection.
- EntryPoint preservation.
- Workflow event coverage.
- Security and size limits.

Use existing unittest conventions in this file.

## File 4 — Atlas schema

`REOS_CONTROL_CENTER/contracts/project_reference_atlas.schema.json`

Responsibilities:

- Validate every Atlas section.
- Validate every required identity.
- Validate exact SHA fields.
- Validate inventory counts.
- Validate link targets.
- Validate requirement relationships.
- Validate code-compliance outcomes.
- Validate research and CI evidence.
- Validate Session Pack.
- Validate freshness states.
- Validate provenance and integrity.

Incompatible compact-format and data-contract changes must increment the schema version.

## File 5 — Automatic GitHub workflow

`.github/workflows/homio-project-reference-atlas.yml`

Responsibilities:

- Source-change triggers.
- Pull-request validation.
- Exact source snapshot.
- Previous Atlas retrieval.
- Incremental change analysis.
- Atlas generation.
- Session Pack generation.
- Schema/integrity checks.
- Source race protection.
- Serialized reference publication.
- Final reference readback.
- Compact evidence artifacts.

Validation and publishing permissions must remain separated.

---

# PART 5 — THE ADDITIONAL GAP THAT MUST BE FIXED: RESEARCH REUSE

Existing research-related files:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/research_cache.py`

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/research_gate.py`

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/research_policy.py`

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/source_policy.json`

### Current observed limitation

The current ResearchCache is a small JSON key/value cache.

It does not itself enforce:

- Source commit SHA.
- Source file blob SHA.
- Query fingerprint.
- Evidence provenance.
- Expiration.
- Freshness.
- Integrity.
- Atomic writes.
- Corruption recovery.

It returns an empty dictionary on malformed JSON instead of distinguishing missing cache from corrupted cache.

ResearchGate uses a verified boolean, source count and topics, but it does not independently prove evidence freshness.

ResearchPolicy already identifies domains such as software versions, API behavior, cloud services, pricing, security guidance and standards as current-fact domains.

### Required behavior

Reuse the existing research components. Do not create a new independent research cache engine.

Before any research result can be reused:

1. Identify the original query.
2. Compute a normalized query fingerprint.
3. Identify the repository, topic and research scope.
4. Identify source URLs or repository paths.
5. Verify source identity.
6. Verify evidence provenance.
7. Verify the source's currentness.
8. Verify that the result is still relevant.
9. Reuse the finding only when all conditions pass.

### Research record stored inside Atlas

Each durable research finding must contain:

- Stable finding ID.
- Normalized query fingerprint.
- Research topic and category.
- Relevant project requirement.
- Source names and URLs.
- Repository file paths and blob SHAs, where applicable.
- Source authority tier.
- Short verified conclusion.
- Material decision supported.
- Verification method.
- Date checked.
- Publication/modified date when available.
- Expiry or freshness policy.
- Invalidation reason.
- Current status.

Do not store complete search-result pages, full browser logs or unnecessary copied text.

### Search reuse rules

**Repository research:**

If the query, indexed repository state and relevant source SHAs are unchanged, reuse the previously recorded result. Do not repeat broad GitHub code searches.

**External web research:**

If a trusted source and its relevant facts remain valid within the applicable freshness window, reuse its evidence.

If the fact is time-sensitive, expired, changed or safety-critical, perform the targeted current lookup required by `research_policy.py`.

Do not automatically repeat a web search just because a new chat started.

### Important persistence boundary

The Atlas is the durable repository-side reference for saved project findings.

The existing local ResearchCache must not become a second canonical knowledge database.

If its call sites use it, harden or adapt it to validate Atlas/T14 evidence. If it is not used, do not introduce a new runtime dependency simply to keep it alive.

### Chat research capture

A GitHub workflow cannot automatically see an unrecorded search or private reasoning from a ChatGPT conversation.

Therefore:

- Research that materially changes an architecture or coding decision must be captured in the relevant existing authoritative project document or existing evidence process.
- The Atlas then indexes its exact path, SHA and source evidence.
- Do not create a separate research-reference document.
- Search history is not the authority; the verified finding and its provenance are.
- Never claim that a conversational search was durably saved unless its evidence is actually present in the project or Atlas.

This is a platform boundary, not something GitHub Actions can secretly solve.

---

# PART 6 — NO REPEATED CODE RESEARCH OR COMPLIANCE AUDITS

This is mandatory.

The Atlas must contain a `compliance_traceability` section.

Required relationship:

```text
Approved architecture requirement
           |
           v
Authoritative task acceptance criterion
           |
           v
Actual saved source file
           |
           v
Relevant tests and contracts
           |
           v
Exact verification/CI evidence
           |
           v
Current compliance result
```

Each compliance record must identify:

- Requirement ID.
- Authoritative document and section.
- Exact source document blob SHA.
- Relevant implementation paths.
- Implementation blob SHAs.
- Relevant test paths.
- Test blob SHAs.
- Relevant workflow and action SHAs.
- Dependency fingerprint.
- Exact verification command or method.
- CI workflow/run/attempt or T20 evidence ID.
- Result and verified date.
- Invalidation reason.

### Allowed compliance statuses

- `VERIFIED`
- `FAIL`
- `PARTIAL`
- `UNKNOWN`
- `STALE`
- `NOT_APPLICABLE`

`VERIFIED` requires actual requirement-to-implementation-to-test traceability and successful matching evidence.

File presence, code similarity or an assistant statement alone are not proof.

### Assistant-supplied coding record

When a complete file is delivered and saved:

1. Preserve the intended target path.
2. Verify GitHub readback.
3. Capture the exact saved commit and file blob SHA.
4. Use T20's repair verification owner and relevant tests.
5. Verify against the authoritative requirement.
6. Record the verification result and evidence identities in the Atlas.
7. Reuse the result while all relevant SHA inputs remain unchanged.

If a source file has not changed and its evidence remains valid, do not repeat the same full compliance audit in a new chat.

If a source file changes, invalidate only the affected requirement/test evidence.

The saved repository version is canonical. The assistant must not assume that a delivered replacement was saved exactly as provided.

---

# PART 7 — SYMBOL, MODULE AND CONTRACT KNOWLEDGE

The previous Atlas inventory was not enough to eliminate repeated code reading.

Use existing T16 owners:

- `T16_Repository_Intelligence_File_Discovery/contract_graph.py`
- `T16_Repository_Intelligence_File_Discovery/source_intelligence/dependency_graph.py`
- `T16_Repository_Intelligence_File_Discovery/symbol_intelligence/snapshot.py`
- Existing T16 source parser and web source parser.

For supported source types, index:

- Module path.
- Public classes and functions.
- Function and method signatures where statically extractable.
- Imports.
- Local dependencies.
- Contract identifiers.
- API route references where supported.
- Schema references.
- Test references.
- File ownership.
- Source SHA.
- Parser confidence.

The purpose is to let a new chat locate the implementation and understand its interface without reading every file.

Do not copy entire source files into the Atlas.

For unsupported file formats, report the limitation honestly.

A complete file inventory is not the same as complete semantic understanding.

---

# PART 8 — CHANGE IMPACT AND SELECTIVE REVERIFICATION

Reuse:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py`

Existing interface:

`ChangeImpactAnalyzer(repository_root).analyze(changed_paths)`

The Atlas must detect:

- Added files.
- Deleted files.
- Modified files.
- Renamed files.
- File-mode changes.
- Import and dependency changes.
- Package and lockfile changes.
- Architecture and document changes.
- State and work-plan changes.
- Test changes.
- Workflow and reusable-action changes.
- EntryPoint changes.
- Ownership changes.

For each actual change:

1. Identify old and new blob SHA.
2. Identify direct dependents.
3. Use T17 for impact closure.
4. Identify affected requirements.
5. Identify affected tests.
6. Identify affected CI workflows.
7. Identify stale evidence.
8. Preserve unaffected findings.
9. Determine the minimum required reverification scope.
10. Update Atlas and Session Pack.

An unrelated source change must not cause a full project audit.

If the dependency graph is incomplete for a changed file, mark the impact as partial and perform a targeted dependency discovery. Do not assume no impact.

---

# PART 9 — LINK AND REFERENCE SYNCHRONIZATION

The Atlas must automatically update relationships when repository paths or identities change.

Handle:

- New files.
- Deleted files.
- Renamed files.
- Moved folders.
- Updated architecture documents.
- Updated work plans.
- Updated test paths.
- Changed imports.
- Changed workflows.
- Changed reusable actions.
- Changed source branches.
- Changed owner mappings.
- Changed dependency references.

Each relationship must contain:

- Canonical repository-relative path or external URL.
- Relationship type.
- Discovery source.
- Target identity.
- Target SHA where tracked.
- Resolution status.
- Confidence.
- Old path when a rename is established.

Rules:

- Do not guess replacements for deleted files.
- Do not preserve deleted targets as current links.
- Preserve historical relationships only as historical.
- Report unresolved links explicitly.
- Never silently redirect a broken reference.

External URLs must record their last verified time and source status where available.

---

# PART 10 — CI FAILURE MEMORY

Reuse T19:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis/failure_diagnosis.py`

Also reuse its existing test-selection owner:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis/selection_engine.py`

Each CI incident must record:

- Workflow path and identity.
- Workflow blob SHA.
- Run ID and attempt.
- Trigger event.
- Source branch and head SHA.
- Job and failed step.
- Error category.
- Failure signature.
- Relevant file SHAs.
- Relevant dependency fingerprint.
- Relevant test selector.
- Evidence URL.
- Diagnosis status.
- Verified root cause, if established.
- Repair commit.
- Relevant tests after repair.
- Exact post-fix CI evidence.

Distinguish:

- Backend code regression.
- Frontend regression.
- Workflow configuration failure.
- Reusable action failure.
- Dependency/build failure.
- Runner/environment failure.
- Control Center governance failure.
- Atlas generation/publication failure.

### Same-failure reuse

If the same failure signature and relevant source identities reappear:

- Reuse the previous diagnosis as historical evidence.
- Compare current run and current inputs.
- Do not repeat the entire investigation if inputs are unchanged.
- Do not blindly apply the old repair.

A repair is verified only after the required post-fix tests and exact-source CI pass.

---

# PART 11 — CROSS-CHAT CONTINUITY

This is a major requirement, not an optional enhancement.

Reuse existing:

### T07

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T07_New_Chat_Bootstrap/new_chat_bootstrap.py`

Purpose: construct and validate a compact restart payload and fast-resume decision.

### T24

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T24_Cross_Chat_Continuity_Recovery_Engine/`

Important existing files:

- `continuity_coordinator.py`
- `continuity_snapshot.py`
- `continuity_evidence.py`
- `continuity_recovery.py`
- `continuity_store.py`

Purpose: validate cross-chat continuity evidence and recovery.

### T30

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T30_Autonomous_Completion_Handoff_Engine/`

Reuse existing handoff and completion proof owners.

### T25

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T25_Context_Token_Work_Budget_Manager/`

Use existing context-budget ownership to avoid loading the complete Atlas.

### Persistence boundary

T23, T24 and T30 contain in-memory stores. Their in-memory objects must not be treated as durable cross-chat persistence.

T07 and T24 validate and reconstruct continuity.

The durable saved project reference is the Atlas on `reos-project-reference`.

T14's validated resume cache/artifacts can supplement it but must not be the only long-term source.

### Required Session Pack

The Session Pack must exist inside the Atlas and contain:

1. Current repository and branch.
2. Exact source HEAD and tree SHA.
3. EntryPoint blob SHA.
4. Live `state.json` blob SHA.
5. Current gate, task and subtask.
6. Current task phase or position, when authoritatively available.
7. Current acceptance criteria.
8. Exact work-plan paths and SHAs.
9. Relevant architecture references.
10. Relevant code owners.
11. Verified completed work.
12. Unresolved work.
13. Last verified CI results.
14. Known failure root causes.
15. Stale evidence and invalidation reason.
16. Changed files.
17. Affected dependencies.
18. Exact files required for the next work unit.
19. Required test and CI selectors.
20. Next permitted step.
21. Unresolved authority conflicts.
22. Explicit missing external verification.

The Session Pack must never choose or authorize a new task.

It derives task and subtask from live Control Center authority.

### New-chat bootstrap

The assistant must use fixed repository identity from EntryPoint and the connected GitHub app.

It must not ask the user to resend repository URLs, old Actions links or previous file names when repository access is available.

Startup order:

1. Read EntryPoint.
2. Discover the connected `prajaktaranjane80-sketch/Homio` repository.
3. Fetch current `reos-development` HEAD.
4. Read live `state.json`.
5. Fetch Atlas from `reos-project-reference`.
6. Verify Atlas source HEAD, tree SHA and state SHA.
7. Validate Session Pack.
8. Read only the current task's exact relevant files.
9. Continue from the last verified incomplete unit.

If the GitHub connection is unavailable, the assistant must say that repository access is unavailable and request reconnection. It must not ask the user for a large collection of old links or repeat the project research.

A repository file cannot itself force the ChatGPT platform to expose a disconnected GitHub account. That is an external platform dependency.

---

# PART 12 — AUTHORITY CONFLICTS AND ARCHITECTURE DRIFT

Reuse:

- T02 Architecture Lock.
- T09 State Fingerprint.
- T10 Drift Detection.
- T28 Conflict Resolution/Reconciliation.
- Existing T05 dependency authority map.
- Existing T21 Git coordination.

Decision authority:

| Information | Authority |
|---|---|
| Current task and status | Live `state.json` |
| Actual source implementation | Live GitHub branch |
| Acceptance criteria | Authoritative task plan and state contract |
| Approved architecture | Designated architecture master |
| Stable operating rules | EntryPoint |
| Existing module ownership | Existing owner contracts and code |
| Verification results | Exact CI/T20 evidence |
| Repository index | Generated Atlas |
| Previous findings | Atlas, only while fresh |
| Cross-chat continuity | T07/T24 validated Session Pack |

When authoritative sources conflict:

1. Detect the conflict.
2. Identify exact paths, sections and SHAs.
3. Identify the authority type of each source.
4. Use the correct existing owner to reconcile.
5. Preserve the resolution evidence.
6. Stop when the controlling authority cannot be determined.

Never guess the answer.

Atlas is not permitted to override `state.json`, task acceptance criteria or architecture approval.

---

# PART 13 — GITHUB WORKFLOW AND AUTOMATIC EVENT COVERAGE

Current live source snapshot contained 26 GitHub workflow files.

Their structure includes top-level workflow entry points and reusable workflow components.

The current major top-level producers include:

- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/backend-b4-reopen.yml`
- `.github/workflows/homio-project-reference-atlas.yml`

The backend workflow also invokes guarded reusable workflows, including AI-001, BACKEND-001 and CORE-008 transitions.

### Required event audit

Do not simply subscribe to all 26 workflow names.

Map:

- Top-level workflow.
- `workflow_call` reusable workflow.
- Actual caller.
- Jobs with source write permissions.
- Actual source-branch writes.
- Exact completion event that follows the write.

The current Atlas workflow already listens for:

- Push to `reos-development`.
- Pull request validation.
- Backend CI completion.
- Frontend CI completion.
- Guarded B4 recovery reopen completion.
- Manual dispatch.
- Repository dispatch.
- Scheduled refresh.

Verify these producer relationships after every workflow graph change.

### Bot-write requirement

Normal GitHub `GITHUB_TOKEN` commits may not trigger another `push` workflow.

Therefore, source-writing automation must have a verified completion-trigger path or an explicit refresh dispatch.

When a backend or guarded transition workflow writes `state.json`, the Atlas refresh must read the latest committed branch HEAD after that workflow finishes.

### Concurrency

Use one global publisher group:

`homio-project-reference-atlas-${{ github.repository }}`

`cancel-in-progress: false`

Separate event-specific publisher groups are not permitted.

### Exact-source protection

- Generate from one exact source snapshot.
- Verify the source SHA before generation.
- Verify it again before publication.
- Verify it after publication.
- Reject stale output.
- Publish only to `reos-project-reference`.
- Never update `reos-development` as an Atlas side effect.
- Never publish pull-request head content.
- Preserve reference branch history.
- Never claim an older Atlas is current for a newer source SHA.

---

# PART 14 — EXTERNAL DEPENDENCY CHANGES

Some changes are not visible in GitHub source files.

Examples:

- GitHub secrets.
- Repository permissions.
- Branch protection.
- Environment approvals.
- External API provider changes.
- Production PostgreSQL schema.
- Redis runtime settings.
- Deployment configuration.
- External credentials and runtime state.

The Atlas must include an `external_dependencies` section containing:

- Dependency identity.
- Responsible owner.
- Verification method.
- Last verified time.
- Evidence reference.
- Current status.
- Applicable freshness interval.
- Whether the current task actually requires it.

Do not store secret values.

Do not claim automatic verification when no verification source exists.

A scheduled check or task-specific check may update external verification metadata, but a Git push cannot detect every external setting change.

---

# PART 15 — COMPACT ATLAS AND READER LIMIT

The current generated Atlas is approximately 5.1 MB.

The connected GitHub file-reading path returned an empty result even when a limited line range was requested.

This means the existing Atlas is not practically readable through the current startup path.

### Required target

Keep the complete Atlas at or below 1 MiB uncompressed.

This limit must be enforced in code and in tests.

Do not solve the size problem by deleting tracked-file entries or hiding missing relationships.

Use:

- Compact ordered inventory records.
- Integer-indexed relationship edges.
- Deduplicated owner and category references.
- Only meaningful resolved local dependencies.
- Derived reverse relationships.
- Compact evidence references.
- Bounded recent CI incident summaries.
- Current reusable finding records.
- Session Pack at the beginning of the JSON.
- No complete source files.
- No full CI logs.

If the complete required data cannot safely fit the size budget, fail generation and report the largest sections. Never publish an incomplete Atlas as current.

The 1 MiB target must be demonstrated against the real repository, not just a tiny test fixture.

---

# PART 16 — SCHEMA AND ATLAS DATA CONTRACT

The Atlas logical sections must include:

```json
{
  "atlas_schema_version": "2.0.0",
  "status": "CURRENT_OR_PARTIAL",
  "repository": {},
  "source_baseline": {},
  "authority_model": {},
  "session_pack": {},
  "coverage": {},
  "inventory": {},
  "ownership": {},
  "architecture": {},
  "requirements": {},
  "symbols": {},
  "compliance_traceability": {},
  "relationships": {},
  "dependency_impact": {},
  "workflow_graph": {},
  "test_map": {},
  "verified_knowledge": {},
  "research_memory": {},
  "ci_evidence": {},
  "failure_memory": {},
  "evidence_freshness": {},
  "external_dependencies": {},
  "change_history": {},
  "provenance": {},
  "known_limitations": [],
  "integrity": {}
}
```

These are logical sections. Avoid duplicating the same content across sections.

The schema must validate the exact required structure.

Incompatible format changes must bump the version.

The generator and schema must be tested together against the real output.

---

# PART 17 — IMPLEMENTATION ORDER

## TASK 1: Safe registry and owner extraction

Modify:

- `project_reference_atlas.py`
- `test_project_reference_atlas.py`

Prove:

- Dynamic entries cannot erase literal registries.
- Safe constants and literal dictionary references resolve.
- Unknown dynamic expressions are not executed.
- Ownership evidence is explicit.
- Duplicate owners are rejected.

## TASK 2: T16 symbol and contract intelligence

Reuse:

- `contract_graph.py`
- `source_intelligence/dependency_graph.py`
- `symbol_intelligence/snapshot.py`

Integrate module/symbol/contract indexes into Atlas.

Prove:

- Symbol relationships have exact source file identities.
- Dependency edges resolve only when supported.
- Unsupported formats are reported.
- No duplicate scanner is created.

## TASK 3: Complete compact Atlas and schema

Modify:

- `project_reference_atlas.py`
- `project_reference_atlas.schema.json`
- `test_project_reference_atlas.py`

Prove:

- Complete tracked inventory.
- Exact file blob SHAs.
- Owner and document mappings.
- Dependency and test maps.
- Compliance records.
- Research memory contract.
- CI and failure memory.
- Session Pack.
- Under 1 MiB output for the real repository.
- Deterministic integrity fingerprint.

## TASK 4: Evidence-backed research reuse

Reuse:

- `AUTONOMY_ENGINE/research/research_cache.py`
- `AUTONOMY_ENGINE/research/research_gate.py`
- `AUTONOMY_ENGINE/research/research_policy.py`
- `AUTONOMY_ENGINE/research/source_policy.json`
- T14 and T23 evidence validation.

Prove:

- Same research fingerprint can be reused only when source and freshness rules pass.
- Current facts expire according to the appropriate policy.
- Malformed cache data does not silently become verified empty knowledge.
- Durable findings are preserved inside Atlas.
- No duplicate research database is introduced.

## TASK 5: Requirement-to-code-to-test compliance

Reuse:

- T02.
- T10.
- T14.
- T16.
- T17.
- T19.
- T20.
- T23.

Prove:

- Every claimed verified requirement has authoritative source, implementation, test and matching proof.
- Missing traceability is UNKNOWN, not VERIFIED.
- Code changes invalidate only affected findings.
- Unrelated code remains reusable.
- Assistant-delivered source is read back before claiming it was saved correctly.

## TASK 6: Cross-chat continuity

Reuse:

- T07.
- T14.
- T24.
- T25.
- T28.
- T30.

Prove:

- New chat can use fixed repository identity and connected GitHub tools.
- It loads the latest valid Atlas and live state.
- It does not request old repository links.
- It resumes from the last valid work unit.
- It does not rely on in-memory T23/T24/T30 stores for permanent persistence.
- It does not reread the complete repository when the evidence remains valid.

## TASK 7: CI failure memory and event coverage

Modify:

- `.github/workflows/homio-project-reference-atlas.yml`
- `test_project_reference_atlas.py`
- Only additional producer workflows when the live event audit proves a real missing refresh path.

Prove:

- All source-branch writers have a refresh route.
- Reusable workflow callers are mapped correctly.
- Concurrent publication is serialized.
- Bot-generated updates are captured.
- Old workflow runs cannot publish current status for a newer SHA.
- Backend, frontend and Atlas failures remain distinct.
- Reference branch readback matches the generated source SHA.

## TASK 8: EntryPoint startup integration

Modify:

- `update_entrypoint_atlas_reference.py`
- `AI_AGENT_ENTRYPOINT.py`
- Existing EntryPoint contract tests.

Prove:

- One managed integration block.
- Existing stable policy is preserved.
- New-chat startup uses the connected repository automatically.
- No old links are requested when tool access is available.
- Session Pack validation occurs before broad reading.
- Atlas cannot override task authority.
- Repeated updater execution is idempotent.

## TASK 9: Full end-to-end verification

Prove the full sequence:

1. A real source file changes.
2. The workflow detects that exact change.
3. Atlas updates its path and blob SHA.
4. T17 identifies the affected dependencies.
5. Only affected findings become stale.
6. Unrelated verified findings remain reusable.
7. Relevant tests run against the matching source identity.
8. CI evidence is stored with exact run identity.
9. Session Pack points to the current task and exact next files.
10. A new chat resumes without repeating broad research.
11. A changed requirement invalidates affected compliance evidence.
12. A repeated unchanged CI failure reuses the previous diagnosis.
13. A stale or missing Atlas fails closed.

---

# PART 18 — REQUIRED FAILURE AND REGRESSION TESTS

### Research and repeated search
- `test_same_repository_query_reuses_same_sha_findings`
- `test_changed_index_invalidates_only_affected_query_results`
- `test_research_result_requires_source_provenance`
- `test_expired_external_research_requires_targeted_lookup`
- `test_current_fact_reuse_respects_research_policy`
- `test_corrupt_research_cache_is_not_treated_as_valid_empty`
- `test_research_memory_has_no_duplicate_authoritative_store`

### Coding compliance
- `test_requirement_maps_to_authoritative_document`
- `test_requirement_maps_to_actual_source_files`
- `test_requirement_maps_to_relevant_tests`
- `test_missing_mapping_is_unknown_not_verified`
- `test_pass_requires_matching_source_and_ci_evidence`
- `test_saved_file_identity_is_recorded`
- `test_changed_code_invalidates_only_dependent_compliance`
- `test_changed_tests_invalidate_affected_evidence`

### Repository and symbols
- `test_complete_git_tree_inventory`
- `test_exact_blob_sha_for_every_file`
- `test_safe_symbol_snapshot`
- `test_contract_graph_relationships`
- `test_no_duplicate_owner`
- `test_unknown_owner_is_explicit`
- `test_unsupported_format_is_reported`

### Link and dependency sync
- `test_added_file_is_indexed`
- `test_deleted_file_has_no_current_link`
- `test_renamed_file_updates_known_relationships`
- `test_dependency_change_uses_t17`
- `test_unrelated_file_preserves_findings`
- `test_unresolved_link_is_not_guessed`

### CI and failure memory
- `test_same_failure_signature_reuses_verified_history`
- `test_changed_source_rechecks_failure`
- `test_repair_requires_post_fix_evidence`
- `test_ci_run_attempt_is_preserved`
- `test_ci_pass_is_bound_to_exact_head_sha`
- `test_backend_frontend_and_atlas_failures_are_separate`

### Cross-chat startup
- `test_session_pack_uses_live_state`
- `test_new_chat_does_not_require_old_links_when_repository_access_exists`
- `test_session_pack_uses_exact_head`
- `test_invalid_atlas_blocks_fast_resume`
- `test_t07_bootstrap_preserves_authority`
- `test_t24_continuity_validates_evidence`
- `test_in_memory_store_is_not_treated_as_durable`

### Automation and security
- `test_all_source_writers_have_refresh_coverage`
- `test_reusable_workflows_map_to_actual_callers`
- `test_bot_commit_has_refresh_path`
- `test_publication_is_serialized`
- `test_source_sha_change_during_generation_fails`
- `test_pull_request_cannot_publish_reference`
- `test_wrong_repository_cannot_publish`
- `test_atlas_size_budget_is_enforced`
- `test_integrity_fingerprint_is_deterministic`
- `test_sensitive_values_are_not_serialized`

Add equivalent tests only once. Use existing owners' tests rather than duplicate them in the Atlas suite.

---

# PART 19 — AUTOMATIC ENTRYPOINT AND ATLAS UPDATE RULES

**Atlas:**

- Rebuild on every ordinary source push.
- Refresh after relevant completed source-writing workflows.
- Refresh on explicit repository dispatch.
- Support manual recovery.
- Run scheduled recovery checks.
- Compare exact HEAD before and after generation.

**EntryPoint:**

- Remain stable on ordinary implementation commits.
- Its latest blob SHA is recorded in Atlas.
- Stable policy changes require controlled update and contract tests.
- Its Atlas path remains fixed and tested.
- Dynamic repository paths and ownership links are maintained in Atlas.

Do not create a commit loop by having the Atlas workflow automatically modify `reos-development` on every push.

The reference publisher writes only to `reos-project-reference`.

---

# PART 20 — KNOWN PLATFORM AND SYSTEM LIMITS

The objective is to eliminate unnecessary repeated work, not make impossible guarantees.

### ChatGPT connector

New-chat bootstrap can avoid user-provided links when the connected GitHub app can access the repository.

A repository file cannot reconnect a disconnected ChatGPT integration.

If the connector is unavailable, one reconnection is required; the user should not be asked to resend a list of old links.

### External research

A GitHub workflow cannot see unrecorded ChatGPT web searches or private conversation reasoning.

Only materially used findings saved through existing authoritative project documents/evidence can become durable Atlas research memory.

Current external facts may still need rechecking after their valid freshness period.

### Semantic code correctness

Static parsing cannot prove every business behavior.

A compliance result requires explicit requirements, implementation mapping, tests and relevant proof.

Unsupported semantics must be marked PARTIAL or UNKNOWN.

### External runtime configuration

Production secrets, permissions, API providers and live database schema require the appropriate task-specific live check.

A repository Atlas cannot guarantee that external systems have not changed.

### No-false-completion rule

A test PASS does not prove every unrelated acceptance criterion.

An Atlas generation PASS does not prove the whole reference system complete.

A successful saved file readback does not by itself prove implementation correctness.

Only exact evidence supports each claim.

---

# PART 21 — LIVE BASELINE AT PLAN CREATION

Verified source branch HEAD:

`3a493bb4c5e3d748664fc5be3c6b6059fc0556d1`

Reference branch HEAD:

`7f7f3692dc13433130d60026311d7099b25fd15`

Git-tracked files observed:

`2,390`

Workflow files observed:

`26`

Atlas workflow run #11:

`46139831143`

Run result at that baseline:

`PASS`

These are historical baseline identities. Every implementation task must refresh the actual live HEAD and file blob SHAs before changing any file.

The current task authority observed at this baseline remains:

`BACKEND-001-B4 — PostgreSQL integration`

This reference-system implementation must not change B4 acceptance criteria or task state.

---

# PART 22 — FINAL ACCEPTANCE: HOW WE KNOW THE USER'S PROBLEM IS SOLVED

The system is accepted only when all of these outcomes are demonstrated:

1. The assistant can find the repository from fixed identity without requesting old URLs.
2. A new chat retrieves the current Atlas and Session Pack.
3. It reads the minimum live state authority.
4. It avoids broad repository searches when the relevant index and evidence are unchanged.
5. It reuses the previous verified code-compliance finding for unchanged files.
6. It recognizes when a file change invalidates that finding.
7. It identifies the affected tests without re-auditing unrelated modules.
8. It remembers proven CI failure diagnoses.
9. It automatically synchronizes source paths and links.
10. It updates current SHA and source provenance.
11. It tracks architecture and requirement changes.
12. It records whether a saved coding version has actually passed its relevant checks.
13. It distinguishes stable knowledge from time-sensitive web research.
14. It preserves cross-chat continuity without depending on ephemeral in-memory objects.
15. It never invents missing evidence or falsely claims full understanding.

**Final operating rule:**

Do not repeat research merely because a chat changed.

Do not repeat file reading merely because a task continues.

Do not repeat verification when the relevant code, tests, dependencies and evidence remain unchanged.

Do not repeat a CI investigation when the same verified failure and exact relevant inputs already exist.

Automatically update all dynamic project references when their source changes.

Read only the current authority, the two references and the files that the actual change or task requires.

**Authority boundary:** `state.json` remains the sole task authority. The Atlas is a verified project knowledge and navigation system, never a replacement task manager or production security runtime.
