# HOMIO / REOS — PROJECT REFERENCE ATLAS IMPLEMENTATION PLAN

## Consolidated Engineering Implementation Contract — Version 2.1

**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical source branch:** `reos-development`  
**Generated reference branch:** `reos-project-reference`  
**Stable operating reference:** `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`  
**Generated project reference:** `REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json`  
**Design authority:** `REOS_CONTROL_CENTER/Project Foundation work`  
**Execution authority:** `REOS_CONTROL_CENTER/data/state.json`

**Document status:** Updated implementation specification. This document does not mean that the proposed system is already implemented, approved, or operationally verified.

**Audience:** HOMIO / REOS engineering agents and maintainers. The human project owner does not need to understand or manually implement the code described here. Complete file replacements, exact paths, and evidence must be provided for any later implementation work.

---

# PART 1 — PURPOSE AND NON-NEGOTIABLE OBJECTIVE

The purpose is to make GPT-assisted HOMIO / REOS engineering continuous, evidence-backed, efficient, and resistant to repeated research and context loss.

The system must reduce unnecessary repetition of:

- Repository discovery.
- Reading unchanged source files.
- Searching for already-known file paths.
- Reconstructing known ownership and dependency relationships.
- Repeating valid architecture research.
- Rechecking unchanged code when its previous evidence remains valid.
- Investigating an identical, previously diagnosed CI failure without new evidence.
- Asking the user to resend old repository links, work-plan links, or Actions links.
- Rebuilding the same project context every time a new chat starts.
- Repeating completed work because a chat or context window changed.

The objective is **not** to eliminate necessary engineering verification.

The objective is:

> Research once → verify → preserve the result and its provenance → detect actual changes → reuse unchanged findings → reverify only the affected scope.

A new chat should be able to locate the current project position without requiring the user to explain HOMIO / REOS again.

It must still inspect the actual source files required by the current task. An index is not a substitute for implementation code, tests, or authoritative documents.

## Success criteria

The system is successful only when it demonstrates that:

1. Exactly two primary repository project-reference files are maintained.
2. A new chat can retrieve and validate those references through the connected GitHub access available in that ChatGPT experience.
3. The live task and status are recovered from `state.json`, not guessed from old chat history.
4. Existing ACRL owners are reused rather than duplicated.
5. Previous research is reused only while its source identity and freshness remain valid.
6. A delivered file can be compared with the exact file saved in GitHub.
7. A source change invalidates the affected findings without invalidating unrelated findings.
8. CI failure diagnoses are reused only when their relevant inputs and failure identity still match.
9. Repository path and dependency relationships are updated automatically.
10. A stale, missing, incomplete, or unreadable Atlas is never presented as current.
11. The user is not asked to repeat information already available from the connected repository and valid project evidence.
12. No false claim of complete semantic understanding or zero-verification engineering is made.

---

# PART 2 — EXACTLY TWO PRIMARY PROJECT-REFERENCE FILES

HOMIO / REOS will have exactly two primary repository project-reference files.

The five supporting implementation files described later are not additional project references. Existing source files, architecture documents, task evidence, tests, and `state.json` remain in their existing roles.

## REFERENCE 01 — Stable operating and authority reference

**Exact path:**

`REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`

### Responsibility

This file defines how GPT and engineering agents must operate HOMIO / REOS.

It is the stable operating reference and must include or preserve:

1. Canonical repository identity.
2. Canonical source branch.
3. Project identity: `HOMIO / REOS`.
4. Authority hierarchy.
5. Stable operating rules.
6. Existing module and ACRL ownership.
7. Startup procedure.
8. New-chat recovery instructions.
9. Atlas retrieval and validation procedure.
10. Research reuse rules.
11. Code delivery and saved-file verification requirements.
12. Requirement-to-code-to-test compliance rules.
13. Change-impact and selective-reverification rules.
14. Evidence freshness and provenance requirements.
15. GitHub Web Editor and human write boundary.
16. Security, privacy, and secret-handling boundaries.
17. Prohibition on duplicate engines, registries, APIs, bridges, and task managers.
18. Full-file replacement and readback requirements.
19. Human approval boundaries.
20. Context-loss recovery instructions.

### Stable-file policy

The EntryPoint must not be rewritten or regenerated on every ordinary source push.

It should change only when stable operating policy, authority, ownership, or startup integration changes.

Dynamic information belongs in the generated Atlas, including:

- Current file paths and SHAs.
- Current task and Session Pack.
- Dependency relationships.
- Test and workflow identities.
- Verification results.
- CI failure history.
- Research findings.
- Evidence freshness.
- Code delivery verification records.

The EntryPoint must preserve the existing project rules. The existing large EntryPoint must not be replaced merely to insert Atlas support.

The existing updater must use one idempotent managed integration block, preserve the existing policy, reject partial or duplicate managed blocks, and validate the final complete output.

---

## REFERENCE 02 — Automatically generated project knowledge reference

**Exact path on `reos-project-reference`:**

`REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json`

### Responsibility

The Atlas is the generated, SHA-backed technical map and durable repository-side knowledge reference.

It must contain or index:

1. Complete Git-tracked file inventory.
2. Exact Git blob SHAs and file modes.
3. File classification and ownership.
4. ACRL owner routing and owner contracts.
5. Architecture document relationships.
6. Master-reference and requirement relationships.
7. Workstream routing.
8. Source-code symbols and signatures where safely extractable.
9. Imports and local dependency edges.
10. API, schema, and contract relationships where supported.
11. Test relationships.
12. Workflow and reusable-action relationships.
13. Change history and impact records.
14. Requirement-to-code-to-test compliance traceability.
15. Previous verified research and its provenance.
16. Evidence identity and freshness.
17. CI results and failure memory.
18. Code delivery and saved-file verification evidence.
19. External dependency verification metadata.
20. Known limitations and unresolved relationships.
21. A compact current Session Pack.
22. Exact source, state, and EntryPoint baseline identities.

The Atlas is a derived knowledge and navigation reference. It is not a task authority, architecture approval authority, or production runtime security component.

### Atlas and Session Pack relationship

The Session Pack must be a section inside the Atlas JSON.

It must not become a third independent project-reference file.

The Session Pack is the short, task-focused portion of the Atlas used at the start of a new chat. Detailed records remain available in the same Atlas and are retrieved only when necessary.

The Session Pack must appear near the beginning of the serialized Atlas so that the most important current information is encountered first.

---

# PART 3 — AUTHORITY HIERARCHY

The system must preserve the existing HOMIO / REOS authority model.

| Information | Controlling authority |
|---|---|
| Current task and status | Live `REOS_CONTROL_CENTER/data/state.json` |
| Actual implementation | Live GitHub source branch |
| Task acceptance criteria | Authoritative task plan and state contract |
| Approved architecture | Designated architecture master |
| Stable operating rules | `AI_AGENT_ENTRYPOINT.py` |
| Existing module ownership | Existing owner contracts and source |
| Test and CI verification | Exact test and CI evidence |
| Repository inventory and derived relationships | Generated Atlas |
| Previously verified research | Atlas, only while fresh and valid |
| Cross-chat recovery | T07/T14/T24 validated evidence and Session Pack |
| Human approval decisions | Existing approval and decision boundaries |

When two sources conflict:

1. Detect the conflict.
2. Identify the exact source paths, sections, SHAs, and authority types.
3. Use the correct existing authority owner.
4. Resolve only the relevant conflict.
5. Preserve the resolution evidence.
6. Stop if the controlling authority cannot be established.

The Atlas cannot override `state.json`, task acceptance criteria, approved architecture, or human approval.

**Important task protection:** This reference system must not alter the current B4 task, its acceptance criteria, its work plan, or its guarded Control Center completion requirements.

---

# PART 4 — CHATGPT PROJECT WORKSPACE

The ChatGPT Project workspace is an external GPT session layer.

It is not a third repository reference file and is not a replacement for GitHub.

### Purpose

Use one dedicated ChatGPT Project for HOMIO / REOS when the feature is available in the user's ChatGPT account.

The Project can help keep together:

- HOMIO / REOS project instructions.
- Related engineering chats.
- Relevant conversation context.
- Project-specific working rules.

### Required operating rules

1. Project instructions must identify the project as HOMIO / REOS.
2. Project instructions must identify the canonical repository and branch.
3. Project instructions must require startup retrieval of EntryPoint, live state, and Atlas.
4. Project instructions must require reuse of existing ACRL owners.
5. Project instructions must forbid mixing Imperium AI with HOMIO / REOS.
6. Project instructions must require complete files and exact repository paths for user-facing code delivery.
7. Project instructions must preserve the user's GitHub Web Editor workflow.
8. Project instructions must prohibit unsupported claims that a file was saved, a workflow passed, or a task completed.
9. Project instructions must state that repository files and evidence, not chat memory, are the engineering authority.

### Dynamic Atlas policy

Do not rely on a manually uploaded copy of Atlas as the current project reference.

A manually uploaded copy can become stale as soon as GitHub changes.

Use the connected GitHub source to retrieve the live Atlas. If the connected GitHub feature cannot retrieve it in the current ChatGPT experience, report the limitation and do not pretend a stale uploaded copy is current.

Project memory and chat-history access depend on the Project memory setting, account, and product availability. The engineering system must not assume that every new chat can see every previous conversation.

### Platform boundary

The ChatGPT GitHub integration retrieves permitted repository content on demand. It does not provide a continuously synced GitHub repository index.

The GitHub app in ChatGPT is read-only for repository analysis and search. It must not be treated as a GitHub write mechanism.

The user continues to save source changes through the GitHub Web Editor. GitHub Actions may publish the generated Atlas to the dedicated reference branch under its separately authorized workflow permissions.

Official platform references:

- GitHub connection: https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt
- ChatGPT Projects: https://help.openai.com/en/articles/10169521-projects-in-chatgpt

These platform rules must be rechecked if OpenAI changes the product behavior.

---

# PART 5 — EXISTING FIVE ATLAS SUPPORTING FILES

The system must reuse the five existing Atlas implementation files.

No additional standalone scanner, research engine, resume database, symbol engine, failure engine, evidence registry, or task manager is authorized by this plan.

## File 1 — Atlas generator

**Path:**

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/project_reference_atlas.py`

**Existing blob SHA at plan inspection:**

`3c4c9417b113fc398266ea0fb5589f2051105c48`

Responsibilities:

- Read the exact Git-tracked repository inventory.
- Validate repository and branch identity.
- Extract supported source and document relationships safely.
- Reuse existing T16 functionality.
- Generate compact Atlas data.
- Attach exact source provenance.
- Calculate deterministic integrity metadata.
- Reject incomplete or stale publication.
- Report unsupported semantic relationships honestly.

### Existing observed limitation

The current registry extraction uses `ast.literal_eval` against whole registry assignments.

When a registry contains dynamic expressions or references to other dictionaries, the entire registry can become unavailable rather than preserving its resolvable entries.

This must be fixed through safe, per-entry static evaluation.

Unknown expressions must be recorded as unresolved. They must never be executed to obtain registry values.

## File 2 — EntryPoint updater

**Path:**

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/update_entrypoint_atlas_reference.py`

**Existing blob SHA at plan inspection:**

`c4d870fbd4d0309434df7f33a89ee71ed649227e`

Existing functions include:

- `project_reference_atlas_rules()`
- `project_reference_atlas_generation()`
- `repository_paths()`
- `startup_instructions()`
- `update_entrypoint(source)`

Responsibilities:

- Safely integrate Atlas instructions into the existing EntryPoint.
- Preserve the entire existing stable operating policy.
- Use one managed block.
- Validate existing registry and startup structures.
- Reject duplicate or partial managed blocks.
- Produce deterministic, idempotent output.
- Preserve existing function and variable ownership.
- Never replace the full EntryPoint with a newly invented smaller file.

## File 3 — Regression tests

**Path:**

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T16_Repository_Intelligence_File_Discovery/project_reference_atlas/test_project_reference_atlas.py`

**Existing blob SHA at plan inspection:**

`db000dd962999053f4692b9c52cbcfeabac915f7`

Responsibilities:

- Generator tests.
- Registry extraction tests.
- Atlas integrity tests.
- Schema compatibility tests.
- EntryPoint updater tests.
- Idempotency tests.
- Real repository integration tests.
- Regression tests for all new Atlas requirements.

Tests owned by existing ACRL modules should remain in those modules. Do not duplicate the entire ACRL regression suite inside this file.

## File 4 — Atlas schema

**Path:**

`REOS_CONTROL_CENTER/contracts/project_reference_atlas.schema.json`

**Existing blob SHA at plan inspection:**

`f8e74e673ccc935d137a5b82bb0b20d6db4d01b7`

Responsibilities:

- Validate all required Atlas sections.
- Validate data types and record identities.
- Reject missing required sections.
- Reject invalid source and evidence identities.
- Validate the Session Pack.
- Validate research, compliance, workflow, and failure records.
- Reject unsupported authority claims.
- Require an explicit partial or unknown status when evidence is incomplete.

## File 5 — Atlas workflow

**Path:**

`.github/workflows/homio-project-reference-atlas.yml`

**Existing blob SHA at plan inspection:**

`3e5cf8cab363dbbecdf3cc4a76d7accc86bf66e5`

Responsibilities:

- Generate Atlas from one exact source snapshot.
- Validate the generated data and schema.
- Publish only to `reos-project-reference`.
- Detect stale source inputs.
- Prevent concurrent publication races.
- Support explicit recovery and scheduled refresh.
- Preserve the canonical source branch.
- Keep pull-request validation separate from publication.

The workflow must never update `reos-development` as a side effect of Atlas publication.

---

# PART 6 — LIVE BASELINE AND VERIFIED GAPS AT VERSION 2.1

The following identities were read from the live GitHub repository during preparation of this version.

## Live source snapshot

| Item | Verified value |
|---|---|
| Source branch | `reos-development` |
| Source HEAD | `f4b57f7cbbd2ed884b59d4d20edeeb9b836613ea` |
| Source tree SHA | `be1e5f8c3736a3037a5065aaf1cae520d0d4f64f` |
| EntryPoint blob SHA | `f21a5d993fb2692838c77acc442f7059b9861958` |
| State blob SHA | `df35b7a4888e17110d8e04dad76d3e278053ce41` |
| Plan v2.0 blob SHA | `a526c416d9eeaba120afcada020fec75c65c0dee` |
| Reference branch HEAD | `c707b2b3120679749d38c5e6bac528c3b7390551` |

The reference branch commit `c707b2b3120679749d38c5e6bac528c3b7390551` was generated for source commit `f4b57f7cbbd2ed884b59d4d20edeeb9b836613ea`.

These are historical inspection identities. Every actual implementation task must refresh the live identities before changing source.

## Current task authority

The live `state.json` reports:

- Current gate: `BACKEND-001`.
- Current task: `BACKEND-001-B4: PostgreSQL integration`.
- Current subtask: `BACKEND-001-B4`.

This project-reference plan does not change that task or its acceptance criteria.

## Actual generated Atlas state

The Atlas currently observed on `reos-project-reference` has:

| Item | Observed result |
|---|---|
| Serialized content size | Approximately 5.1 MB |
| Atlas schema version | `1.0.0` |
| Atlas status | `INVENTORY_CURRENT_SEMANTICS_PARTIAL` |
| Tracked inventory entries | 2,391 |
| Static import edges | 7,020 |
| Documentation reference edges | 445 |
| Test files | 468 |
| Workflow files | 26 |
| ACRL owner-routing entries | 18 |
| Document registry owners | 0 |
| Workstream routing records | 0 |

The current Atlas does not yet contain the proposed complete Session Pack, research-memory, and requirement-compliance sections.

The current Atlas is not a fully complete GPT project knowledge system.

## Retrieval issue reproduced

The connected GitHub file-reading operation returned zero characters for the approximately 5.1 MB Atlas, including attempted limited line ranges.

A separate GitHub API content retrieval returned the full large JSON.

The result is not acceptable as proof that GPT can reliably retrieve and use the Atlas with a practical context budget.

The Atlas must be redesigned and tested against the actual connected GitHub reading path.

## Current implementation gaps

1. Safe per-entry extraction of dynamic registries is not complete.
2. Semantic owner extraction and owner completeness are partial.
3. Document registry and workstream mapping are empty in the current generated Atlas.
4. The current schema is `1.0.0`, not the proposed target contract.
5. The current Atlas is too large for the tested file-reading route.
6. The current Atlas lacks the required Session Pack and research/compliance sections.
7. The current ResearchGate does not independently verify evidence freshness.
8. The current ResearchCache is not a durable, provenance-verified research authority.
9. The current workflow concurrency key is event-specific rather than the required single publisher key.
10. The current workflow event list must be re-audited against actual source-branch writers.
11. The live EntryPoint still requires the controlled Atlas startup integration.
12. The new-chat process has not yet passed the full live ChatGPT/GitHub acceptance test.

A successful Atlas generation workflow run does not prove these gaps are fixed.

---

# PART 7 — EXISTING ACRL OWNER INTEGRATION

ACRL is an existing HOMIO / REOS engineering continuity and coordination system.

The Atlas must document and reuse the correct existing owners. It must not replace them.

The Atlas is a navigation, evidence, and relationship layer around those owners.

## Required owner map

| Existing owner | Responsibility to reuse |
|---|---|
| T02 Architecture Lock | Architecture authority, lock, and drift constraints |
| T05 Dependency Authority Map | Task and dependency authority reconstruction |
| T07 New Chat Bootstrap | Startup, restart payload, fast resume, and continuity validation |
| T09 State Fingerprint | State identity, fingerprint, integrity, and provenance |
| T10 Drift Detection | Detecting architecture or repository drift |
| T14 Repository Intelligence Context | Resume manifest, repository context, evidence freshness, and invalidation |
| T16 Repository Intelligence File Discovery | File discovery, source parsing, symbols, contracts, dependency graphs, and Atlas generation |
| T17 Change Impact Dependency Analysis | Changed-file impact closure and affected dependency identification |
| T19 Intelligent Test Selection and Failure Diagnosis | Test selection, failure classification, and diagnosis |
| T20 Autonomous Repair Patch Verification | Patch and repair verification, source identity, and proof |
| T21 Git Repository Read/Write Coordination | Git scope, commit, push, lock, provenance, and authorization boundaries |
| T23 Reference Evidence Resolution Engine | Evidence identity, source resolution, validation, and provenance |
| T24 Cross-Chat Continuity Recovery Engine | Cross-chat continuity evidence and recovery |
| T25 Context Token Work Budget Manager | Context and work-budget allocation |
| T28 Conflict Resolution Reconciliation Engine | Authority and evidence conflict resolution |
| T29 Human Decision Boundary Controller | Human approval and decision boundaries |
| T30 Autonomous Completion Handoff Engine | Completion proof, residual work, and handoff |

### Exact path corrections

The implementation must use the actual live paths, including:

- `T14_Repository_Intelligence_Context` for repository resume and context.
- `T14_Full_Regression` is a separate directory and must not be confused with the repository-context owner.
- `T20_Autonomous_Repair_Patch_Verification`.
- `T25_Context_Token_Work_Budget_Manager`.

### Owner integration rules

1. Read the actual owner contract and interfaces before integration.
2. Record the exact owner path, contract path, and source blob SHA.
3. Reuse the existing public interface rather than creating a competing interface.
4. Use the owner's tests where the existing test suite already covers the requirement.
5. Add new tests to the existing owner test suite when the responsibility belongs there.
6. Do not assume a directory or owner is fully integrated merely because it exists.
7. Mark unverified owner relationships as partial or unknown.
8. Recheck only owners affected by a real source or contract change.

### Persistence boundary

Some existing T23, T24, and T30 stores are in-memory stores.

They must not be treated as permanent cross-chat persistence.

The durable repository-side reference is the Atlas and the existing authoritative project evidence.

No second durable continuity database, evidence database, or research database may be created for this project without a separately approved architecture decision.

---

# PART 8 — GPT NEW-CHAT STARTUP HANDSHAKE

This is one of the main requirements of version 2.1.

A repository file cannot force ChatGPT to invoke a connected app. The startup procedure must therefore be explicit and tested in the actual ChatGPT experience.

## Startup sequence

At the beginning of every new HOMIO / REOS engineering chat:

### Step 1 — Establish project identity

- Confirm HOMIO / REOS project identity.
- Use the fixed repository `prajaktaranjane80-sketch/Homio`.
- Use the source branch `reos-development`.
- Never mix in Imperium AI.
- Use the dedicated ChatGPT Project when available.
- Do not ask the user to resend the old repository URL when the connected repository is available.

### Step 2 — Read the stable operating reference

Retrieve the live:

`REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`

Confirm its current blob SHA and use its authority, ownership, and startup rules.

### Step 3 — Read the source branch and task authority

Retrieve the live `reos-development` branch HEAD and:

`REOS_CONTROL_CENTER/data/state.json`

Record:

- Source HEAD.
- Source tree SHA.
- State blob SHA.
- Current task.
- Current subtask.
- Authoritative acceptance criteria.
- Current work-plan identity where applicable.

Do not infer a new task from the Atlas or chat history.

### Step 4 — Retrieve the generated Atlas

Retrieve:

`REOS_CONTROL_CENTER/HOMIO_PROJECT_REFERENCE_ATLAS.json`

from `reos-project-reference`.

Use the actual connected GitHub reading mechanism available to that ChatGPT experience.

Do not claim retrieval succeeded if the tool returns empty, truncated, stale, or invalid content.

### Step 5 — Validate Atlas provenance

The Atlas must match:

- Repository identity.
- Source branch.
- Exact source HEAD.
- Exact source tree SHA.
- EntryPoint blob SHA.
- Live state blob SHA.
- Atlas schema version.
- Atlas integrity fingerprint.
- Generator identity and source provenance.

The reference branch must not be trusted merely because a JSON file exists there.

### Step 6 — Validate Session Pack

The Session Pack must be valid for the exact live source and state identities.

It must identify:

- Current task and subtask.
- Current authoritative work plan.
- Relevant architecture references.
- Existing code owners.
- Verified completed work.
- Remaining work.
- Last valid test and CI evidence.
- Known failure diagnoses.
- Stale and invalidated evidence.
- Exact files needed for the next work unit.
- Required tests.
- Next permitted action.
- Missing external verification.

The Session Pack must never authorize a task or state transition.

### Step 7 — Decide resume mode

Use the existing T07 and T14 resume contracts.

Possible outcomes:

- `FAST_RESUME`: Exact baseline matches and relevant evidence remains valid.
- `TARGETED_REFRESH`: Only identified changed sources and dependents need verification.
- `PARTIAL_RESUME`: Some semantic relationships or evidence are incomplete.
- `FULL_RECONSTRUCTION_REQUIRED`: The current baseline cannot safely be reconciled.
- `BLOCKED`: Authority or integrity cannot be established.

Do not convert a partial or blocked result into a successful fast resume.

### Step 8 — Read only required source files

Use the Session Pack, T16, T17, and existing owner relationships to identify the minimum task-specific files.

Read those exact live files.

Do not read the full repository merely because a new chat started.

### Step 9 — Continue from the last verified work unit

Continue from the last valid incomplete work unit.

Do not repeat completed work unless its input identity or evidence has changed.

Do not skip an unfinished required step just because a previous chat described it as done.

### Step 10 — Report only material blockers

If the repository connection is missing, say so clearly and request reconnection.

If the Atlas cannot be retrieved, report the exact retrieval failure and use a limited, targeted fallback if safe.

Do not silently substitute stale chat context for live repository state.

Do not ask the user for a large bundle of old links or project explanations.

---

# PART 9 — CHAT-TO-PROJECT KNOWLEDGE CAPTURE

GitHub Actions cannot automatically read unrecorded private ChatGPT conversation history, private reasoning, or every web search from a chat.

This is a real platform boundary.

### Required capture process

When a conversation produces a material project finding:

1. Determine whether it changes an architecture decision, task requirement, code implementation, verification result, or project operating rule.
2. Identify the controlling existing document or evidence process.
3. Prepare the required complete content for that existing location.
4. The user saves it through the GitHub Web Editor when a source change is required.
5. Retrieve the saved source from GitHub.
6. Verify its exact blob SHA.
7. Allow the Atlas generation process to index the saved finding.
8. Verify the Atlas source baseline and finding provenance.

Do not preserve every conversation or every search result.

Preserve the verified conclusion, its source, the decision it supports, its owner, and freshness.

### Prohibited behavior

- Do not claim a chat finding is permanently saved when it exists only in conversation history.
- Do not invent an automatic private-chat-to-GitHub synchronization mechanism.
- Do not create a separate chat-memory database.
- Do not create a third project-reference document.
- Do not copy complete web pages or full private conversations into Atlas.
- Do not treat chat memory as task authority.

If a material finding cannot be saved through an existing authorized project/evidence process, explicitly mark it as conversation-only and not yet durable.

---

# PART 10 — PERSISTENT RESEARCH REUSE

Reuse the existing files:

- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/research_cache.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/research_gate.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/research_policy.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/research/source_policy.json`

Also reuse T14 and T23 evidence validation.

Do not create a new research engine or second canonical research database.

## Existing observed limitations

The current `ResearchCache` is a small JSON key/value cache.

It does not independently enforce:

- Source commit SHA.
- Source file blob SHA.
- Query fingerprint.
- Evidence provenance.
- Expiration.
- Freshness.
- Integrity.
- Atomic writes.
- Corruption recovery.

Malformed JSON currently becomes an empty dictionary rather than a distinct cache-corruption result.

The current ResearchGate checks a verified flag, source count, and topics. It does not independently prove evidence freshness.

ResearchPolicy identifies domains that can require current external research, including software versions, API behavior, cloud services, pricing, security guidance, standards, and support windows.

## Required research record

Each reusable research finding must contain:

- Stable finding ID.
- Normalized query fingerprint.
- Research category and topic.
- Relevant project requirement.
- Source names and URLs.
- Repository paths and blob SHAs, where applicable.
- Source authority tier.
- Short verified conclusion.
- Decision supported.
- Verification method.
- Date checked.
- Publication or modified date when available.
- Applicable freshness policy.
- Expiry or invalidation condition.
- Current status.
- Provenance identity.

Do not store full search-result pages, unnecessary copied web content, or complete browser logs.

## Research reuse rules

### Repository research

If the query, repository snapshot, and relevant source SHAs are unchanged, reuse the valid recorded findings.

Do not repeat broad GitHub discovery searches just because a new chat started.

### External web research

Reuse findings only while the sources, facts, and applicable freshness rules remain valid.

A current or volatile fact must be looked up again when its freshness period expires or a relevant source changes.

### Safety and correctness boundary

Do not reuse stale security guidance, obsolete software versions, outdated API behavior, pricing, compliance requirements, or other volatile external facts as current truth.

If evidence freshness cannot be established, mark the finding `STALE` or `UNKNOWN`.

---

# PART 11 — EXACT CODE DELIVERY AND SAVED-FILE VERIFICATION

This section addresses a critical practical problem: code supplied by GPT is not automatically the same as the code eventually saved in GitHub.

### Required delivery record

When GPT provides a complete file replacement, capture:

1. Target repository path.
2. Target branch.
3. Exact intended UTF-8 content.
4. Expected SHA-256 fingerprint of the delivered content.
5. Expected byte length.
6. Relevant authoritative requirement IDs.
7. Required tests and verification method.
8. Delivery timestamp or delivery identity.

### After the user saves the file

The assistant must:

1. Retrieve the actual saved file from GitHub.
2. Obtain its actual content and Git blob SHA.
3. Compute the SHA-256 fingerprint of the retrieved UTF-8 content.
4. Compare the actual content fingerprint with the intended delivered fingerprint.
5. Confirm exact byte length.
6. Report `MATCH`, `MISMATCH`, or `NOT_VERIFIED`.
7. Use the saved repository version as canonical.
8. Run the relevant tests and verification after a match.
9. Record the exact resulting commit, blob SHA, and CI/test evidence.

A blob SHA and a SHA-256 digest of file contents are different identities. They must not be compared as though they are the same hash algorithm.

### Persistence boundary

The assistant can calculate the expected delivery fingerprint and compare it after readback.

A conversation delivery record is not automatically durable in GitHub.

After a successful readback, preserve the verification result through the existing authorized task/evidence process and Atlas generation. Do not create a separate universal delivery database.

If no durable record exists, report that the comparison was verified in the current session but was not yet preserved for future sessions.

### Failure handling

- If the user has not saved the file, do not claim it was saved.
- If the saved content differs, identify the mismatch and do not claim success.
- If GitHub cannot be read, do not infer the result.
- If tests have not run, do not claim the implementation passed.
- If source changes after successful tests, invalidate the affected evidence.

---

# PART 12 — REQUIREMENT-TO-CODE-TO-TEST COMPLIANCE

The Atlas must contain `compliance_traceability`.

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
Exact test / CI / T20 evidence
            |
            v
Current compliance result
```

Each compliance record must identify:

- Requirement ID.
- Authoritative document path and section.
- Exact source document blob SHA.
- Task/state criterion identity.
- Implementation paths and blob SHAs.
- Relevant test paths and blob SHAs.
- Workflow and reusable-action identities.
- Dependency fingerprint.
- Verification method.
- Exact CI run and attempt, or other accepted evidence ID.
- Result.
- Verification date.
- Invalidation reason.

Allowed statuses:

- `VERIFIED`
- `FAIL`
- `PARTIAL`
- `UNKNOWN`
- `STALE`
- `NOT_APPLICABLE`

`VERIFIED` requires actual authoritative requirement mapping, actual saved implementation identity, relevant tests, and matching successful evidence.

File presence, code similarity, a passing unrelated workflow, or an assistant statement is not proof.

### Selective compliance reuse

When all relevant input identities remain unchanged, reuse the previous valid compliance result.

When a source, requirement, test, contract, dependency, workflow, or other required input changes, invalidate only the affected records.

If the dependency graph is incomplete, report `PARTIAL` or `UNKNOWN` and perform the necessary targeted discovery.

---

# PART 13 — SYMBOL, MODULE, CONTRACT, AND TEST KNOWLEDGE

Use the existing T16 owners:

- `T16_Repository_Intelligence_File_Discovery/contract_graph.py`
- `T16_Repository_Intelligence_File_Discovery/source_intelligence/dependency_graph.py`
- `T16_Repository_Intelligence_File_Discovery/source_intelligence/source_parser.py`
- `T16_Repository_Intelligence_File_Discovery/symbol_intelligence/snapshot.py`
- Existing T16 web-source parsing.

Where supported, index:

- Module path.
- Public classes and functions.
- Function and method signatures.
- Imports.
- Local dependencies.
- Contract IDs.
- API route relationships.
- Schema relationships.
- Test relationships.
- Existing owner.
- Exact source SHA.
- Parser status and confidence.

Do not copy complete source files into Atlas.

A parser failure must be recorded, not hidden.

An inventory-complete Atlas is not necessarily semantically complete.

---

# PART 14 — CHANGE IMPACT AND SELECTIVE REVERIFICATION

Reuse:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py`

Existing public interface:

`ChangeImpactAnalyzer(repository_root).analyze(changed_paths)`

Use T09 for relevant source identity and T16/T05 for dependency and ownership information.

Detect:

- Added files.
- Modified files.
- Deleted files.
- Renamed or moved files.
- File-mode changes.
- Import changes.
- Package and lockfile changes.
- Architecture and task-plan changes.
- State changes.
- Test changes.
- Workflow and reusable-action changes.
- EntryPoint changes.
- Owner and contract changes.

For each change:

1. Identify old and new identities.
2. Identify direct dependents.
3. Use T17 for impact closure.
4. Identify affected requirements.
5. Identify affected tests.
6. Identify affected workflows.
7. Identify stale research and compliance evidence.
8. Preserve unaffected valid findings.
9. Select the minimum safe reverification scope.
10. Update Atlas and Session Pack.

An unrelated source change must not automatically trigger a full repository audit.

If the dependency graph is incomplete, do not assume that the impact is empty. Perform targeted discovery and mark the result partial until resolved.

---

# PART 15 — LINK AND REFERENCE SYNCHRONIZATION

The Atlas must synchronize relationships when repository paths or identities change.

Handle:

- New files.
- Deleted files.
- Renamed files.
- Moved folders.
- Updated master architecture documents.
- Updated work plans.
- Updated tests.
- Updated imports.
- Updated workflows.
- Updated reusable actions.
- Updated owner mappings.
- Updated workstream references.
- Changed branch or source identities.

Each relationship must record:

- Canonical repository path or external URL.
- Relationship type.
- Discovery source.
- Target identity.
- Target SHA, where tracked.
- Resolution status.
- Confidence or parser status.
- Previous path when a rename is established.

Rules:

- Never guess a replacement for a deleted file.
- Never silently preserve a deleted target as current.
- Preserve old relationships only as historical.
- Mark unresolved links explicitly.
- Reverify external URLs according to their freshness policy.
- Do not duplicate a relationship in multiple Atlas sections.

---

# PART 16 — CI FAILURE MEMORY

Reuse T19:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis/failure_diagnosis.py`

Also reuse:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T19_Intelligent_Test_Selection_Failure_Diagnosis/selection_engine.py`

Each failure record must identify:

- Workflow path and workflow identity.
- Workflow blob SHA.
- Run ID and attempt.
- Trigger event.
- Source branch and exact head SHA.
- Job and failed step.
- Failure category.
- Normalized failure signature.
- Relevant source SHAs.
- Dependency fingerprint.
- Relevant test selector.
- Evidence URL.
- Diagnosis status.
- Verified root cause, if established.
- Repair commit, if any.
- Post-repair tests.
- Exact post-fix CI evidence.

Distinguish at least:

- Backend code regression.
- Frontend regression.
- Workflow configuration failure.
- Reusable action failure.
- Dependency or build failure.
- Runner or environment failure.
- Control Center governance failure.
- Atlas generation or publication failure.

### Same-failure reuse

When the same failure signature and exact relevant source identities recur:

- Reuse the previous verified diagnosis as historical evidence.
- Compare the current run and relevant inputs.
- Avoid repeating the entire investigation if nothing relevant changed.
- Do not blindly apply a historical repair.
- Require current post-fix tests and CI evidence before claiming repair success.

A matching error message alone is not sufficient to prove the root cause is unchanged.

---

# PART 17 — GITHUB WORKFLOW AND AUTOMATIC REFRESH

The Atlas must refresh whenever the source information it depends on changes.

Current workflow snapshot includes 26 workflow files.

Current major top-level workflow producers observed include:

- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/backend-b4-reopen.yml`
- `.github/workflows/homio-project-reference-atlas.yml`

The current Atlas workflow listens for backend CI, frontend CI, and guarded B4 recovery reopen completion, along with source pushes, manual dispatch, repository dispatch, and a scheduled refresh.

This list must not be blindly assumed to cover every source writer.

## Required event audit

Inspect actual workflow behavior, not merely declared permissions.

Map:

1. Top-level workflow.
2. Reusable `workflow_call` workflow.
3. Actual caller.
4. Jobs that receive source write permissions.
5. Actual Git pushes or GitHub API writes.
6. Actual files and branches written.
7. Completion event that follows each write.
8. Exact Atlas refresh path.

A `contents: write` permission is not proof that a workflow writes to the source branch.

A reusable workflow run is part of its top-level caller run. Do not incorrectly subscribe to every reusable workflow as though it were an independent top-level workflow.

### Bot-write requirement

GitHub Actions commits made using the normal `GITHUB_TOKEN` may not trigger another push workflow.

Every real source-branch writer must therefore have a verified refresh route, such as an applicable completion-trigger path or explicit refresh dispatch.

After an automated workflow writes `state.json` or other indexed source files, Atlas refresh must retrieve the latest committed source HEAD.

### Global publisher concurrency

Use one global publisher concurrency group:

`homio-project-reference-atlas-${{ github.repository }}`

Set:

`cancel-in-progress: false`

The publisher must not use event-specific concurrency groups that allow separate publisher runs for the same repository to race.

PR validation may use a separate non-publishing job, but it must not publish PR-head Atlas content.

### Exact-source protection

The workflow must:

1. Capture one exact source snapshot.
2. Validate repository and branch identity.
3. Verify source HEAD before generation.
4. Generate the Atlas from that snapshot.
5. Verify source HEAD again before publication.
6. Publish only to `reos-project-reference`.
7. Read back the publication.
8. Verify the reference branch contains the expected Atlas for the exact source HEAD.
9. Reject stale output.
10. Preserve reference branch history.
11. Never publish PR-head content as current source-branch state.
12. Never update `reos-development` as an Atlas side effect.

Use the minimum permissions required for each job.

---

# PART 18 — ATLAS SIZE, RETRIEVAL, AND CONTEXT BUDGET

This is a critical version 2.1 requirement.

The current Atlas is approximately 5.1 MB and the tested `fetch_file` reading path returned empty content.

The previous proposed 1 MiB limit was not demonstrated against a reliable real retrieval path. Therefore:

**1 MiB is not a proven final limit. It must not be treated as a guaranteed platform limit.**

## Required retrieval experiment

Test the actual GitHub reading mechanism used by ChatGPT.

The acceptance process must determine:

1. Which connected GitHub read operation can retrieve the Atlas.
2. Whether it returns the complete expected content.
3. Whether it can retrieve the required Session Pack and specific records.
4. Whether the returned content is truncated or empty.
5. Whether the operation consumes a practical amount of GPT context.
6. Whether the content's integrity can be checked after retrieval.

Test representative Atlas sizes and formats using the real source data.

The implementation must not choose a final size limit based only on a guess or a small unit-test fixture.

Use the largest consistently successful retrieval size observed in the actual supported path, then select a conservative target below it.

The 1 MiB figure may be used as one test point, not as a pre-approved guarantee.

## Compact representation

Keep the complete required data without silently deleting inventory or hiding unresolved relationships.

Use:

- Compact inventory arrays.
- Short field names only when schema clarity is preserved.
- Integer-indexed relationships.
- Deduplicated owner and category references.
- Meaningful resolved dependency edges.
- Derived reverse relationships where safe.
- Compact evidence identities.
- Bounded recent CI failure summaries.
- Compact research findings.
- Session Pack near the beginning.
- No complete source-file copies.
- No full CI logs.
- No repeated copies of the same evidence record.

## Context-budget policy

Use T25 for context and work-budget decisions.

Load:

1. Stable EntryPoint instructions.
2. The compact current Session Pack.
3. Only current-task-specific records.
4. Only exact source files needed for the next work unit.

Do not load the complete Atlas into the conversation when a validated targeted retrieval is sufficient.

T25 cannot be assumed to read ChatGPT's hidden platform context meter. It must not claim exact remaining ChatGPT tokens without a supported measurement source.

## Fail-closed behavior

If the Atlas cannot fit the validated retrieval budget without losing required information:

- Fail generation or publication.
- Report the largest Atlas sections.
- Report missing retrieval evidence.
- Do not publish an incomplete Atlas as current.
- Do not pretend the startup handshake passed.

Do not create several new reference JSON files as a workaround. The canonical project reference remains the single Atlas file.

---

# PART 19 — ATLAS DATA CONTRACT

The target Atlas schema must include these logical sections:

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
  "relationships": {},
  "dependency_impact": {},
  "workflow_graph": {},
  "test_map": {},
  "compliance_traceability": {},
  "verified_knowledge": {},
  "research_memory": {},
  "ci_evidence": {},
  "failure_memory": {},
  "delivery_verification": {},
  "evidence_freshness": {},
  "external_dependencies": {},
  "change_history": {},
  "provenance": {},
  "known_limitations": [],
  "integrity": {}
}
```

These are logical sections. Do not duplicate the same content across sections.

The generator, schema, and tests must be updated together.

The Atlas schema must not be declared upgraded until the generated real repository output validates against it.

A compatible schema change must be tested against the actual generated Atlas.

An incompatible data-format change must bump the schema version.

The target schema version is `2.0.0`; the currently generated Atlas remains `1.0.0` until the implementation is actually upgraded and read back.

---

# PART 20 — IMPLEMENTATION ORDER

The implementation must be carried out through the existing owners and the five supporting files.

Each task must have its own focused verification.

## TASK 1 — Safe registry and owner extraction

Modify:

- `project_reference_atlas.py`
- `test_project_reference_atlas.py`

Prove:

- Dynamic entries cannot erase literal registry entries.
- Safe constants and literal dictionary references resolve.
- Unknown dynamic expressions are never executed.
- Resolvable entries are preserved individually.
- Unresolved entries have explicit reasons.
- Duplicate owners are rejected.
- All extracted records have exact source provenance.

## TASK 2 — Complete ACRL and T16 integration

Reuse the existing ACRL owner map and T16 contract, source, dependency, and symbol owners.

Prove:

- Relevant owner directories and contracts are discovered.
- Each relationship has an exact source path and SHA.
- T02, T05, T07, T09, T10, T14, T16, T17, T19, T20, T21, T23, T24, T25, T28, T29, and T30 are accurately represented where relevant.
- `T14_Full_Regression` is not confused with `T14_Repository_Intelligence_Context`.
- Unknown or unsupported ownership is explicit.
- No duplicate engine or owner is introduced.

## TASK 3 — Complete compact Atlas and schema

Modify:

- `project_reference_atlas.py`
- `project_reference_atlas.schema.json`
- `test_project_reference_atlas.py`

Prove:

- Complete exact Git-tracked inventory.
- Exact path, file mode, and blob SHA.
- Ownership and document mapping.
- Workstream mapping.
- Dependency and test mapping.
- Symbol and contract data where supported.
- Session Pack.
- Research memory.
- Compliance records.
- CI and failure records.
- Delivery verification records.
- Deterministic integrity fingerprint.
- Real repository output validates against the target schema.
- Output remains within the empirically verified reader and context budget.

Do not silently claim semantic completeness if parsing or ownership remains partial.

## TASK 4 — Research evidence reuse

Reuse:

- `AUTONOMY_ENGINE/research/research_cache.py`
- `AUTONOMY_ENGINE/research/research_gate.py`
- `AUTONOMY_ENGINE/research/research_policy.py`
- `AUTONOMY_ENGINE/research/source_policy.json`
- T14 and T23 evidence validation.

Prove:

- Same research fingerprint can be reused only when source identity and freshness pass.
- Expired external research requires targeted current lookup.
- Corrupt cache is not treated as verified empty knowledge.
- Findings have source provenance.
- ResearchGate cannot approve stale evidence based only on a boolean.
- Atlas is the durable repository-side reference.
- No duplicate research database is created.

Before changing any existing ResearchCache behavior, inspect its live call sites and actual usage. Do not add a dependency merely to keep an unused component alive.

## TASK 5 — Requirement and code-delivery verification

Reuse:

- T02.
- T09.
- T10.
- T14.
- T16.
- T17.
- T19.
- T20.
- T21.
- T23.
- Existing task evidence and guarded verification process.

Prove:

- Every claimed verified requirement has an authoritative source.
- The actual saved implementation is identified.
- The delivered content and saved content can be compared exactly.
- Relevant tests and exact CI evidence are linked.
- Missing traceability remains `UNKNOWN`.
- Unchanged valid compliance records are reusable.
- Changed files invalidate only affected findings.

## TASK 6 — Cross-chat continuity and GPT startup

Reuse:

- T07.
- T09.
- T14.
- T24.
- T25.
- T28.
- T29.
- T30.

Modify only the existing EntryPoint updater, EntryPoint integration, Atlas generator, and relevant tests.

Prove:

- Fixed repository identity works.
- Live source HEAD and state are fetched.
- Atlas is retrieved from the correct branch.
- Source and state identities are validated.
- Session Pack is valid.
- T07/T14 resume decisions preserve authority.
- A new chat resumes from the correct work unit.
- No old links are requested when connected GitHub access is available.
- No full repository reread occurs when the relevant evidence remains valid.
- In-memory stores are not treated as permanent persistence.

## TASK 7 — Workflow event coverage and publication safety

Modify:

- `.github/workflows/homio-project-reference-atlas.yml`
- `test_project_reference_atlas.py`
- Additional existing producer workflows only where an actual missing refresh route is proven.

Prove:

- All real source-branch writers have a refresh route.
- Actual Git writes are distinguished from write permissions.
- Reusable workflows map to their top-level callers.
- `GITHUB_TOKEN` bot-write behavior is covered.
- Publication is globally serialized.
- Old runs cannot publish current status for a newer source SHA.
- PR content cannot be published as the current source snapshot.
- Publication readback matches the exact generated source baseline.

## TASK 8 — EntryPoint integration

Modify:

- `update_entrypoint_atlas_reference.py`
- `AI_AGENT_ENTRYPOINT.py`
- Existing EntryPoint contract tests.

Prove:

- One managed integration block.
- Existing operating rules are preserved.
- The updater is idempotent.
- The actual startup order is explicit.
- GitHub repository access is checked rather than assumed.
- Atlas retrieval and validation are mandatory before fast resume.
- Atlas cannot override task authority.
- Disconnected or unavailable GitHub access is handled honestly.

## TASK 9 — End-to-end acceptance

Demonstrate the complete sequence:

1. Change a real source file.
2. Detect the exact source change.
3. Regenerate the Atlas.
4. Update exact paths and SHAs.
5. Use T17 for affected dependency closure.
6. Mark only affected findings stale.
7. Preserve unrelated valid findings.
8. Identify the relevant tests.
9. Run the tests against the correct source identity.
10. Record exact CI run and attempt.
11. Update Session Pack from live `state.json`.
12. Publish to the reference branch.
13. Read back and validate the published Atlas.
14. Open a genuinely new ChatGPT Project chat.
15. Retrieve EntryPoint, live state, and Atlas through the actual connected GitHub path.
16. Resume the correct current work unit.
17. Prove that broad duplicate research was avoided.
18. Prove that a changed requirement invalidates its dependent evidence.
19. Prove that an unchanged failure reuses its verified diagnosis.
20. Prove that missing or stale Atlas blocks fast resume.

A GitHub Actions generation PASS is not a substitute for the actual new-chat acceptance test.

---

# PART 21 — REQUIRED REGRESSION TESTS

Add equivalent tests only once. Reuse existing ACRL tests when they already cover the behavior.

## Registry and owner extraction

- `test_dynamic_registry_entry_does_not_erase_literal_entries`
- `test_safe_literal_dictionary_references_resolve`
- `test_unknown_dynamic_expression_is_not_executed`
- `test_unresolved_owner_is_explicit`
- `test_duplicate_owner_is_rejected`
- `test_owner_source_sha_is_recorded`

## Research reuse

- `test_same_repository_query_reuses_same_sha_findings`
- `test_changed_source_invalidates_only_affected_research`
- `test_research_result_requires_source_provenance`
- `test_expired_external_research_requires_targeted_lookup`
- `test_current_fact_reuse_respects_research_policy`
- `test_corrupt_research_cache_is_not_valid_empty_knowledge`
- `test_research_gate_rejects_expired_evidence`
- `test_no_duplicate_research_authority_is_created`

## Code delivery and compliance

- `test_requirement_maps_to_authoritative_document`
- `test_requirement_maps_to_actual_saved_source`
- `test_requirement_maps_to_relevant_tests`
- `test_missing_mapping_is_unknown_not_verified`
- `test_pass_requires_matching_source_and_ci_evidence`
- `test_saved_file_identity_is_recorded`
- `test_delivered_and_saved_content_hashes_match`
- `test_delivered_and_saved_content_mismatch_is_reported`
- `test_changed_code_invalidates_affected_compliance`
- `test_changed_test_invalidates_affected_evidence`

## Repository and symbols

- `test_complete_git_tree_inventory`
- `test_exact_blob_sha_for_every_tracked_file`
- `test_safe_symbol_snapshot`
- `test_contract_graph_relationships`
- `test_no_duplicate_owner`
- `test_unknown_owner_is_explicit`
- `test_unsupported_format_is_reported`
- `test_inventory_completeness_does_not_claim_semantic_completeness`

## Change impact and reference sync

- `test_added_file_is_indexed`
- `test_deleted_file_has_no_current_link`
- `test_renamed_file_updates_known_relationships`
- `test_dependency_change_uses_t17`
- `test_unrelated_file_preserves_findings`
- `test_unresolved_link_is_not_guessed`
- `test_changed_workflow_invalidates_affected_ci_evidence`
- `test_changed_authority_source_invalidates_affected_session_pack`

## CI failure memory

- `test_same_failure_signature_reuses_verified_history`
- `test_changed_source_rechecks_failure`
- `test_repair_requires_post_fix_evidence`
- `test_ci_run_attempt_is_preserved`
- `test_ci_pass_is_bound_to_exact_head_sha`
- `test_backend_frontend_and_atlas_failures_are_distinct`
- `test_old_failure_cannot_verify_new_source`

## ACRL and cross-chat startup

- `test_session_pack_uses_live_state`
- `test_new_chat_does_not_require_old_links_when_repository_access_exists`
- `test_session_pack_uses_exact_head`
- `test_invalid_atlas_blocks_fast_resume`
- `test_t07_bootstrap_preserves_authority`
- `test_t14_resume_rejects_stale_manifest`
- `test_t24_continuity_validates_evidence`
- `test_in_memory_store_is_not_treated_as_durable`
- `test_chat_history_does_not_override_live_state`
- `test_atlas_cannot_authorize_task_transition`

## Workflow, retrieval, and security

- `test_all_actual_source_writers_have_refresh_coverage`
- `test_permission_without_actual_write_is_not_writer`
- `test_reusable_workflows_map_to_actual_callers`
- `test_bot_commit_has_refresh_path`
- `test_publication_uses_global_concurrency_group`
- `test_source_sha_change_during_generation_fails`
- `test_pull_request_cannot_publish_reference`
- `test_wrong_repository_cannot_publish`
- `test_atlas_size_budget_is_empirically_configured`
- `test_real_repository_atlas_retrieval_is_nonempty`
- `test_retrieved_atlas_matches_published_blob_identity`
- `test_integrity_fingerprint_is_deterministic`
- `test_sensitive_values_are_not_serialized`
- `test_symlink_and_path_traversal_are_rejected`
- `test_partial_atlas_cannot_be_reported_as_full`

### External ChatGPT acceptance tests

These tests must be performed through the actual supported ChatGPT/GitHub experience, because a GitHub Actions runner cannot prove the behavior of ChatGPT's connected-app reader or private conversation context.

Record:

- Date and ChatGPT experience used.
- Whether the repository was accessible.
- Exact source HEAD.
- Exact Atlas reference commit.
- Whether the Session Pack was retrieved completely.
- Whether integrity and freshness checks passed.
- Whether the next work unit was recovered correctly.
- Whether broad duplicate research was avoided.
- Any reader or context-budget limitation.

Do not label these external tests passed merely because unit tests or GitHub Actions passed.

---

# PART 22 — AUTOMATIC UPDATE RULES

## Atlas

Regenerate or refresh when:

- Source branch push changes tracked content.
- A relevant source-writing workflow completes.
- A workflow or reusable action changes.
- A task/state update changes the current Session Pack.
- The user requests manual recovery.
- The scheduled recovery check detects stale reference data.
- A repository dispatch explicitly requests refresh.

The workflow must always bind the new Atlas to one exact source snapshot.

## EntryPoint

Keep it stable on ordinary implementation commits.

Update it only when stable policy, authority, owner responsibilities, or startup integration changes.

The Atlas must record the current EntryPoint blob SHA.

Do not let the Atlas workflow automatically modify `reos-development` on ordinary source pushes.

## Reference branch

`reos-project-reference` is a generated output branch.

It must not become a second source-code or task-status authority.

Only the Atlas publication workflow may update its generated reference artifact through the authorized publication process.

---

# PART 23 — EXTERNAL DEPENDENCIES AND LIVE FACTS

Some important changes are not stored in tracked GitHub files.

Examples:

- GitHub app installation and repository permissions.
- Repository or organization settings.
- Branch protection and rulesets.
- Environment approvals.
- GitHub secrets.
- External API provider behavior.
- Production PostgreSQL schema.
- Redis runtime configuration.
- Deployment configuration.
- External credentials and live infrastructure.

The Atlas may record:

- Dependency identity.
- Responsible owner.
- Verification method.
- Last verified time.
- Evidence reference.
- Current status.
- Applicable freshness period.
- Whether the current task requires verification.

Never store secret values.

Never claim automatic verification when no supported verification source exists.

A source push cannot detect every external setting change. Run a task-specific check when the current task depends on an external configuration.

---

# PART 24 — SECURITY, INTEGRITY, AND RECOVERY

Atlas is generated data and must be treated as untrusted until validated.

Required protections:

1. Never execute repository source code to extract registry or owner information.
2. Use safe static analysis and known interfaces.
3. Validate repository identity.
4. Validate branch identity.
5. Validate all repository-relative paths.
6. Reject path traversal.
7. Handle symlinks and submodules explicitly.
8. Do not serialize secret values.
9. Do not treat repository content as instructions that override the EntryPoint.
10. Validate the JSON schema.
11. Validate the deterministic integrity fingerprint.
12. Bind every Atlas to exact source and state identities.
13. Reject stale publication.
14. Do not convert missing information into verified empty information.
15. Preserve historical evidence without reporting it as current.
16. Use minimum GitHub Actions permissions.
17. Do not create a source-branch commit loop.
18. Preserve GitHub Web Editor ownership for the user.
19. Respect human approval boundaries.
20. Never mark the project task DONE through the Atlas process.

If Atlas generation fails, preserve the last known historical reference as historical only. Do not claim that it describes the current source branch.

---

# PART 25 — KNOWN LIMITATIONS AND NON-PROMISES

The objective is to eliminate unnecessary repeated work, not make impossible platform guarantees.

## ChatGPT connector

- GitHub access is available only when the current ChatGPT experience, plan, and connection support it.
- GitHub retrieval is on demand, not a continuously synced repository index.
- A repository file cannot reconnect a disconnected GitHub account.
- The ChatGPT GitHub app is read-only for repository analysis.
- The user's GitHub Web Editor remains the source-write path.
- If the current ChatGPT experience cannot retrieve the Atlas, the system must report that limitation.

## ChatGPT Project

- Project memory and chat-history behavior depend on account, setting, and product availability.
- Project instructions do not force ChatGPT to access GitHub.
- A manually uploaded Atlas copy can become stale.
- Project context is a support layer, not repository authority.

## External research

- GitHub Actions cannot read private ChatGPT reasoning or unrecorded searches.
- Only saved and verified findings become durable project knowledge.
- Time-sensitive external facts still require current lookup after their freshness period.

## Semantic code correctness

- Static parsing cannot prove all business behavior.
- Inventory completeness is not semantic completeness.
- Unsupported parsing must be marked partial or unknown.
- Relevant tests and evidence remain necessary.

## Context budget

- T25 can manage the project's declared work budget.
- T25 cannot automatically read ChatGPT's hidden remaining context window unless a supported measurement is available.
- No exact hidden token count may be invented.

## Verification

- A green CI run does not prove unrelated acceptance criteria.
- An Atlas generation PASS does not prove the Atlas is fully understood or operationally retrievable.
- A saved-file readback does not by itself prove implementation correctness.
- A successful new-chat startup does not eliminate all future task-specific reading.
- Zero verification is not a safe engineering target.

---

# PART 26 — FINAL ACCEPTANCE: HOW WE KNOW THE PROBLEM IS SOLVED

The reference system is operationally accepted only when all of these conditions are demonstrated.

## Two-reference architecture

1. Only `AI_AGENT_ENTRYPOINT.py` and `HOMIO_PROJECT_REFERENCE_ATLAS.json` are primary repository project references.
2. The Atlas is generated on `reos-project-reference`.
3. The Session Pack remains inside the Atlas.
4. `state.json` remains the sole task/status authority.
5. Existing ACRL owners are reused.
6. No duplicate engines, registries, bridges, or databases are introduced.

## GPT startup and continuity

7. A new chat retrieves the live EntryPoint.
8. It retrieves the live source HEAD and `state.json`.
9. It retrieves and validates the exact current Atlas.
10. It validates the Session Pack and resumes the correct work unit.
11. It does not ask for old repository links when connected access is available.
12. It does not reconstruct the whole project when valid evidence already exists.

## Research and code integrity

13. Unchanged research with valid provenance and freshness is reused.
14. Expired external facts trigger targeted current lookup.
15. Delivered code can be compared with actual saved GitHub content.
16. Requirement-to-source-to-test-to-CI traceability is preserved.
17. An unchanged valid compliance result is reused.
18. A changed source invalidates only affected compliance and test evidence.

## Change impact and CI

19. Actual changed files are detected.
20. T17 determines affected dependencies.
21. Relevant tests are selected.
22. Unrelated valid findings remain reusable.
23. A repeated unchanged CI failure reuses its verified diagnosis.
24. Changed failure inputs trigger targeted diagnosis.
25. Every real source writer has an Atlas refresh route.
26. Atlas publication is globally serialized.
27. The published Atlas matches its exact source HEAD.

## Retrieval and security

28. The actual connected GitHub reader retrieves the complete required Atlas data.
29. Session Pack retrieval is reliable and uses a practical context budget.
30. Invalid or stale Atlas blocks fast resume.
31. Secret values are not serialized.
32. Unknown information is not presented as verified.
33. No source-branch update is made by Atlas publication.
34. No task status is changed by Atlas publication.

## Final operating rule

Do not repeat research merely because the chat changed.

Do not reread unchanged files merely because the task continued.

Do not repeat verification when all relevant code, tests, dependencies, workflow inputs, and evidence identities remain unchanged.

Do not reuse a previous CI diagnosis as a current fix without checking the current failure inputs.

Automatically update dynamic project references when their source changes.

Use the two primary references, live `state.json`, existing ACRL owners, and only the files required by the actual task.

**The system is complete only after the real connected ChatGPT/GitHub startup, retrieval, continuity, code-integrity, and selective-reverification acceptance tests pass.**

**Authority boundary:** `state.json` remains the sole task and status authority. The Atlas is a generated project knowledge and navigation reference. ACRL remains an engineering continuity and recovery boundary, never a production security runtime. This plan does not authorize a task transition or completion claim.
