# HOMIO / REOS — 360° Gap Closure & Production Readiness Execution Structure

**Document ID:** `HOMIO-G360-EXECUTION-001`  
**Revision:** `2.1 — Scope, Ownership & Evidence Reconciliation`  
**Status:** SUPPORTING IMPLEMENTATION PLAN — NOT EXECUTION AUTHORITY  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical branch:** `reos-development`  
**Canonical path:** `REOS_CONTROL_CENTER/architecture/HOMIO_360_DEGREE_GAP_CLOSURE_EXECUTION_STRUCTURE.md`  
**Review date:** 2026-10-29

**Purpose:** Maintain one reliable, duplicate-resistant, dependency-aware plan for identifying and closing HOMIO / REOS's real integration, autonomy, security, reliability and production-readiness gaps. This plan must work with the existing Control Center, approved architecture, domain owners, ACRL, frontend execution and GitHub Actions. It must never replace them.

---

## 1. Mission and engineering outcome

HOMIO / REOS aims to become a world-class real-estate platform with reliable AI capabilities and carefully governed autonomous operations.

Success is not measured by the number of AI modules, documentation files or passing synthetic tests. Success means that real requirements are handled correctly, authorized actions remain controlled, business data remains authoritative, failures are recoverable and the resulting behavior can be independently verified.

The required outcome is a platform that can:

1. Translate supported property requirements into validated canonical search criteria.
2. Retrieve current, authorized and traceable property/business evidence.
3. Answer with accurate claims, useful uncertainty handling and source provenance.
4. Integrate customer-facing AI through an approved server-side boundary.
5. Use existing identity, tenancy, search, inventory, lead, deal, financial and governance owners rather than reproducing their business logic.
6. Plan and execute permitted work through existing authorized execution paths.
7. Persist and verify execution outcomes where the approved architecture requires it.
8. Recover from interruption, timeout, retry and partial failure without unsafe repeated side effects.
9. Measure quality, safety, cost, latency, reliability and business outcomes against approved requirements.
10. Preserve auditability and continuity without treating conversation history as live project authority.
11. Meet release criteria using exact source revisions, applicable tests, operational evidence and required approvals.
12. Support Pune-first customer needs without permanently hardcoding Pune-specific behavior into international product architecture.

**Core engineering principle:** Existing capability must be integrated and verified before new capability is added. An implementation, plan, test fixture or successful CI run is not by itself proof of end-to-end production behavior.

---

## 2. Authority, scope and non-negotiable rules

### 2.1 Authority hierarchy

| Concern | Existing authoritative owner |
|---|---|
| Current gate, task, subtask and acceptance criteria | `REOS_CONTROL_CENTER/data/state.json` and the existing Control Center |
| Committed implementation and source history | GitHub `reos-development` |
| Development-agent operating contract | `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py` |
| Task selection and formal transitions | Existing REOS Control Center process |
| AI platform implementation requirements | `REOS_CONTROL_CENTER/architecture/AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md` |
| Identity, tenancy and domain authorization | Existing CORE-001 and authorization owners |
| Leads and ownership attribution | CORE-003 |
| Inventory truth | CORE-004 |
| Search and matching | CORE-005 |
| Deals and transactions | CORE-006 |
| Trust, fraud and governance | CORE-007 |
| Financial and commission truth | CORE-008 |
| Development-agent continuity, recovery and repository coordination | Existing ACRL and `AI_AGENT_ENTRYPOINT.py` |
| Customer-facing UI and design system | Existing frontend/F-layer files and the approved frontend execution plan |
| AI quality and production-readiness evidence | Existing AI-001 evidence records, including Sections 14 and 19 |
| Security-reference mapping and implementation rules | Existing AI-001 evidence records, including Sections 20 and 21 |
| Regression, build and integration evidence | Existing backend/frontend GitHub Actions workflows |
| This document | Cross-domain gap register and supporting execution reference only |

### 2.2 Non-negotiable rules

- Never edit `state.json` manually to create progress, a new task, a completion record or an approval.
- Never let this plan choose the next authorized task.
- Never treat a historical chat, remembered SHA, old test count or a Markdown plan as current execution authority.
- Never reopen or reverse an approved gate merely to accommodate additional follow-up work.
- Never confuse formal AI-001 approval with approval for customer-facing production enablement.
- Never create a second identity system, tenant registry, business-data store, search engine, agent executor, state store, memory system, evidence service or recovery engine without a proven architectural need and appropriate authorization.
- Never add a new server, API boundary, provider adapter, verifier, test framework or workflow before checking whether the existing owner can satisfy the requirement.
- Never delete a file merely because its filename resembles another file.
- Never accept model-generated permission claims, success messages, receipts or business facts as authoritative without validation.
- Never expose secrets, unnecessary customer prompts, private listing data or unredacted sensitive errors.
- Never equate green CI with complete security, production deployment, customer quality or release approval.
- Never change frozen architecture or silently reorder canonical tasks.
- Preserve successful regressions while adding focused negative, failure and integration coverage.
- If a required change is outside the currently authorized task, record the finding and route it through the existing change-control process.
- Never claim that a file was saved or verified without confirming the actual GitHub result.

### 2.3 Scope of this review session

The active task observed in canonical state is:

`APP-001-T01 — Implement application shell and design system.`

The frontend owner is working on this task in a separate chat.

**Scope boundary for this chat:**

- Audit and improve this 360° supporting plan.
- Reconcile its references, identifiers, dependencies and evidence rules.
- Do not edit frontend source files.
- Do not create or replace frontend CSS, design tokens, components, navigation, pages, verifiers or tests.
- Do not repeat work already done on the Rosewood & Almond design system.
- Do not run parallel implementation of APP-001-T01.
- Do not alter canonical state or claim a formal task transition.
- Do not start a new backend/AI implementation merely because this plan identifies a possible gap.

A follow-up can be assigned to the correct existing owner only when the canonical execution process or an applicable authorized change request permits it.

---

## 3. Audited repository baseline and its limitations

This is a dated observation, not a permanent live-status cache. Revalidate it before any implementation batch.

| Item | Verified observation |
|---|---|
| Repository | `prajaktaranjane80-sketch/Homio` |
| Branch | `reos-development` |
| HEAD observed during this review | `bbb62bbfdddb95578b89133d0f43f7684febdb65` |
| Existing 360° structure path | `REOS_CONTROL_CENTER/architecture/HOMIO_360_DEGREE_GAP_CLOSURE_EXECUTION_STRUCTURE.md` |
| Existing 360° structure blob at review | `8e22b4bace4dac4a9bd254636ca52f7f209948ff` |
| Canonical state blob | `6242f63371a725ea99447c218bbbeb46a0c5eddd` |
| Canonical state metadata timestamp | `2026-10-27T09:12:50+00:00` |
| Current task in state | `APP-001-T01` |
| Current gate | `APP-001` |
| AI-001 formal status | `APPROVED` |
| AI-001 subtasks | T01–T10 recorded as `DONE` |
| AI-001 acceptance criteria | AC01–AC06 recorded as `VERIFIED` |
| Current work of this chat | Supporting-plan audit/revision only |

### 3.1 AI-001 formal status does not prove production readiness

The canonical state records the AI-001 gate as approved. Its verified criteria cover the implementation-gate scope and include provider abstraction, authorization, retrieval, cost-control configuration, authorized tool boundaries, fallback and observability behavior.

That formal outcome must be preserved. Additional integration, deployment, operational or production-quality work must be mapped to the correct existing or future authorized scope instead of reopening AI-001 without an approved reason.

### 3.2 GitHub Actions evidence must be bound to the tested source

The latest backend/ACRL workflow observed in the branch run listing during this audit was:

- Run: `40898104151`
- Workflow: `HOMIO Backend and ACRL Runtime CI`
- Tested commit: `8bfbcee9d618a720885c6339063bbeb01cd2851e`
- Result: `success`
- URL: https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40898104151

The current document review observed a newer documentation revision than that tested commit. This audit does not claim that a frontend workflow or every check ran against the exact HEAD observed above.

A successful backend workflow establishes only the checks actually performed against its tested revision. It does not establish that the frontend was visually reviewed, production infrastructure was tested or customer-facing AI was approved for live enablement.

### 3.3 The current Section 14 evidence needs reconciliation

The live file:

`REOS_CONTROL_CENTER/evidence/AI-001/section-14-operational-readiness.md`

has blob SHA:

`76c42afd96ad5bf11029ab1dd8fe9a48a3357ba1`

It still records backend Run #547 at tested commit `ee86056a55a94416bfa62cb4da4ed3b512278e52`, with nine synthetic cases passed and one blocked. It explicitly records `release_ready=False`.

Later Section 19 and Section 21 evidence records refer to newer successful runs and synthetic evaluation results. The old chat history also refers to Run #562, which passed ten synthetic cases with none blocked while `release_ready` remained false.

These records must not be silently treated as one identical, current evaluation.

Required reconciliation:

1. Inspect the actual latest applicable Actions logs and sanitized artifacts.
2. Establish which evaluation result corresponds to which tested commit.
3. Update the existing Section 14 record through its authorized evidence workflow.
4. Preserve prior results as dated history; do not erase a blocked result.
5. Keep the production-readiness decision separate from synthetic case counts.

This plan does not change those evidence records or declare production readiness.

### 3.4 GitHub governance observation

The branch metadata observed during this audit reported `protected=false` for `reos-development`.

This is a governance risk to revalidate, not permission to change repository settings in this work session. The existing governance owner must inspect applicable branch protection/rulesets, required-check policy and permissions before proposing a controlled change.

---

## 4. Duplicate and plan-ownership audit

### 4.1 Existing standalone document

The live repository tree contains the current standalone document at:

`REOS_CONTROL_CENTER/architecture/HOMIO_360_DEGREE_GAP_CLOSURE_EXECUTION_STRUCTURE.md`

The repository-tree review did not identify another standalone file with the old proposed name:

`REOS_CONTROL_CENTER/architecture/HOMIO_AI_AUTONOMY_360_DEGREE_GAP_CLOSURE_STRUCTURE.md`

However, an earlier draft of a 360° AI/autonomy structure is embedded in:

`REOS_CONTROL_CENTER/old chat histry`

That historical draft is context, not a second standalone canonical file. It must not be followed as an independent active plan.

### 4.2 Confirmed gap-ID collision

The older embedded draft used IDs such as `G360-00`, `G360-01`, and so on. The current standalone document also uses `G360-01` through `G360-17`, but assigns different meanings to those identifiers.

For example, the old draft used `G360-01` for structured real-estate search. The newer document uses `G360-01` for the customer-facing AI service boundary.

This is a real traceability defect: the same identifier can point to different findings when history is searched or work is handed to another chat.

**Resolution:** This revision uses `H360-00` and `H360-01` through `H360-17` for its internal workstream register. Existing `APP-001-Txx`, `CORE-00x`, `AI-001-Txx`, ACRL task IDs and all canonical project identifiers remain unchanged.

The old `G360-*` labels appearing in historical chat content are historical labels only. Do not create or rename files merely to preserve the old label sequence.

### 4.3 Existing plans are not to be duplicated

| Existing reference | Proper use |
|---|---|
| `AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md` | AI design, package responsibilities and implementation requirements |
| `HOMIO_FRONTEND_MASTER_EXECUTION_PLAN.md` | Frontend ownership, design system, UX, security and frontend verification |
| `new chat work reference` | Frontend-specific continuation context; revalidate its instructions against canonical state |
| `old chat histry` | Historical context and findings; not a live task authority |
| `HOMIO_REOS_FIX_EXECUTION_STRUCTURE` | Older supporting execution document; its historical task claims are not current authority |
| `evidence/AI-001/section-14-operational-readiness.md` | Existing quality and operational readiness record |
| `evidence/AI-001/section-19-definition-of-done-verification-matrix.md` | Existing definition-of-done/evidence reconciliation |
| `evidence/AI-001/section-20-external-security-risk-reference-audit.md` | Existing external security reference and risk mapping |
| `evidence/AI-001/section-21-final-implementation-rules-audit.md` | Existing implementation and handoff rules |
| `data/state.json` and existing Control Center | Authoritative task selection and transition |

Do not create a new master plan, audit platform, release tracker, state file, memory engine or evidence registry to mirror these sources.

---

## 5. Finding classification and evidence rules

Every workstream requires a current classification. Historical findings are starting points only.

Use these statuses:

- **CONFIRMED_GAP:** The required behavior is absent or a reproducible requirement fails in the reviewed scope.
- **PARTIAL:** Relevant implementation exists, but an integration, lifecycle, scope or acceptance requirement remains incomplete.
- **UPDATE_REQUIRED:** Existing documentation, evidence or configuration is demonstrably stale or inconsistent.
- **UNVERIFIED:** Available source evidence cannot establish the current behavior or deployment state.
- **VERIFIED_SOURCE_TEST:** The specified behavior has passed relevant tests on the recorded revision within the stated scope.
- **VERIFIED_PRODUCTION:** The required production behavior and operational controls have been independently verified against the applicable release criteria.
- **REUSE_COVERED:** An existing owner satisfies the named requirement within the stated evidence scope.
- **DUPLICATE_CANDIDATE:** Similar ownership is suspected; behavioral and dependency proof is required before removal.
- **BLOCKED:** A required contract, prerequisite, approval, environment or external dependency is unresolved.
- **DEFERRED_NOT_AUTHORIZED:** Work may be useful but is outside the currently authorized task.

`VERIFIED_SOURCE_TEST` is not equivalent to `VERIFIED_PRODUCTION`.

### 5.1 Mandatory finding record

Every finding that advances beyond a historical note must record the following using the existing authorized task/evidence mechanism:

| Field | Required information |
|---|---|
| Workstream ID | `H360-xx` |
| Canonical task | Current gate/task/subtask read from live state |
| Review timestamp | Date and time of the inspection |
| Repository revision | Exact commit SHA inspected |
| State reference | State blob SHA and current task |
| Classification | One of the statuses above |
| Existing owner | Module, contract or workflow already responsible |
| Exact references | Paths, public symbols, callers and tests |
| Actual behavior | Reproducible observation or identified missing contract |
| Proposed change | Minimum change needed to satisfy the requirement |
| Change class | `REUSE`, `UPDATE`, `ADD`, `REMOVE`, `DEFER` or `NO_CHANGE` |
| Dependencies | Contracts, tasks and approvals required first |
| Security/privacy impact | Trust boundaries and abuse scenarios affected |
| Acceptance criteria | Objective, observable pass/fail behavior |
| Verification | Focused and regression test evidence |
| CI evidence | Run ID, workflow, conclusion and exact tested SHA |
| Production evidence | Environment, monitoring, release controls and approval where applicable |
| Residual risk | Unresolved limitations |
| Final status | Changed only through the applicable authorized process |

Do not invent missing evidence or fill unknown values from memory.

---

## 6. Master workstream register

The workstream IDs in this section are for traceability within this document. They are not canonical Control Center tasks.

The initial classifications below are provisional where noted. They must be revalidated before implementation.

### H360-00 — Live baseline, ownership and change-control reconciliation

**Priority:** Critical  
**Initial status:** UPDATE_REQUIRED / repeat before implementation  
**Existing owners:** `state.json`, `AI_AGENT_ENTRYPOINT.py`, existing Control Center, ACRL and Actions workflows.

**Required work**

1. Read current branch HEAD and canonical `state.json`.
2. Confirm current task, acceptance criteria, prior unfinished subtasks and declared dependencies.
3. Re-read relevant architecture, implementation and test files.
4. Map every finding to an existing owner.
5. Identify active work in another chat or workstream before planning a conflicting change.
6. Confirm current CI evidence and the exact source revision each run tested.
7. Separate missing source implementation from unverified deployment behavior.
8. Record `REUSE`, `UPDATE`, `ADD`, `REMOVE`, `DEFER` or `NO_CHANGE` for each candidate path.
9. Preserve old audit evidence while marking it historical if superseded.
10. Read the saved file back from GitHub after any user-applied replacement.

**Acceptance**

Another development session can reconstruct the current task, source revision, relevant owners, proven findings, open blockers and next authorized action without relying on an old chat.

**Prohibited:** A second controller, state store, history engine, audit database or competing resume manifest.

### H360-01 — Canonical real-estate search and structured criteria

**Priority:** Critical  
**Initial status:** PARTIAL / revalidate against current CORE-005

**Existing owners to inspect**

- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/search_filters.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/search_domain.py`
- Existing search execution, request and index contracts.
- CORE-004 inventory fields and projections.
- Existing CORE-005 matching/search tests.
- Existing F03 search API contracts, through their owner.

**Required behavior**

Supported natural-language property requirements must become validated search criteria that the canonical search owner understands. Depending on the approved domain contract, supported criteria may include locality, property type, bedroom/BHK configuration, budget/price, area, transaction type, availability and proximity.

**Important evidence distinction**

The existing Section 14 record reported that canonical structured fields for bedrooms, budget/price, location and transit proximity were missing in the reviewed contract. Later synthetic evaluation evidence demonstrated safe handling of unsupported criteria. Safe refusal or faithful pass-through of free text does not, by itself, establish that the complete structured-search capability has been implemented.

**Acceptance**

- Every supported field maps to a canonical typed contract.
- Unsupported fields are never silently dropped or guessed.
- Contradictory requirements produce deterministic clarification or rejection behavior.
- Tenant context is trusted and established server-side.
- Units and currency conversions are deterministic and tested.
- Search executes through the canonical CORE-005 owner.
- Results respect approved criteria and tenant boundaries.
- No second property-search engine or parallel search truth is created.

### H360-02 — Authenticated customer-facing AI service boundary

**Priority:** Critical  
**Initial status:** PARTIAL / UNVERIFIED end-to-end production connection

**Existing owners to inspect**

- `AUTONOMY_ENGINE/ai_platform/server_composition.py`
- `model_gateway.py`
- `authorization.py`
- `rag_pipeline.py`
- Existing frontend F08 route/service contracts.
- Existing approved server/API and identity boundaries.
- Existing provider configuration and error-mapping interfaces.

**Required work**

Prove the real request path from an authorized customer request to an approved server boundary, trusted identity/tenant context, existing AI composition, retrieval/policy handling and a validated response.

Before introducing any endpoint or server, resolve the runtime/integration contract against the approved technology stack and existing hosting/deployment structure. Historical planning identified a possible boundary between the approved backend stack and the existing Python AI package; this must be verified against current architecture, not solved through an unapproved parallel backend.

**Acceptance**

- Protected AI functions cannot be called without the required trusted identity and policy context.
- Tenant identity is not trusted merely because it appears in client data or model output.
- Request size, schema, timeout, cancellation and error behavior are bounded.
- Secrets stay server-side.
- Provider errors and malformed outputs produce safe, defined responses.
- Integration tests exercise the actual approved composition and route boundary.
- Live status is not enabled until the approved end-to-end path and release conditions pass.

### H360-03 — Evidence-grounded answers and retrieval integrity

**Priority:** High  
**Initial status:** PARTIAL; verify scope and production integration

**Existing owners**

- `AUTONOMY_ENGINE/ai_platform/rag_pipeline.py`
- `retrieval_adapter.py`
- CORE-005 retrieval and indexing owners.
- Existing response-validation and provenance contracts.

**Acceptance**

- Listing-specific claims can be traced to authoritative records.
- Tenant, source, version and freshness checks are enforced.
- Conflicting or incomplete source records are explicitly qualified.
- Invalid, fabricated or mismatched citations are rejected.
- Prompt injection in retrieved or user-supplied content cannot grant authority.
- Insufficient evidence results in clarification, qualification or refusal rather than invented facts.
- Retrieval quality and citation correctness are measured on a versioned representative set.
- No duplicate RAG pipeline or vector-index owner is added.

### H360-04 — Customer conversation context, privacy and feedback

**Priority:** High  
**Initial status:** UNVERIFIED / defer persistence design until owner and need are established

Customer conversation context is distinct from ACRL project continuity.

Before any implementation, establish the business purpose and retention requirements. Inspect existing identity, data ownership, consent and storage contracts.

**Acceptance**

- Customer context cannot cross identity or tenant boundaries.
- Only approved, necessary information is persisted.
- Access, correction, deletion and retention behavior is defined and testable where required.
- Conversation facts are not silently promoted to trusted business truth.
- Feedback is recorded through an approved mechanism with explicit access and retention controls.
- Any proposed persistence reuses existing authorized storage and event owners where possible.

**Prohibited:** Creating another customer-memory or project-memory service merely because a new architecture diagram suggests one.

### H360-05 — Pune-first domain and multilingual quality

**Priority:** High  
**Initial status:** UNVERIFIED against an approved benchmark

Create a representative, versioned evaluation set for the supported English, Hindi and Marathi property-request patterns.

Cover practical queries involving Pune localities, BHK, rentals, sale, price ranges, lakhs/crores, area units, locality spelling variations, proximity and ambiguous requirements.

**Acceptance**

- Every supported interpretation has an expected structured output.
- Unsupported claims and missing inventory are handled honestly.
- Unit conversion and locality matching have deterministic regressions.
- Multilingual quality has an approved measurement method and release threshold.
- Tests do not use unauthorized customer data.
- Model-dependent results are tied to the model/configuration and source revision.

Do not claim a percentage accuracy or quality SLA until a threshold is formally approved and measured.

### H360-06 — Governed autonomous planning and orchestration

**Priority:** Critical for autonomous capabilities  
**Initial status:** PARTIAL / revalidate the complete lifecycle

**Existing owners**

- Existing agent runtime and tool bridge.
- Existing execution gateway and policy/authorization owners.
- Existing approval, preflight and evidence mechanisms.
- Existing ACRL and Control Center contracts.

**Required lifecycle**

1. Receive a bounded, authorized objective.
2. Establish trusted identity, scope and constraints.
3. Inspect relevant project/business context.
4. Produce a typed, bounded plan.
5. Check dependencies, policy and risk.
6. Request approval when required.
7. Execute only through the existing authorized tool boundary.
8. Validate the actual resulting state.
9. Record evidence and execution outcome.
10. Stop, recover or request human intervention if an invariant fails.

**Acceptance**

- Model-generated plans cannot authorize themselves.
- Untrusted text cannot modify trusted execution scope.
- Tool arguments and results are validated.
- High-risk actions remain behind required approval gates.
- Partial completion and denial are distinguishable from success.
- Completion reports agree with authoritative execution evidence.
- Tests cover denial, interruption, malformed outputs and unsafe requests.

### H360-07 — Durable execution, idempotency, checkpoints and recovery

**Priority:** Critical  
**Initial status:** PARTIAL / current cross-component lifecycle not established by a plan alone

Inspect the existing execution store, run/action identity, checkpoint, receipts and ACRL recovery pathways before making changes.

**Acceptance**

- Runs and actions have traceable identities.
- Safe checkpoints can be resumed under defined conditions.
- Duplicate requests do not duplicate unsafe business side effects.
- Retry behavior is bounded and tested under concurrent conditions.
- Irreversible actions are not blindly replayed after ambiguous outcomes.
- Recovery does not convert stale or conflicting evidence into success.
- An execution receipt agrees with the authoritative resulting state.
- Tests exercise process restart, duplicate request, partial completion and ambiguous-result scenarios.

### H360-08 — Authorization, tenant isolation and action governance

**Priority:** Critical  
**Initial status:** VERIFIED_SOURCE_TEST for some reviewed controls; production integration remains separately unverified

**Existing owners**

- CORE-001 identity and tenant membership.
- Existing authorization and domain policy owners.
- Existing `ai_platform/authorization.py`.
- Existing execution/tool gateway and approval controls.

**Acceptance**

- Every protected operation is authorized on the server.
- Cross-tenant reads, writes, retrieval and caches are covered by relevant tests.
- Client data and model output cannot grant privileges.
- Sensitive actions use the designated authorization and approval path.
- Replay and privilege-escalation cases are tested.
- Denial and policy errors are observable without leaking secrets or private records.
- Production configuration and deployment behavior have separate evidence from source-level tests.

### H360-09 — Provider/model reliability and failure handling

**Priority:** High  
**Initial status:** PARTIAL / test and deployment scope must be separated

Reuse the existing model gateway, model registry, provider adapters and fallback rules.

**Acceptance**

- Provider and model configuration is validated.
- Capability constraints are preserved during model selection.
- Timeouts, rate limits, unavailable providers and malformed responses have defined outcomes.
- Retries cannot cause unbounded cost or duplicate business actions.
- Fallback behavior is explicit and does not silently violate constraints.
- Circuit breaking or similar resilience machinery is added only when a verified gap warrants it.
- Failure tests establish behavior for the selected configuration.
- No parallel provider router is created.

### H360-10 — Usage accounting, budgets, quotas and cost control

**Priority:** High  
**Initial status:** PARTIAL until production wiring is independently verified

**Existing owners**

- `AUTONOMY_ENGINE/ai_platform/cost_control.py`
- Existing usage/budget ports and transactional datastore contract.
- Existing model/pricing configuration.

**Acceptance**

- Usage is attributed to the correct tenant, operation and provider/model.
- Reservations and settlements are safe against duplicate events.
- Missing required pricing or budget context fails safely.
- Quotas remain correct under concurrent usage.
- Budget exhaustion has predictable behavior.
- Retry and fallback attempts are accounted for consistently.
- Multi-replica production operation uses the approved shared transactional store where required.
- Cost and usage telemetry avoids unnecessarily recording sensitive prompts or secrets.

### H360-11 — Evaluation, benchmarks and adversarial testing

**Priority:** Critical for production readiness  
**Initial status:** UPDATE_REQUIRED / evidence reconciliation

**Existing owners**

- `AUTONOMY_ENGINE/ai_platform/tests/test_section14_quality_evaluation.py`
- `AUTONOMY_ENGINE/ai_platform/tests/fixtures/section14_quality_cases.json`
- Existing AI platform, domain and ACRL tests.
- `evidence/AI-001/section-14-operational-readiness.md`
- `evidence/AI-001/section-19-definition-of-done-verification-matrix.md`

**Required coverage**

- Structured property criteria and CORE-005 execution.
- Citation correctness, provenance and stale-source behavior.
- Unsupported-claim and insufficient-evidence behavior.
- English, Hindi and Marathi property interpretation.
- Tenant isolation and authorization.
- Tool-use safety, approval enforcement and recovery.
- Provider failures, usage limits and cost behavior.
- Regression cases for each previously observed defect.
- Relevant operational and deployment controls.

**Acceptance**

- Every metric has a documented method and approved threshold.
- Datasets are versioned and appropriately sanitized.
- Critical authorization or tenant leakage failures block release.
- Results identify the tested commit and relevant model/configuration.
- Synthetic tests are clearly distinguished from real-provider quality and production measurements.
- The existing Section 14 evidence record is reconciled with later actual evaluation evidence.
- `release_ready` remains false until the actual defined readiness conditions are satisfied.

**Prohibited:** Treating a higher passing-test count as proof of better customer outcomes or production readiness.

### H360-12 — Observability, incident handling and operational ownership

**Priority:** High  
**Initial status:** PARTIAL at source/test level; production operations UNVERIFIED

Reuse current telemetry, execution events and logging owners.

**Acceptance**

- Requests and execution runs have correlatable identifiers.
- Errors, latency, provider failures, usage and policy denials are observable.
- Log fields are bounded, redacted and access-controlled.
- Sensitive prompts and private data are not captured without an approved need.
- Alert ownership and escalation paths are documented.
- Runbooks cover provider outage, cost runaway, suspected tenant leakage and unsafe autonomous behavior.
- Production alert delivery, retention and access controls have environment-specific evidence.

### H360-13 — Deployment and production release readiness

**Priority:** Critical before live enablement  
**Initial status:** NOT VERIFIED / production enablement not approved by this plan

**Acceptance**

- Runtime configuration, secrets and permissions are reviewed.
- Dependency, artifact and supply-chain risks are assessed.
- Safe startup, shutdown and health checks are tested.
- Staging or equivalent verification covers the actual server/service boundary.
- Data/index/schema changes have compatibility and recovery plans.
- Rollback has been exercised against documented conditions.
- Retention, deletion, monitoring and data-residency requirements are addressed for the intended market.
- Availability/SLO and quality-release thresholds are approved and measured.
- The authorized release owner approves production enablement.

**Do not mark READY merely because the backend or frontend CI is green.**

### H360-14 — Real-estate business workflow integration

**Priority:** Critical  
**Initial status:** PARTIAL until relevant end-to-end workflows are verified

Reuse:

- CORE-003 for lead and attribution truth.
- CORE-004 for inventory truth.
- CORE-005 for search truth.
- CORE-006 for deals and transaction truth.
- CORE-007 for trust, fraud and governance.
- CORE-008 for financial and commission truth.

**Acceptance**

- AI and UI do not create parallel lead, inventory, search, deal or commission systems.
- Lead origin and ownership remain traceable.
- Sensitive business and financial changes follow existing policy.
- Provenance is maintained for important listing and lead claims.
- Authorized and rejected state transitions are tested.
- Important outcomes are recorded through the existing evidence mechanisms.
- API contracts are validated before dependent consumer behavior is changed.

### H360-15 — Development-agent continuity and audit integrity

**Priority:** High  
**Initial status:** UPDATE_REQUIRED / revalidate all cache and handoff claims

**Existing owners**

- `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py`
- ACRL T07, T14, T15, T18 and T20–T24 as applicable.
- Existing context/resume manifest.
- Existing Control Center and evidence-resolution mechanisms.

**Acceptance**

- New sessions identify current task and scope from live state.
- Historical notes are clearly marked as history.
- Handoffs preserve exact paths, source revisions, tests and blockers.
- A fast-resume decision is supported by valid existing evidence.
- If the changed-path delta or authority cannot be established, the prescribed full-audit or blocked path is followed.
- Stale CI results and old task identifiers never become current PASS.
- Recovery does not create a competing state or history system.
- A new chat cannot infer task authorization from this plan.

### H360-16 — GitHub governance and software supply-chain safety

**Priority:** Critical for protected release  
**Initial status:** UPDATE_REQUIRED / governance review needed

**Existing owners**

- Existing GitHub workflows and their reusable components.
- Repository branch protection/ruleset configuration.
- Existing dependency and security checks.

**Acceptance**

- Branch protection and repository rules are rechecked against the release policy.
- Required status checks are actually generated for the relevant changes.
- Workflow permissions follow least privilege.
- Third-party actions and dependencies are governed according to policy.
- Secrets are protected from untrusted pull-request code.
- Failed required checks cannot be bypassed through an undocumented process.
- Security-sensitive configuration changes are approved and auditable.

The observed `protected=false` status is a risk to review. This document does not authorize changing repository settings.

### H360-17 — Frontend/API contracts and customer experience

**Priority:** High  
**Initial status:** SPLIT — existing UI ownership, no frontend implementation in this chat

**Existing owners**

- `REOS_CONTROL_CENTER/Frontend`
- `REOS_CONTROL_CENTER/architecture/frontend/plans/HOMIO_FRONTEND_MASTER_EXECUTION_PLAN.md`
- Existing F-layer and route/API owners.
- `REOS_CONTROL_CENTER/new chat work reference`
- Current APP-001 task and its acceptance criteria.

**Important current finding**

The existing Rosewood & Almond design tokens are already present in:

`REOS_CONTROL_CENTER/Frontend/src/app/styles/tokens.css`

The established palette is:

- Rosewood: `#6F334B`
- Blush: `#F3DDE4`
- Almond: `#F8F1E7`
- Cocoa: `#352A2D`

The existing foundation also contains shared shell, navigation, UI components and design-system verification scripts. These are existing implementation assets, not a request to recreate the design system.

**Required scope for the frontend owner**

- Preserve the existing canonical design system and avoid introducing a second token/CSS system.
- Keep UI behavior consistent with frozen API and domain contracts.
- Ensure AI loading, clarification, empty, error and retry behavior is truthful and accessible.
- Prevent duplicate submissions and unsafe repeated actions.
- Verify responsive UX, keyboard access and appropriate accessibility behavior.
- Do not represent preview data as authoritative inventory.
- Do not label AI as live before the authorized server path and release conditions are verified.
- Assess potential duplicate entry points only through the frontend owner's reference/build/deployment audit.

**Boundary for this chat:** No frontend source, CSS, token, route, component or frontend verifier modifications. This workstream remains tracked in the master register without parallel implementation.

---

## 7. Change classification and duplicate prevention

Every proposed source change must be classified before implementation.

### 7.1 REUSE — default choice

Use the existing owner whenever it can satisfy the requirement through an appropriate stable interface.

Before choosing REUSE, record:

- Exact existing path and owner.
- Relevant public contract and callers.
- Current tests.
- Identified integration point.
- Evidence scope and remaining limitation.

### 7.2 UPDATE — preferred when the owner already exists

Update an existing owner when a verified defect belongs to that responsibility.

Required checks:

1. Read the complete current file and record its live blob SHA.
2. Inspect imports, public symbols and direct callers.
3. Confirm the observed behavior and intended contract.
4. Select the smallest coherent file batch.
5. Evaluate compatibility, security and migration consequences.
6. Define positive, negative, failure and regression tests.
7. Save using the approved process, then read back from GitHub.
8. Verify relevant Actions results and exact tested commit.

### 7.3 ADD — only for a proven ownership gap

A new module or file is justified only when:

- A real requirement is confirmed.
- Existing owners cannot satisfy it without violating responsibility boundaries.
- The new owner and interface are approved.
- Repository references and dependencies are inspected.
- Input, output, error, authorization and lifecycle contracts are defined.
- Required tests and CI discovery are specified.
- The change is authorized by the applicable process.

Do not create another gateway, state store, search service, memory service, recovery engine, evidence registry, design-token system or generic orchestration framework just to match a proposed diagram.

### 7.4 REMOVE — only after behavioral proof

A removal requires:

- Current repository-wide references/imports/callers/tests/workflow review.
- Proof the target is obsolete or duplicate in behavior and ownership.
- Identification of the canonical replacement.
- A migration approach where necessary.
- Regression evidence showing no required behavior or contract is lost.
- Readback and verification of the post-removal source state.

A similar filename is not sufficient proof of duplication.

### 7.5 DEFER or NO_CHANGE

Use `DEFER` when the work requires a future task, unresolved contract, environment, external action or approval. State the exact blocker and required evidence.

Use `NO_CHANGE` when current implementation already satisfies the requirement. Cite the existing owner and evidence so the same work is not repeated in another chat.

---

## 8. Dependency and execution model

This section helps organize findings. It does not override the canonical execution sequence or authorize parallel implementation.

### Stage 0 — Live baseline and ownership review

- Read current HEAD and state.
- Confirm current task, acceptance criteria and existing dependencies.
- Revalidate current architecture and the relevant evidence records.
- Check other active work to avoid conflicting edits.
- Record source owners and classifications.
- Keep the current task unchanged.

**Exit:** Current authority and the boundary of any permitted work are unambiguous.

### Stage 1 — Current APP-001 execution belongs to its existing owner

The canonical plan currently identifies APP-001 as the active gate and APP-001-T01 as its current task.

This plan does not advance or replace that task. The separate frontend chat owns its implementation. No parallel frontend modifications are authorized by this supporting document.

The canonical sequence currently recorded in state is:

1. `APP-001-T01` — Application shell and design system.
2. `APP-001-T02` — Authentication and tenant UX.
3. `APP-001-T03` — Buyer workflows.
4. `APP-001-T04` — Broker workflows.
5. `APP-001-T05` — Builder workflows.
6. `APP-001-T06` — Admin and governance workflows.
7. `APP-001-T07` — Search, lead, inventory and deal API integration.
8. `APP-001-T08` — AI integration with policy controls.
9. `APP-001-T09` — Accessibility, security and E2E tests.
10. `APP-001-T10` — Release-candidate freeze.

This list is the sequence recorded at the audit baseline, not a claim that any pending subtask has become complete. Re-read live state before any later decision.

**Exit:** The existing owner and Control Center complete the applicable task sequence and record any required formal transitions.

### Stage 2 — Map findings to the correct existing task or approved change request

After the current canonical task permits it, map each H360 finding to the correct existing owner and authorized scope.

Potentially relevant owners include CORE-005 for search criteria, APP-001-T07/T08 for the corresponding application integration, and the appropriate existing or future release/scale task for production controls.

These are **candidate mappings only**, not authorization to skip ahead, change the roadmap or modify an earlier gate. The Control Center and approved change process determine the actual task.

**Exit:** The applicable owner, acceptance criteria, dependencies and authority are explicitly established.

### Stage 3 — Close confirmed integration gaps

For each authorized workstream:

- Reuse existing interfaces and modules.
- Implement only verified missing behavior.
- Validate real request-to-response and action-to-outcome pathways.
- Add failure-path and authorization regression tests.
- Verify evidence against the exact changed revision.

**Exit:** The specific integration acceptance criteria are met at the declared evidence level.

### Stage 4 — Close reliability and recovery gaps

For authorized changes:

- Validate idempotency and durable identity.
- Exercise failure, interruption, retry and recovery scenarios.
- Preserve approval and scope enforcement.
- Verify the resulting state against the authoritative owner.
- Record residual risk.

**Exit:** The required execution paths complete or stop safely under the tested failure conditions.

### Stage 5 — Reconcile evaluation and operational evidence

- Update stale evaluation records through their existing owner.
- Reconcile old and new test results without deleting historical context.
- Approve measurable quality thresholds before release decisions.
- Verify observability and production controls separately from source tests.
- Keep the Section 14 decision consistent with actual accepted evidence.

**Exit:** Quality and operational outcomes are measurable and their evidence is traceable to tested revisions.

### Stage 6 — Release authorization

- Verify the relevant source revision and required workflows.
- Validate runtime configuration, secrets and permissions.
- Exercise deployment and rollback controls.
- Confirm monitoring, retention and incident-response evidence.
- Obtain required human and canonical approvals.

**Exit:** The authorized release owner has evidence to approve or reject production enablement.

### Stage 7 — Measured optimization

Only after the required release and safety gates are satisfied, prioritize further capabilities using measured business value, quality, reliability, cost and risk.

Future optimization must not create a second owner for an existing capability and must not be allowed to bypass formal execution authority.

---

## 9. Cross-cutting acceptance requirements

These apply to every relevant workstream.

### Architecture and maintainability

- One authoritative owner per business capability.
- Stable and validated module/API contracts.
- No accidental circular dependencies.
- No duplicated business rules in UI, AI and backend.
- No speculative abstractions without a proven need.
- Existing passing regressions remain enabled.

### Security and privacy

- Trusted server-side identity and authorization.
- Correct tenant scope across reads, writes, retrieval and telemetry.
- Least-privilege tool execution.
- Required human approvals for sensitive actions.
- Safe secret handling and redacted telemetry.
- Defined retention and deletion behavior where personal data is stored.
- Adversarial testing for prompt injection, privilege confusion and replay.

### Reliability

- Bounded timeout, retry and resource consumption.
- Explicit behavior for unavailable dependencies.
- Safe cancellation and recovery.
- Idempotency for retryable operations.
- No blind replay of irreversible actions.
- Truthful reporting of failure, partial completion and unresolved outcomes.

### Quality

- Unit tests for local behavior.
- Integration tests for public boundaries.
- Regression tests for previously observed defects.
- Security tests for critical trust boundaries.
- E2E tests for critical business workflows.
- Benchmarks for model-dependent behavior.
- Performance and cost tests appropriate to the intended workload.

### Evidence and operations

- Exact source commit for each tested claim.
- Applicable workflow/run identifier and result.
- Clear distinction between unit, synthetic, integration, E2E and production evidence.
- Logs and metrics suitable for investigation without unnecessary sensitive data.
- Operational ownership and runbooks for critical failures.
- Rollback and approval evidence for release.

---

## 10. Production quality and release scorecard

Do not declare HOMIO “world-class”, “production-ready” or “fully autonomous” merely because the code has many modules or test suites pass.

The release scorecard must use approved measurable requirements for:

| Dimension | Evidence required |
|---|---|
| Business correctness | Supported real-estate requests return contract-compliant outcomes |
| Search quality | Structured criteria, result correctness and unsupported-field behavior are measured |
| Groundedness | Listing claims and citations match authoritative, current records |
| Authorization | Protected operations and cross-tenant boundary tests pass |
| Agent safety | Tool allowlists, approval rules, invariant enforcement and actual outcomes are verified |
| Recovery | Interruption and retry tests prove safe resume and no duplicate side effects |
| Quality | Representative benchmark results are tied to model/configuration and revision |
| Economics | Cost, usage and quota behavior is measured under relevant load |
| Reliability | Latency, failures, availability and recovery evidence meet approved targets |
| Observability | Alerts, logs, traceability and incident response are demonstrated in the intended environment |
| Governance | Required checks, review controls, source revisions and approvals are traceable |
| Customer experience | Contract-compliant behavior is accessible, understandable and truthful |

Numerical thresholds and availability SLOs must be approved by the relevant owner. Do not invent accuracy targets, uptime promises or cost targets.

---

## 11. Evidence and document reconciliation policy

The supporting documents already in the repository have different responsibilities. They must not silently override one another.

### When an evidence record is stale

1. Identify the exact stale field or claim.
2. Find the actual newer source, test log or sanitized artifact.
3. Establish its tested revision and scope.
4. Preserve the prior result as historical context.
5. Update the existing evidence owner through its permitted process.
6. Read back the saved record.
7. Revalidate linked summaries that may now be stale.

### Current known reconciliation items

- Section 14 must be reconciled with the actual latest evaluation evidence. Its saved record currently points to an older backend run.
- Section 19 distinguishes AI-001 gate completion from production-release readiness. Preserve that distinction.
- Sections 20 and 21 provide security-reference and implementation-rule evidence. They do not certify production security on their own.
- The AI-001 blueprint's dated baseline/checkpoint remains history. Do not rewrite its old SHA values to make them appear current.
- The frontend master plan and frontend-specific continuation reference remain owned by the frontend workstream.
- The canonical state and existing Control Center determine formal task/status transitions.

Do not create a second status dashboard or evidence index when an existing source can be reconciled.

---

## 12. Required implementation-record template

Use this template inside the existing authorized task/evidence mechanism when a workstream is formally picked up. Do not create a separate tracking subsystem only to hold this template.

```text
WORKSTREAM ID: H360-xx
CANONICAL TASK / SUBTASK:
CURRENT CANONICAL STATUS:
REPOSITORY / BRANCH:
REVIEWED COMMIT SHA:
STATE BLOB SHA:
REVIEW DATE:
EXISTING OWNER:
FINDING CLASSIFICATION:
EXACT PATHS / SYMBOLS / CALLERS / TESTS:
OBSERVED BEHAVIOR:
CONFIRMED GAP:
CHANGE CLASS: REUSE / UPDATE / ADD / REMOVE / DEFER / NO_CHANGE
PROPOSED CHANGE:
DEPENDENCIES / BLOCKERS:
SECURITY AND PRIVACY IMPACT:
UNIT TESTS:
INTEGRATION TESTS:
REGRESSION TESTS:
E2E / ADVERSARIAL TESTS:
ACCEPTANCE CRITERIA:
REQUIRED APPROVALS:
ACTIONS WORKFLOW / RUN ID:
TESTED SOURCE SHA:
READBACK / VERIFICATION:
PRODUCTION EVIDENCE:
RESIDUAL RISK:
FINAL STATUS:
```

Unknown information must be marked `UNVERIFIED` or `BLOCKED` and investigated.

---

## 13. Definition of done and status meanings

### 13.1 Workstream completion

A workstream may be considered closed at its declared scope only when:

1. Its requirement is observable and unambiguous.
2. The live implementation and existing owner were inspected.
3. The smallest necessary change class was selected.
4. Dependencies and approvals were satisfied.
5. Required code or configuration exists on the intended source revision.
6. Applicable tests pass against that revision.
7. Saved content was read back and verified.
8. Evidence is traceable to the relevant behavior and tested source.
9. Residual risks and limitations are recorded.
10. The applicable owner or canonical process records the proper status.

### 13.2 Overall readiness statuses

- **AUDIT_COMPLETE:** The defined audit scope was reviewed and findings classified. This does not imply implementation.
- **IMPLEMENTATION_COMPLETE:** Authorized changes are present on the intended revision.
- **VERIFICATION_COMPLETE:** Applicable tests and source-revision evidence pass.
- **OPERATIONALLY_VERIFIED:** Required runtime controls have been demonstrated in the intended environment.
- **RELEASE_READY:** Approved security, quality, operational, governance and release conditions are satisfied.
- **PRODUCTION_ENABLED:** The authorized enablement/deployment has occurred and is verified.

These statuses must never be conflated.

### 13.3 Current plan disposition

This document is a supporting plan. Revising or saving it does not complete APP-001, reopen AI-001, close any H360 workstream, change canonical state or approve production enablement.

---

## 14. New-chat handoff protocol

A handoff should contain only the context needed to continue safely:

- Canonical repository and branch.
- Freshly observed HEAD and state blob SHA.
- Current canonical task and acceptance criteria.
- The specific workstream and scope currently authorized.
- Exact existing owner files and interfaces.
- Finding classifications and verified evidence.
- Completed changes with commit SHA and readback.
- Applicable tests and Actions run IDs with tested revisions.
- Open blockers and necessary approvals.
- Duplicate/dependency checks already completed.
- Work owned by another chat and files that must remain untouched.
- The next action allowed by live canonical state.

A handoff is context, not execution authority. A new session must re-read live state before acting.

### Current cross-chat boundary

The current frontend implementation is owned by the separate frontend chat. That chat must continue from the live frontend source and its existing Rosewood & Almond design-system contracts. This plan does not assign parallel CSS, token, navigation or page work.

---

## 15. Controlled maintenance of this plan

Update this document only when a real cross-domain gap, dependency, source-owner change or evidence issue requires plan reconciliation.

Before updating it:

1. Fetch the live document and confirm its current SHA.
2. Check repository paths and historical references.
3. Preserve existing canonical owner paths and current task IDs.
4. Use the `H360-*` namespace only for this plan's internal register.
5. Update the smallest coherent section or use a full replacement when the structure itself needs reconciliation.
6. Do not copy entire AI-001 or frontend specifications into this document.
7. Do not move implementation status into this file as a substitute for canonical evidence.
8. Re-read the saved version and verify the expected revision.
9. Keep the plan subordinate to current state and approved architecture.

### Revision 2.1 changes

This revision is intended to correct these identified weaknesses in the previous standalone plan:

- Resolves the gap-ID meaning collision with the older draft embedded in chat history.
- Defines the other-chat frontend ownership boundary explicitly.
- Recognizes the existing Rosewood & Almond token system as existing work to reuse, not a new implementation task.
- Separates AI-001 formal approval from customer-facing production readiness.
- Records the Section 14 evidence reconciliation requirement.
- Adds the observed branch-protection concern without changing repository settings.
- Adds an explicit architecture/runtime-boundary check before any new AI endpoint or server is proposed.
- Tightens the distinction between synthetic tests, exact-commit regression, operational verification and production approval.
- Preserves the existing plans, evidence owners, state authority and task sequence.

---

## 16. Adoption and review checklist

Before accepting a revised copy of this document into the repository, verify:

- [ ] The existing canonical path is being replaced rather than creating another standalone 360° plan.
- [ ] All current plan gap IDs use `H360-*`.
- [ ] Old history is treated as context, not execution authority.
- [ ] The current live task has been re-read and not changed by this document.
- [ ] AI-001 remains formally approved; this plan does not reopen it.
- [ ] Frontend work remains assigned to its existing owner.
- [ ] Rosewood & Almond is reused; no duplicate palette or design system is introduced.
- [ ] Section 14 reconciliation refers to actual newer evidence rather than assumed test counts.
- [ ] GitHub governance concerns are recorded without unauthorized repository-settings changes.
- [ ] Existing AI, search, execution, ACRL and evidence owners are preserved.
- [ ] Every future implementation batch has a duplication/dependency review and explicit acceptance criteria.
- [ ] The replacement is read back from GitHub after it is saved.
- [ ] No completion or production-readiness claim is made from the plan alone.

**Final rule:** The purpose of this document is to prevent forgotten gaps, duplicate implementation and false completion claims. It improves the engineering work plan; it does not replace the Control Center, current source code, actual test evidence or required approvals.

---

**End of document.**
