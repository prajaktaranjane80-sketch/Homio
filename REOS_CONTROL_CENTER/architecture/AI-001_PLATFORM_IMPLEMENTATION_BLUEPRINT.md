# HOMIO / REOS
# AI-001 — Production AI Platform, Agents, Project Context and Fast-Audit Blueprint

**Document ID:** HOMIO-AI-001-BLUEPRINT-001  
**Version:** 2.0  
**Status:** IMPLEMENTATION REFERENCE — NOT EXECUTION AUTHORITY  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical branch:** `reos-development`  
**Document path:** `REOS_CONTROL_CENTER/architecture/AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md`  
**Scope:** AI-001 platform architecture, implementation order, security, project-history references, fast audit, context reconstruction, evidence, testing and release criteria.

**Implementation checkpoint rule:** Section 3.6 records a dated, independently verified repository snapshot. That snapshot is non-authoritative and must be refreshed before every implementation batch. The architecture version remains 2.0; the checkpoint never supersedes canonical state.

---

## 1. Mission and Design Goals

Build HOMIO / REOS's AI platform as a secure, provider-independent, tenant-aware, observable, cost-controlled and recoverable capability for international real estate workflows.

This blueprint is the single detailed implementation reference for the AI-001 gate. It defines the intended package structure, module ownership, dependency rules, implementation sequence, project-context handoff rules, audit efficiency requirements, security checks and acceptance evidence.

The goals are:

1. Build the AI platform without creating duplicate HOMIO services or governance systems.
2. Preserve the existing property-search, identity, tenant, execution, financial and frontend boundaries.
3. Stabilize interfaces before connecting model providers.
4. Prevent AI from granting its own permissions or bypassing business authorization.
5. Keep retrieved property and business information traceable to authoritative sources.
6. Control model selection, usage, cost, retries and failure behavior.
7. Make project history and audit references reusable across AI sessions without rereading the entire repository on every turn.
8. Distinguish live facts, historical snapshots, approved decisions, unverified claims and stale test evidence.
9. Require exact GitHub commit, content readback, test and CI evidence before a completion claim.
10. Keep final integration and release verification ordered after the required component contracts and security boundaries are stable.
11. Preserve already-working code and passing regressions.
12. Use the existing Control Center for task selection and formal transitions.

**Reliability objective:** Reduce avoidable errors through explicit ownership, bounded interfaces, authoritative evidence, targeted verification and regression testing. No blueprint can truthfully guarantee the complete absence of future defects.

---

## 2. Canonical Authority and Non-Negotiable Rules

The following authorities retain their existing responsibilities.

| Concern | Canonical owner |
|---|---|
| Current gate, task, subtask and execution status | `REOS_CONTROL_CENTER/data/state.json` and the existing Control Center |
| Committed source and code history | GitHub repository branch `reos-development` |
| Agent operating contract | `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py` |
| Task selection and formal transitions | Existing REOS Control Center and its prescribed execution process |
| AI implementation structure | This blueprint, subordinate to canonical state and approved architecture |
| Repository-aware discovery and dependencies | Existing ACRL T14 and T16 |
| New-session bootstrap | Existing ACRL T07 |
| Development-agent governance | Existing ACRL T15 and applicable authorization controls |
| Execution authorization | Existing ACRL T18 and applicable business authorization contracts |
| Repair and patch verification | Existing ACRL T20 |
| Repository coordination | Existing ACRL T21 |
| Commit and checkpoint coordination | Existing ACRL T22 |
| Evidence resolution | Existing ACRL T23 |
| Cross-chat continuity and recovery | Existing ACRL T24 |
| Business identity and tenant membership | Existing identity/tenant domain implementation |
| Business-tool execution | Existing execution pipeline and governed tool gateway |
| Search and retrieval | Existing search/matching and indexing infrastructure |
| General context-budget responsibility | Existing budget and context controls |
| Backend CI | Existing `.github/workflows/backend-ci.yml` and its authorized reusable workflows |
| Frontend CI | Existing `.github/workflows/frontend-ci.yml` |
| Customer-facing AI user experience | Existing HOMIO frontend F08 boundary |
| AI platform implementation detail | This blueprint and the owning `ai_platform` modules |
| Project continuity context | Existing T07/T14/T23/T24 mechanisms; never a competing state authority |

### Mandatory rules

- Never edit `data/state.json` manually to manufacture progress, completion, approval or a next task.
- Never use this blueprint, a chat transcript or a generated summary as execution authorization.
- Never assume the current subtask from an old message, older plan, project-memory snapshot or historical audit record.
- Never add a second identity system, tenant registry, vector index, property ranking engine, business tool executor, Control Center, state store, memory system or Git synchronization engine.
- Never trust a tenant ID or permission claim merely because the client or model supplied it.
- Never permit an LLM response to authorize or approve its own business action.
- Never send provider secrets to the browser, repository, telemetry or ordinary error messages.
- Never call historical CI success a pass for a newer commit unless the tested source and applicable checks justify that claim.
- Never mark an audit finding fixed merely because a proposed file exists.
- Never weaken an existing authorization rule or required test just to make CI green.
- Never enable live AI customer-facing behavior until the full server-side path is implemented and verified.
- Never mix the separate Imperium AI project into HOMIO / REOS.
- When sources conflict, stop the affected decision and resolve the conflict using the applicable authority.
- Use existing files and responsibilities whenever they already satisfy the required behavior.
- Make additions only after current-tree, imports, ownership, contract and test inspection.

This document defines implementation intent. It does not override the Control Center, change canonical task status or authorize state-changing work outside the current task.

---

## 3. Reviewed Baseline and Known Starting Conditions

This section records the repository state observed while preparing Version 2.0. It is a dated baseline, not a permanent source of current status.

### 3.1 Canonical state at the Version 2.0 baseline

At the original review time:

- Repository: `prajaktaranjane80-sketch/Homio`
- Branch: `reos-development`
- Observed branch HEAD before saving the original replacement: `c7388dbdf8fe3aa5666228691f502eba94a38da6`
- Observed canonical state blob SHA: `38521091f3a40c990180ab1f6c59374ac0810745`
- Previous gate `CORE-008`: `APPROVED`
- Current gate: `AI-001`
- Current subtask: `AI-001-T01`
- Current subtask title: `Implement AI Gateway`
- Execution mode: `CONTROL_CENTER_DRIVEN`
- AI-001 subtasks: T01 current; T02–T10 pending at the time of review.
- AI-001 acceptance criteria AC01–AC06: pending at the time of review.

The branch and state must be read again before every implementation batch. Do not reuse these identifiers as a substitute for live verification.

### 3.2 Previous-gate evidence and current-HEAD limitation

The successful GitHub Actions Run #295 is:

`https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40191062850`

It tested commit `5bf0b982b3222e58b4582331da7be24ed8788ddb` and completed successfully. The authorized Control Center approval/freeze commit is:

`https://github.com/prajaktaranjane80-sketch/Homio/commit/a30007031cc55674a145e040f83bfe2ae9cdf9d4`

That verifies the CORE-008 approval path at the recorded point in history. It does **not** establish that GitHub Actions tested the later AI-001 blueprint commit or every future code change.

The blueprint is a planning document and need not trigger CI if the existing workflow path filters exclude the architecture directory. Do not change CI solely to make a documentation-only commit show a check. When AI source, tests or workflow configuration are changed, verify the applicable checks against the exact relevant commit.

### 3.3 Existing AI service boundary

The existing frontend documentation at:

`REOS_CONTROL_CENTER/Frontend/src/features/f08_ai/README.md`

states that `AI_LIVE_SERVICE_CONNECTED` is intentionally false and describes the current preview as not connected to a live AI model, market-data feed, affordability engine or brokerage handoff.

Preserve that truthful disclosure until the real server-side service path is operational and verified.

### 3.4 AI package at the original review baseline

At the Version 2.0 baseline review, the repository tree did not contain the proposed package:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/`

This is a historical observation about that reviewed HEAD. It is not a statement that the package is currently absent. Section 3.6 records the later verified implementation checkpoint.

Before each addition, inspect the latest branch tree, potential equivalent modules, imports and tests again.

### 3.5 Existing fast-audit manifest at the original review baseline

The path:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T14_Repository_Intelligence_Context/audit_resume_manifest.json`

was observed with:

- `status`: `UNINITIALIZED`
- `manifest_status`: `DERIVED_NON_AUTHORITATIVE_CACHE_ONLY`
- no repository binding
- no branch binding
- no audit-base commit SHA
- no canonical state blob SHA
- no generated timestamp or valid manifest fingerprint
- a blocker explaining that no current audit evidence had been recorded.

**Consequences:**

1. Do not claim that a validated current fast-resume cache is available without fresh evidence.
2. Do not fabricate a baseline, finding status, test record or manifest fingerprint.
3. Initialize or seal that manifest only through the authorized audit mechanism with actual verified evidence.
4. Do not create a second manifest just to avoid the existing `UNINITIALIZED` status.
5. The absence of a ready manifest does not prevent a focused read-only preflight for AI-001-T01. It does prevent claiming cache-backed `FAST_RESUME` until the required baseline is authoritatively recorded.

### 3.6 Live AI-001-T01 implementation checkpoint — verified 2026-10-25

**Purpose:** Preserve an exact snapshot of what was independently checked during the Version 2.0 implementation. This section is an evidence reference, not execution authority, a permanent status cache or a substitute for future readback.

#### Canonical repository and state

- Repository: `prajaktaranjane80-sketch/Homio`
- Branch: `reos-development`
- Verified HEAD at this checkpoint: `17c9d0ed82eaf069809074c27c6229876b4d1c9f`
- Canonical state path: `REOS_CONTROL_CENTER/data/state.json`
- Canonical state blob SHA: `38521091f3a40c990180ab1f6c59374ac0810745`
- Stored state integrity value observed at the checkpoint: `6911f9984f4ca679bb024be534ed431532109d71b94d38cb93c0eef3b0e22842`
- Current gate at the checkpoint: `AI-001`
- Current subtask at the checkpoint: `AI-001-T01 — Implement AI Gateway`
- Execution mode: `CONTROL_CENTER_DRIVEN`

The canonical state still identified T01 as current. No formal T01 completion transition was established by this checkpoint.

#### Verified AI package source

The following package-owned modules were present:

- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/__init__.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/contracts.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/errors.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/ports.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/settings.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_gateway.py`

The following canonical test paths were also present:

- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py`

The test files in `tests/` were read back from GitHub. The contract and gateway test files at those paths had the same blob SHAs as the older root-level copies at the time of this checkpoint.

#### Duplicate test paths still requiring cleanup

These root-level test files remained present at the checkpoint:

- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/test_contracts.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/test_model_gateway.py`

They duplicated the contents of the canonical files in `ai_platform/tests/`.

This is a structural cleanup finding, **not evidence that the tests failed**. A passing test run does not by itself remove duplicate source paths.

The safe resolution is:

1. Recheck the canonical `tests/` paths on the live branch.
2. Verify that the existing CI script explicitly runs those canonical paths.
3. Verify successful test results for the exact tested commit.
4. Only then remove the obsolete root-level copies, using their live blob SHAs.
5. Read back the resulting tree and run CI again against the cleanup commit.
6. Do not delete the canonical test files under `tests/`.

If any path or blob SHA changes before deletion, stop and repeat the readback before proceeding.

#### Verified CI coverage at the checkpoint

Existing backend CI was extended through the owning script:

`.github/actions/homio-backend-ci/verification/scripts/compile_and_contracts.sh`

The script explicitly compiles the AI package and runs:

```bash
python -m pytest -q -p no:cacheprovider \
  AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py \
  AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py
```

Latest relevant successful run at the checkpoint:

`https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40208536109`

Tested commit:

`17c9d0ed82eaf069809074c27c6229876b4d1c9f`

The retrieved Actions logs showed:

- Existing agent-entrypoint contract test command: **15 passed**
- AI package contract, gateway and public-contract test command: **31 passed**
- Full ACRL suite: **1,444 passed**
- Overall backend/ACRL workflow: **SUCCESS**

This is evidence for that specific tested commit. It does not prove a later commit, a future cleanup, production provider integration, all six AI-001 acceptance criteria or formal T01 completion.

The AI tests used deterministic fake dependencies. This checkpoint does not authorize live provider calls, business mutations or changing the frontend's truthful live-AI status.

#### Required interpretation

- The original statement that the package did not exist is historical; the current package now exists.
- The test-path correction and AI CI wiring passed on the tested commit.
- Two obsolete root-level test copies were still present at this checkpoint.
- T01 remained the canonical current subtask.
- This checkpoint must be refreshed before the next implementation batch.
- Do not manually change `data/state.json` to reflect a test pass or to advance the task.

---

## 4. Two Different AI Contexts — Keep Them Separate

HOMIO has two related but different AI concerns.

### 4.1 Customer-facing AI platform

The `ai_platform` package serves product/backend requests and, eventually, approved agent operations. It handles provider calls, retrieval, cost controls, authorization interfaces, tool proposals and operational telemetry.

It must not become responsible for developer-session continuity or GitHub control.

### 4.2 Development-agent project context

The development agent is the GPT/AI-assisted engineering workflow that reads HOMIO history, understands the active task, audits source changes, checks tests and prepares exact implementation content for the owner.

This workflow must use existing repository authorities and ACRL mechanisms:

- T07 for bootstrap and checkpoint coherence.
- T14 for repository-aware context and fast-resume assessment.
- T16 for source discovery and dependency-aware change impact.
- T23 for evidence identity and current-evidence resolution.
- T24 for continuity recovery and authority/provenance consistency.
- T18, T20, T21 and T22 at their established authorization, verification, repository-write and checkpoint boundaries.

**Do not import ACRL runtime code into customer-facing frontend code. Do not make the customer-facing `ai_platform` depend on the developer agent's task history, repository state or Control Center state.**

The shared principle is good evidence and clear ownership; the runtime dependencies and permissions are separate.

---

## 5. Existing Infrastructure — Reuse Before Adding

The following owners were found during the source inventory. They are reuse candidates, not claims that every interface is production-ready.

| Existing owner | Intended use | Boundary |
|---|---|---|
| `AUTONOMY_ENGINE/execution/tool_gateway.py` | Existing governed business-tool gateway | Do not build a parallel business mutation engine |
| `AUTONOMY_ENGINE/execution/execution_pipeline.py` | Existing execution lifecycle | Invoke only through established contracts and authorization |
| `AUTONOMY_ENGINE/core/identity_tenant/` | Existing identity, membership and tenant contracts | Do not create an AI-specific tenant database |
| `AUTONOMY_ENGINE/core/search_matching/` | Existing domain search, retrieval and indexing | Do not create a duplicate property-ranking or vector-index system |
| `AUTONOMY_ENGINE/budgets/context_budget.py` | Existing context/resource budget, when compatible | Do not build a second generic budget manager |
| `AUTONOMY_ENGINE/core/event_platform/event_observability.py` | Existing event/observability capability | Reuse only the compatible event contract |
| `AUTONOMY_ENGINE/core/context_compiler.py` | Existing small priority-ordering/redaction helper | Do not assume this helper alone implements complete safe context reconstruction; verify and extend only under its owning scope |
| ACRL T07 | Bootstrap and checkpoint coherence | Does not authorize execution |
| ACRL T14 | Repository context and resume manifest assessment | T14 uses T16 for repository intelligence; do not duplicate the index or dependency graph |
| ACRL T15 | Development-time AI operator governance | Not the customer-facing agent runtime |
| ACRL T16 | Repository intelligence, discovery and dependency analysis | Canonical source/dependency discovery owner |
| ACRL T18 | Safe execution authorization | Not replaceable by a prompt or model output |
| ACRL T20 | Repair and patch verification | Verification is distinct from Git commit and CI |
| ACRL T21 | GitHub repository coordination | Respect all repository permissions and policies |
| ACRL T22 | Commit/checkpoint coordination | Use existing checkpoint conventions |
| ACRL T23 | Evidence resolution and provenance | Do not create another evidence selector |
| ACRL T24 | Continuity and recovery | Must validate source authority and evidence freshness |
| `AUTONOMY_ENGINE/runtime/runtime_config.json` | Existing autonomy runtime defaults, read-only limits and evidence requirements | Its settings do not automatically become the customer-facing AI's runtime configuration |
| `AUTONOMY_ENGINE/agents/roles.json` | Existing development-agent analytical roles | Roles are not permission grants |
| F08 in `Frontend/src/features/f08_ai/` | Existing customer-facing AI experience | No frontend imports of ACRL runtime; no client-side provider keys |
| `.github/workflows/backend-ci.yml` | Existing backend/ACRL verification path | Reuse and extend only after checking actual test selection |
| `.github/workflows/frontend-ci.yml` | Existing frontend verification path | Do not create another frontend workflow |

### Important source findings

The reviewed autonomy runtime config currently includes:

- `mode`: `READ_ONLY_UNTIL_ADAPTER_APPROVED`
- `canonical_state`: `../data/state.json`
- `max_context_chars`: `24000`
- `max_file_preview_chars`: `6000`
- target limits of 20 for repository, dependency and test targets
- no direct state or repository mutation
- evidence-before-execution, postflight and checkpoint requirements
- fail-closed behavior on ambiguity.

These are settings of the existing autonomy runtime. Apply them according to that runtime's owner and contract. Do not silently copy them into a separate configuration authority or assume that a character count equals a model-token budget.

---

## 6. Proposed AI Platform File Structure

**Package root:**

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/`

```text
ai_platform/
├── __init__.py
├── contracts.py
├── errors.py
├── ports.py
├── settings.py
├── model_registry.py
├── model_gateway.py
├── provider_adapters/
│   ├── __init__.py
│   └── base.py
├── prompt_templates.py
├── embeddings.py
├── retrieval_adapter.py
├── rag_pipeline.py
├── authorization.py
├── agent_runtime.py
├── tool_bridge.py
├── cost_control.py
├── resilience.py
├── observability.py
└── tests/
    ├── conftest.py
    ├── test_contracts.py
    ├── test_public_contract_stability.py
    ├── test_model_registry.py
    ├── test_model_gateway.py
    ├── test_provider_adapters.py
    ├── test_prompt_templates.py
    ├── test_retrieval_and_rag.py
    ├── test_authorization_tenant_isolation.py
    ├── test_agent_tool_boundaries.py
    ├── test_cost_control.py
    ├── test_resilience_observability.py
    ├── test_data_policy_contracts.py
    ├── test_ai_quality_regression.py
    ├── test_runtime_boundary.py
    └── test_ai_platform_integration.py
```

### Structure rules

1. This is a proposed target layout, not permission to create all files in one batch.
2. Recheck every target path on the live branch before adding or replacing it.
3. If an existing module owns the same behavior, reuse it or document a specific extension; do not create a second owner.
4. Add provider-specific adapters only after the provider selection, dependency inventory, secret-management path and required capabilities have been approved.
5. `prompt_templates.py` is for versioned customer-facing AI prompt construction and metadata. It must not hold secrets or become an authorization engine.
6. Do not place developer-session history, resume manifests, T-layer task selection or Control Center state inside `ai_platform/`.
7. Do not create separate project-history, audit-cache, memory, dependency-graph or evidence-index files for convenience.
8. The exact HTTP/API integration path remains undecided until the current backend/server entry points and authentication path have been inspected. Add one narrow integration at the established boundary; do not create another backend.
9. Tests should remain grouped by behavior and contract. Do not add a new test file when an existing focused test already covers the required invariant and the existing file has a clear owner.
10. If evidence supports changing this structure, update this blueprint before implementation spreads across dependent modules.
11. For T01, the canonical locations of package-owned tests are under `ai_platform/tests/`. If identical tests remain at package root, verify the canonical copies, CI paths and successful test evidence before deleting the obsolete root copies. Never delete the canonical `tests/` copies.
12. After removing duplicate tests, read back the complete package tree and run CI against the exact cleanup commit. A successful pre-cleanup run is not proof that the deletion commit passed.

---

## 7. Module Responsibilities and Interface Contracts

### 7.1 `contracts.py` — Stable public data contracts

Owns the typed, provider-independent request/result structures:

- model request and model response
- embedding request and embedding result
- usage metadata and usage status
- model capability metadata
- trusted request-context reference
- source/evidence reference
- tool proposal and validated action result where needed
- completion/failure status
- correlation and idempotency identifiers where applicable.

Requirements:

- Prefer immutable typed records and validated finite value ranges.
- Reject malformed, ambiguous, oversized or unsupported inputs explicitly.
- Distinguish provider-reported usage from estimated usage.
- Distinguish model output from verified evidence and executed business outcomes.
- Never encode credentials or mutable global authorization state in a contract.
- Never encode canonical Control Center state as AI conversation state.
- Version breaking contract changes and preserve compatibility where possible.

### 7.2 `errors.py` — Stable failure taxonomy

Provide explicit machine-readable classifications for:

- invalid request
- unauthorized or untrusted request context
- unknown or disallowed model
- provider unavailable
- provider timeout
- invalid provider response
- embedding incompatibility
- retrieval failure
- policy/tenant access denied
- usage or cost limit exceeded
- tool authorization denied
- required approval missing
- idempotency/replay conflict
- downstream temporary failure
- internal unexpected failure.

Public responses must not leak raw provider exception text, stack traces, credentials or internal infrastructure details. Keep machine-readable codes separate from safe user-facing messages.

### 7.3 `ports.py` — Dependency-inversion interfaces

Define small interfaces for:

- generation provider
- embedding provider
- model registry
- trusted identity and authorization policy
- retrieval provider
- usage reservation/accounting boundary
- business-tool execution boundary
- observability sink
- approved runtime configuration/secret resolution boundary.

Provider SDK objects must not leak into public contracts. Tests should use deterministic fakes and must not require a paid model call or live secret.

If an interface is not available at a required downstream subtask, use a narrow typed contract and fail closed for operations that require the unavailable control. Do not fabricate permission or usage accounting.

### 7.4 `settings.py` — Validated configuration and data policy

Owns non-secret settings and validated policy references:

- enabled provider identifiers
- allowed model identifiers
- context, request and output bounds
- timeout and retry configuration
- per-request usage limits
- retrieval limits and allowed data classes
- feature availability
- fallback policy
- privacy, retention and logging policy references
- model rollout/version selection.

Secret values must come from the approved server-side secret-management path. Do not store secret values in ordinary committed configuration or include them in diagnostics.

Invalid configuration must fail startup or request preflight explicitly. Do not silently use a permissive default.

### 7.5 `model_registry.py` — Provider/model selection

Responsibilities:

- explicitly allowlist provider and model identifiers
- validate model capability and request compatibility
- apply version/alias resolution deterministically
- apply configured model eligibility and rollout policy
- reject arbitrary model names and dynamic imports from user input
- distinguish provider availability from user authorization
- make selected provider/model/version auditable.

The registry is not an identity or tenant-membership registry and cannot approve a business operation.

### 7.6 `model_gateway.py` — Governed model-request coordinator

Expected request path:

1. validate request structure and size
2. require a trusted server-derived request context
3. resolve the configured, allowed model
4. establish the applicable authorization and data-policy context
5. enforce the required usage/cost guard
6. submit the request through the provider adapter
7. enforce request timeout and retry policy
8. validate response shape, output size and usage metadata
9. redact sensitive information according to policy
10. record structured usage and safe operational events
11. return a typed result or explicit failure.

The gateway must not:

- read or mutate `data/state.json` as application runtime data
- access business tables directly to make domain decisions
- bypass the existing tool gateway or execution pipeline
- treat model output as evidence that a business action succeeded
- change tenant or privilege scope after provider failure
- use an unapproved model as a silent fallback
- invent a successful result when no permitted provider succeeded
- enable production live requests while required authorization, data-policy, usage-control or observation ports are absent.

### 7.7 `provider_adapters/base.py` — Common provider contract

Responsibilities:

- map common requests into provider-specific format
- normalize responses, usage and provider errors
- validate the returned structure before exposing it to the gateway
- preserve provider/model version information
- apply safe request and response limits
- avoid logging prompt bodies or private provider payloads by default.

Provider-specific adapters must stay behind this contract. Do not add speculative adapters before the actual approved provider strategy is selected.

### 7.8 `prompt_templates.py` — Versioned prompt construction

Responsibilities:

- keep prompt templates versioned and identifiable
- separate system/developer policy from untrusted user and retrieved content
- declare the task purpose and expected response schema
- retain relevant source identifiers and policy version metadata
- support regression testing of prompt changes
- ensure a change in prompt behavior is detectable in test results.

Never place secrets in prompt templates. Never use the prompt as the only authorization control. Prompt wording can guide model behavior, but actual permissions remain enforced in code at the business boundary.

### 7.9 `embeddings.py` — Embedding adaptation

Responsibilities:

- use a registry-approved embedding model
- validate vector dimension and finite numeric values
- track embedding model/version compatibility
- reject invalid or mismatched vectors
- respect data classification and privacy rules before embedding text
- preserve source/record identity needed to rebuild derived indexes.

Do not create a parallel vector database or index.

### 7.10 `retrieval_adapter.py` — Existing HOMIO search integration

Responsibilities:

- use the established search/retrieval contracts
- require trusted tenant and applicable resource-access context
- enforce tenant scope before results can reach the RAG pipeline
- preserve source identity, access scope, version and provenance
- validate candidate/result structure
- distinguish retrieved content from canonical business truth
- return a typed retrieval failure if the established service is unavailable.

Property ranking, listing eligibility, builder ownership, legal status and financial calculations remain with their existing domain owners.

### 7.11 `rag_pipeline.py` — Evidence-bounded context assembly

Responsibilities:

- assemble model context only from authorized, relevant sources
- preserve source IDs and provenance
- bound document counts, total context and output size
- separate trusted policy instructions from untrusted document contents
- mitigate direct and indirect prompt-injection risks
- distinguish sourced facts from model-generated interpretation
- expose missing, conflicting, incomplete or stale evidence where relevant
- refuse or qualify unsupported property, legal, affordability, yield or price claims
- rebuild derived retrieval data from authoritative source records when required.

An embedding match, retrieval score or model response is not proof that a property fact is current or correct.

### 7.12 `authorization.py` — Adapter to existing identity and permission contracts

Responsibilities:

- accept only trusted server-derived identity context
- use existing membership, tenant and resource authorization contracts
- require action/resource-level authorization where applicable
- default to denial when required evidence is missing
- keep decision provenance and policy reference where supported
- fail closed when the authoritative authorization service is unavailable.

Do not create a second user database, role database or tenant-membership engine. Do not derive permission from an email address, model explanation or client-supplied tenant field alone.

### 7.13 `agent_runtime.py` — Bounded agent loop

Responsibilities:

- define allowed tools and task objectives explicitly
- validate model-proposed actions against typed schemas
- keep proposals separate from authorized execution
- limit iterations, context, elapsed time and tool calls
- detect repeated/circular tool calls and replay attempts
- require sufficient evidence before applicable actions
- return a clear stop/block/failure result
- maintain a traceable relationship between a request, model proposal, policy decision and tool receipt.

An agent must not be given unrestricted shell, arbitrary Python, database, repository or filesystem access by default.

### 7.14 `tool_bridge.py` — Governed business-tool integration

Responsibilities:

- reuse `execution/tool_gateway.py` and established execution contracts
- validate action type and arguments
- enforce authorization independently of model output
- preserve idempotency, approval and audit requirements
- verify the action receipt through the applicable existing boundary
- distinguish accepted, executed, rejected, failed and unknown action outcomes.

Sensitive or irreversible real-estate operations—such as publishing or withdrawing inventory, committing a commercial offer, submitting binding instructions, modifying contractual commitments, or executing a financial mutation—must not run from an untrusted proposal. Apply the existing approval, authorization and domain validation rules.

Until the full safe execution path is implemented and tested, keep sensitive mutations disabled. The T05 agent runtime must not bypass controls that are strengthened in T06 or later.

### 7.15 `cost_control.py` — AI usage controls

Responsibilities:

- apply input, context and output limits
- track actual provider usage when available
- distinguish estimated from provider-reported values
- reserve and account usage through an agreed durable accounting boundary
- support safe concurrent quota enforcement
- make accounting idempotent where request retry/replay is possible
- record explicit usage outcome and accounting status
- fail closed or follow a specifically approved fallback when the usage boundary is unavailable.

Reuse the established context budget and compatible accounting owners. An in-memory counter is not a durable production usage ledger.

### 7.16 `resilience.py` — Bounded failure handling

Responsibilities:

- configure explicit timeouts
- retry only classified transient errors
- bound retry count and total elapsed time
- never retry authorization failures as though they were transient
- avoid blind retry of non-idempotent tool mutations
- expose provider failure and fallback reason
- preserve tenant, policy and response-contract boundaries across permitted fallback.

A fallback must never imply that an action or model call succeeded when it failed. Do not switch to an incompatible model without explicit allowed-model policy.

### 7.17 `observability.py` — Redacted structured operational events

Capture, where supported:

- correlation/request ID
- provider, model and version
- operation category
- duration and outcome
- normalized failure code
- retry and fallback events
- usage and accounting status
- policy/approval decision reference
- retrieval provenance reference
- tool receipt identity and final status.

Do not log API keys, access tokens, cookies, full authentication headers or entire sensitive prompts/documents by default. Recursively redact secrets in nested objects and exception metadata. Apply access control and retention policy to operational records.

---

## 8. Cross-Cutting Production Requirements

These apply to the modules above and must not be deferred merely because the gateway can return a response.

### 8.1 Data classification and privacy

- Identify which request fields and retrieved records are public, tenant-private, personal, confidential or commercially sensitive.
- Send only the minimum necessary content to the provider.
- Never include a different tenant's data in prompts, caches, traces or retrieval results.
- Define retention and deletion behavior for any persisted conversation, request or derived record before enabling persistence.
- Do not persist prompts or responses by default where there is no approved requirement.
- Do not place personal or confidential data in model training/fine-tuning paths without explicit policy and authorization.
- Respect the applicable data-residency and provider-processing requirements for international deployments.
- Ensure logs, evaluation fixtures and evidence artifacts do not contain real secrets or unnecessary personal information.
- Keep user-visible disclosure honest about service status, AI-generated content and limitations.

### 8.2 Request identity, idempotency and replay

- Give each accepted request a stable correlation identifier.
- Use a separate idempotency key where the operation may be retried or cause a side effect.
- Bind action proposals and action receipts to the originating request and applicable authorization decision.
- Reject incompatible replay rather than silently accepting a reused key with different arguments.
- Never treat a repeated timeout as proof that the underlying mutation did not execute; resolve the action outcome through its authoritative receipt.
- Keep business-operation idempotency with the existing execution/domain owner.

### 8.3 Output and structured-data safety

- Validate structured model outputs against explicit schemas.
- Treat model-generated URLs, markup, HTML, tool arguments and database identifiers as untrusted.
- Apply output encoding appropriate to the consuming frontend.
- Never pass free-form model text directly to shell, SQL, file operations or mutation APIs.
- Do not let natural-language output override business rules or server-side validation.
- Do not present model assertions as verified booking, transaction, legal or financial outcomes without authoritative confirmation.

### 8.4 Model/prompt versioning and quality

- Identify the configured model, provider and prompt version for each relevant result.
- Preserve a known-good model/configuration baseline for rollback.
- Require controlled evaluation before changing production model routing or prompt versions.
- Use a deterministic, versioned evaluation set for representative HOMIO use cases.
- Test regressions involving unsupported property claims, cross-tenant leakage, source attribution, retrieval quality, tool misuse and degraded provider behavior.
- Separate response-quality evaluation from authorization and business correctness. A high-quality answer cannot compensate for a failed access-control test.
- Do not invent quality scores, performance thresholds or production SLOs. Set and approve them using measurable requirements before release.

### 8.5 Availability and operational controls

- Bound request concurrency, context size, tool execution, retries and total time.
- Prevent quota overspend during concurrent requests.
- Use provider health suppression/circuit-breaking only if compatible with existing runtime conventions.
- Make the live-AI kill switch or disablement path explicit in the final deployment design.
- Do not silently degrade into stale evidence or cached cross-tenant content.
- Provide sufficient logs/metrics to distinguish provider failure, model selection failure, authorization denial, retrieval failure and business-tool failure.
- Establish and test rollback before broad production rollout.
- Apply existing secret and dependency-locking practices; do not introduce unpinned provider SDKs or undocumented supply-chain dependencies.

---

## 9. Project History and Fast-Audit Protocol for Development Agents

This is a critical development-workflow requirement. Its implementation belongs to the existing T07/T14/T16/T23/T24 owners and relevant authorized tasks; it does **not** create a new AI runtime subsystem.

The objective is to let a new AI session reconstruct the correct project position quickly, reference prior work precisely, and avoid repeated full-repository audits when a valid incremental audit is possible.

### 9.1 Define “project history” correctly

HOMIO project history consists of multiple evidence classes:

1. Current canonical state and current Control Center task.
2. Current committed code and actual Git history.
3. Approved architecture, task contracts and implementation plans.
4. Verified code changes and their exact commit identities.
5. Test output and GitHub Actions results tied to the SHA that was tested.
6. Acceptance evidence and recorded gate transitions.
7. Historical audit findings, decisions, blockers and their supporting references.
8. Non-authoritative context such as chat summaries, `Chat histry`, diagnostic output and old continuity snapshots.

These classes are not interchangeable.

A chat transcript may help locate a previous decision, but it cannot prove the current task, saved file content, test result or formal completion. A passing run on an older SHA cannot prove a newer SHA. A historical plan may document the right state for its date and still be wrong about today's task.

### 9.2 Source hierarchy for every new engineering session

Use this order:

**Level 1 — Current execution authority**

- Read live `REOS_CONTROL_CENTER/data/state.json`.
- Identify repository/branch/HEAD.
- Read current gate, task, subtask, execution status, required acceptance criteria and relevant controller status.
- Do not infer the next task from conversation history.
- When relevant status is inconsistent, report the inconsistency and follow the existing controller process.

**Level 2 — Current code truth**

- Read the exact target files from the live `reos-development` branch.
- Identify their blob SHAs and current owners.
- Inspect current imports, contracts and directly relevant tests.
- Use actual commit history/diffs to reconstruct prior code changes.
- Never use an unverified local or stale snapshot as the replacement source.

**Level 3 — Applicable operating and architecture rules**

- Read `AI_AGENT_ENTRYPOINT.py`.
- Read this blueprint.
- Read the currently relevant approved architecture and exact canonical task plan.
- Use `HOMIO_GPT_GITHUB_WORKFLOW_SYNC_AND_ACRL_EXECUTION_ORDER.md` for ordered work and historical reconciliation, not as an alternative task selector.
- Use `HOMIO_ACRL_PLATFORM_WIDE_AUDIT_PLAN.json` as an audit specification/history record, not execution authority.
- If the applicable plan conflicts with live state, stop the conflicting work until the source is reconciled.

**Level 4 — Verified implementation and test evidence**

- Read the existing acceptance/evidence record for the active gate.
- Inspect the exact commit and relevant diff.
- Verify the specific GitHub Actions run, tested SHA, conclusion and relevant jobs.
- Inspect stale or failed evidence separately; do not delete failed runs from history just to present a clean summary.
- Prefer current, direct, source-linked evidence over copied status prose.

**Level 5 — Historical continuity and search hints**

Reuse T07, T14, T16, T23 and T24 as intended. Chat history, personal memory, diagnostic output and older continuity files can suggest where to look, but their claims must be validated against the higher levels before they affect implementation decisions.

### 9.3 Current known stale-context hazards

The following observations were made during the Version 2.0 review and should be treated as historical evidence, not permanent current status:

- The T14 `audit_resume_manifest.json` was `UNINITIALIZED`. Fast resume must not be claimed until the existing manifest is populated and sealed through the authorized process with actual evidence.
- `REOS_CONTROL_CENTER/PROJECT_CONTINUITY/continuity_state.json` described `main`, an old baseline commit and `CORE-004` while the canonical state reported `reos-development` and `AI-001-T01`. That snapshot must not be used as the current task selector.
- `REOS_CONTROL_CENTER/reos_state.json` is a legacy/non-authoritative snapshot. Do not treat it as the canonical state and do not delete it without a separate source-reference audit.
- `PS Output` and other diagnostic artifacts are evidence only, not project state or execution authority.
- The AI-001 package root was absent at the Version 2.0 baseline. At the dated checkpoint in Section 3.6, it exists. Always use the current live tree before making a path-absence or file-deletion decision.
- Two root-level AI test copies remained present at the Section 3.6 checkpoint, alongside the intended `tests/` paths. Do not claim the duplicate cleanup is complete until the live tree confirms it.
- The existing F08 documentation stated that live AI integration was not connected. The UI flag must not change merely because provider interfaces or frontend builds exist.
- The historical CORE-008 approval run succeeded on its tested commit. It does not prove the AI-001 blueprint or later AI code passed CI.

These hazards should be incorporated into the context packet when relevant. Do not create a new “stale context registry” solely to repeat them.

### 9.4 Fast-resume decision policy

Use the existing T14 `audit_resume_manifest.py`, manifest schema and tests. T07's bootstrap must cross-check the current authoritative state. T14's manifest is a derived cache; it never grants authority.

| Condition after independent live read | Required decision |
|---|---|
| Manifest is missing, uninitialized, malformed, tampered with or fingerprint-invalid | `INVALID_MANIFEST` or `FULL_AUDIT_REQUIRED`, following the existing T14 contract |
| Repository or branch does not match the expected canonical source | Full bootstrap/reconciliation; fail closed on unresolved conflict |
| Canonical state blob SHA changes or current position conflicts | Full authority/bootstrap reconciliation; re-read the current task and required handoff |
| HEAD is unchanged, canonical state matches, manifest is valid and fresh, audited paths/evidence are still applicable | `FAST_RESUME`, but only if the current T14 assessment actually returns it |
| HEAD changes and a reliable, verified commit delta is available | `TARGETED_REAUDIT` of changed paths and verified affected dependents |
| A path was added, deleted, renamed or changed and its relevant blob/dependency evidence can be resolved | Targeted audit of that path and affected consumers |
| The commit delta is unknown, incomplete, untrusted or cannot establish the changed path set | `FULL_AUDIT_REQUIRED` |
| Relevant CI/evidence is stale or from an unrelated SHA | Revalidate the affected findings; do not show expired evidence as current PASS |
| Manifest freshness or source identity cannot be proven | Follow T14's fail-closed decision; never assume cache validity |

`FAST_RESUME` means “use a validated baseline and perform the required current checks”; it does not mean “skip verification.” It also does not mean “never recheck the full system again.” A full audit is required when the authority, baseline or affected scope cannot be established reliably.

If the repository or state changes while an implementation batch is in progress, refresh the relevant baseline before writing. Do not continue with a stale audit decision.

### 9.5 Efficient incremental audit method

When a valid manifest is available:

1. Independently read current branch, live HEAD, canonical state and state blob SHA.
2. Validate the manifest fingerprint, source identity, base SHA and evidence freshness through the existing T14 mechanism.
3. Obtain a reliable commit delta from the last trusted audit base to current HEAD.
4. Resolve actual additions, edits, deletions and renames; do not infer changes from commit messages alone.
5. Use T16 for source classification and affected dependents. Inspect relevant imports and tests.
6. Re-read exact current target files and compare them against the recorded baseline.
7. Use T23 to resolve the requested current evidence and conflicts.
8. Use T24 where cross-session continuity or recovery is needed, with validated upstream provenance.
9. Refresh only the findings and evidence invalidated by the change.
10. Run tests covering the changed module and its impact surface.
11. Record the exact commit, changed paths, tests and CI run when available.
12. Preserve unrelated valid findings instead of declaring the whole audit invalid solely because one independent file changed.

If any step cannot establish trustworthy evidence, stop using the cached result and take the required T14 full-audit or bootstrap path.

### 9.6 Do not force fast resume before the first valid baseline

Because the reviewed manifest was `UNINITIALIZED`, the safe first run is not a fabricated cache hit.

Use this policy:

- Perform the required authorized baseline/audit through the existing audit mechanism.
- Record only actually inspected paths, findings, source identities and verified evidence.
- Run the applicable checks.
- Use the existing manifest builder, validation, fingerprint and sealing mechanism according to its contract.
- Read back the resulting manifest and evidence.
- Test manifest invalidation, path-delta handling, stale evidence and source mismatch.
- Only then allow subsequent sessions to request fast resume.

This work remains subject to the canonical task and authorized scope. If only a focused AI-001-T01 preflight is authorized, perform that bounded read-only preflight, state that cross-project fast resume is not yet established, and do not silently start a separate ACRL implementation task.

### 9.7 Compact AI-agent audit/context packet

For each new session or meaningful handoff, produce a concise packet with the fields below. This is a required **output contract** for the development workflow, not a demand to create another permanent history file.

```text
HOMIO SESSION / AUDIT PACKET

1. PROJECT IDENTITY
   Repository:
   Canonical branch:
   Observed live HEAD SHA:
   Observation timestamp:
   Canonical state path and blob SHA:

2. CURRENT AUTHORITY
   Current gate:
   Current task/subtask:
   Canonical task status:
   Required acceptance criteria:
   Execution authorization boundary:
   Relevant approved architecture references:

3. CURRENT WORK SCOPE
   In scope:
   Out of scope:
   Exact target paths:
   Existing module owner for each responsibility:
   Proposed action per path: ADD / UPDATE / VERIFY / NO CHANGE / BLOCKED

4. VERIFIED HISTORY
   Last relevant code commit:
   Changed paths and what changed:
   Relevant prior design decisions:
   Source path/commit/evidence link for each decision:
   Superseded or historical references that must not be followed:

5. CURRENT FINDINGS
   Finding ID:
   Severity:
   Exact evidence:
   Affected paths:
   Current status:
   Required correction or verification:
   Dependencies/blockers:

6. TESTS AND CI
   Focused tests required:
   Existing regression suites:
   Latest relevant Actions run:
   Exact tested SHA:
   Conclusion and relevant jobs:
   AI package test paths and result:
   Duplicate test copies / cleanup status:
   Evidence that is stale or does not apply:

7. FAST-RESUME STATUS
   T14 decision:
   Manifest SHA/status:
   State identity validated:
   Verified HEAD delta:
   Paths/dependents invalidated:
   Findings requiring re-audit:

8. NEXT AUTHORIZED ACTION
   One concrete action:
   Exact paths:
   Required evidence:
   Prohibited actions:
   Completion proof required:
```

Every field must be supported by the available evidence or explicitly marked `UNKNOWN`, `UNVERIFIED`, `NOT APPLICABLE` or `BLOCKED`. Do not fill blank fields by guessing.

### 9.8 Efficient context sizing and source references

Use the compact context principle:

- Prefer a summary plus exact source references over pasted historical transcripts.
- Include only the current task contract, current source/test excerpts, directly affected dependencies and applicable evidence.
- Inspect whole files when necessary for a replacement or a complete understanding, but do not repeatedly paste unrelated complete files into each new session.
- Use file path, exact blob SHA or commit SHA, and relevant section/line range where available.
- For CI, retain the Actions URL, tested commit SHA, conclusion and relevant job/test details.
- For source-history questions, use commit history and diffs rather than trying to reconstruct every code change from chat memory.
- For a current-status question, re-read canonical state instead of trusting the last packet.
- Do not let a compact packet omit a material security boundary simply to reduce its size.
- Respect the owning runtime's context/preview limits; do not mistake character count for tokens.
- If context budget is exhausted, prioritize authority, current task, blocking safety rules, exact target ownership, changed-path impact, current tests/CI and the next allowed action. Preserve links to lower-priority history for retrieval as needed.

### 9.9 History persistence and audit references

Use the existing sources for their existing purposes:

- Git commit history: what was committed and when.
- Current canonical state: which task is active and which transitions were recorded.
- Gate/task evidence: which acceptance criterion was tested and proved.
- GitHub Actions: what ran, on which SHA and with what result.
- T07/T22 checkpoint or handoff mechanisms: validated resumption data where their contracts support it.
- T14 manifest: derived audit baseline, audited path hashes, findings and evidence freshness.
- T16: repository structure, source classification and dependency impact.
- T23/T24: evidence identity/provenance and continuity recovery.

Do **not** add a separate `project_history_index.json`, `ai_context_cache.json`, `gpt_memory_store`, second audit manifest, or second continuity database to solve this problem.

If T14's present schema or T07's existing packet contract lacks a specific field needed for efficient resume, first prove the gap with a targeted review. Then extend the owning existing contract in the authorized T07/T14 work, update its schema and tests together, and preserve backward compatibility where required. Do not add a second owner just because an existing field is inconvenient.

Historical chat files can be retained as communication context. They must not become the source of current task state.

---

## 10. Target AI Request Architecture

The proposed customer-facing path is:

```text
Authenticated Server Request
        |
        v
Validated Request Contract and Size Limits
        |
        v
Trusted Identity / Tenant Context
        |
        v
AI Model Gateway
        |
        +---- Model / Provider Registry
        |
        +---- Policy and Data Classification
        |
        +---- Usage and Cost Guard
        |
        +---- Optional Authorized Retrieval
        |         |
        |         v
        |     Evidence-Bounded RAG
        |
        +---- Optional Bounded Agent Runtime
                  |
                  v
          Existing Governed Tool Gateway
                  |
                  v
        Authorized Business Execution
        (approval where required)
        |
        v
Provider Response / Tool Receipt Validation
        |
        v
Redacted Observability and Usage Accounting
        |
        v
Typed Response or Explicit Failure
```

Cross-cutting boundaries:

- Authentication and domain authorization remain independently enforced.
- Retrieval respects tenant and resource boundaries.
- Model identifiers and provider capabilities are allowlisted.
- Retrieved documents and tool output are untrusted inputs.
- Tool proposals are not tool execution results.
- Request, context, usage, concurrency and retry limits are explicit.
- Sensitive actions require applicable authorization and approval.
- Telemetry preserves evidence without leaking secrets.
- Failure states remain visible and typed.
- Live service activation occurs only after the approved server-side integration path is verified.

The gateway coordinates model requests. It does not become the owner of property inventory, identity, tenant membership, listing eligibility, brokerage rights, commission calculations, financial settlement, Control Center state or GitHub operations.

---

## 11. Dependency-Aware Implementation Order — Match Canonical AI-001 Tasks

The canonical task list is the required sequence:

- T01 — Implement AI Gateway.
- T02 — Implement provider and model registry.
- T03 — Implement embeddings and retrieval integration.
- T04 — Implement RAG pipeline.
- T05 — Implement agent runtime and tools.
- T06 — Implement AI authorization and tenant isolation.
- T07 — Implement cost controls and usage tracking.
- T08 — Implement AI observability and fallback.
- T09 — Run AI safety, security and reliability tests.
- T10 — Freeze AI platform and agents.

The implementation stages below map to those canonical subtasks. They do not create a new task sequence or give this document execution authority.

### T01 — AI Gateway

Confirm live state, inspect the existing package tree and finalize the smallest stable contracts and interfaces.

Potential targets, only after file-owner inspection:

- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/contracts.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/errors.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/ports.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/settings.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/model_gateway.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/__init__.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py`
- `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py`
- `.github/actions/homio-backend-ci/verification/scripts/compile_and_contracts.sh`, only for the authorized test/compile wiring and verification scope.

Requirements:

- deterministic tests with injected providers
- explicit invalid-request and no-provider failures
- clear dependency-injection points
- bounded input/output and timeout contracts
- no live customer-facing provider activation
- no hidden direct dependency on the Control Center or ACRL runtime
- canonical package tests stored under `ai_platform/tests/`
- explicit Python compilation and CI invocation of the three canonical test paths
- no duplicate test files left after the cleanup is independently verified.

#### T01 verification and cleanup order

1. Read the live branch and state before implementation.
2. Read the full gateway, contracts, ports, errors, settings, package exports, tests and current CI script.
3. Read back each canonical test path from GitHub and verify the actual content and blob SHA.
4. Verify the CI script compiles the package and runs `tests/test_contracts.py`, `tests/test_model_gateway.py` and `tests/test_public_contract_stability.py`.
5. Run focused AI tests using the existing backend workflow; do not create a competing workflow.
6. Verify the exact tested SHA, job conclusion, focused AI test count and wider regression result.
7. If root-level copies still exist, compare them with their canonical `tests/` copies. Delete only the obsolete root copies after the canonical paths and CI invocation have been verified.
8. Re-read the live tree after deletion. Run Actions again and inspect the cleanup commit's result.
9. Do not claim cleanup is complete while duplicate paths remain.
10. Do not transition `AI-001-T01` in `state.json` manually. Use the existing Control Center completion procedure when its requirements and evidence are satisfied.

The checkpoint in Section 3.6 is a verified historical example of the AI tests and backend suite passing. Its counts are not permanent requirements and must never replace a current test run.

### T02 — Provider and model registry

Potential targets:

- `model_registry.py`
- `provider_adapters/base.py`
- only the approved provider adapters required by the chosen provider strategy
- registry and adapter tests.

Requirements:

- stable model/provider contracts
- configured allowlists
- capability validation
- normalized provider errors
- secret-safe behavior
- explicit disabled/missing-provider behavior
- tests for unsupported models and configuration mismatch.

### T03 — Embeddings and retrieval integration

Potential targets:

- `embeddings.py`
- `retrieval_adapter.py`
- focused retrieval tests.

Requirements:

- reuse existing search and indexing
- validate vector compatibility
- establish tenant and resource scope
- preserve source identity and provenance
- test missing/stale/malformed retrieval results.

### T04 — RAG pipeline

Potential targets:

- `prompt_templates.py`
- `rag_pipeline.py`
- focused prompt, retrieval, context and source-grounding tests.

Requirements:

- versioned templates
- trusted/untrusted content separation
- prompt-injection regression tests
- context and output limits
- evidence references retained
- unsupported claims declined or qualified by policy.

### T05 — Agent runtime and tools

Potential targets:

- `agent_runtime.py`
- `tool_bridge.py`
- `tests/test_agent_tool_boundaries.py`.

Requirements:

- typed tool proposals
- explicit tool allowlist
- bounded iterations and execution time
- circular-call/replay detection
- no unrestricted shell/database/repository access
- no sensitive mutation until required authorization and execution controls are verified.

Use the stable authorization/usage ports from the beginning. If the required production implementation does not yet exist, the feature must remain safely disabled rather than using permissive test-only behavior.

### T06 — Authorization and tenant isolation

Potential targets:

- `authorization.py`
- `tests/test_authorization_tenant_isolation.py`.

Requirements:

- use existing trusted identity/tenant contracts
- deny missing, invalid or ambiguous identity
- deny cross-tenant retrieval and action access
- validate specific resources and operations
- prove that model output cannot elevate permissions
- prove tools enforce authorization independently of the model
- do not introduce a second identity or membership engine.

### T07 — Cost and usage controls

Potential targets:

- `cost_control.py`
- `tests/test_cost_control.py`.

Requirements:

- request/context/output bounds
- tenant/global usage policy
- concurrent quota enforcement
- idempotent accounting where needed
- known handling for missing or invalid provider usage metadata
- explicit accounting failure behavior
- no false claim that an in-memory test counter is production billing accounting.

### T08 — Observability and fallback

Potential targets:

- `resilience.py`
- `observability.py`
- `tests/test_resilience_observability.py`.

Requirements:

- bounded timeout/retry behavior
- classified error handling
- safe provider fallback only where explicitly allowed
- secret and sensitive-data redaction
- request and policy correlation
- truthful usage and failure status.

### T09 — Security/reliability tests and approved integration

Only after T01–T08 interfaces are stable should the relevant final integration and consolidated verification take place.

Potential targets:

- `tests/conftest.py`
- `tests/test_ai_quality_regression.py`
- `tests/test_data_policy_contracts.py`
- `tests/test_runtime_boundary.py`
- `tests/test_ai_platform_integration.py`
- existing focused tests, updated when they already own the relevant behavior
- existing CI configuration, only where an authorized code/test change needs CI wiring.

Requirements:

- adversarial security checks
- prompt/retrieval grounding evaluation
- tenant isolation
- tool authorization and replay controls
- cost/concurrency behavior
- provider failure/fallback behavior
- redacted telemetry
- existing financial, identity, retrieval, execution, ACRL and frontend regression coverage as applicable.

Integration must use the inspected, existing backend/API boundary and existing CI workflows. Do not create a duplicate backend or workflow.

### T10 — Freeze AI platform and agents

T10 is the canonical freeze task—not a second, independent integration stage.

Before freeze:

- all blocking implementation subtasks are complete
- final integration is already implemented at the approved boundary
- all acceptance criteria have criterion-specific evidence
- required focused, adversarial and wider regression suites pass
- no required safety control is disabled
- exact code/CI source SHA evidence is verified
- customer-facing live-AI status is truthful
- unresolved issues are either fixed or explicitly dispositioned under the authorized policy.

Use the existing Control Center's completion and approval procedure. This blueprint must not perform or simulate the transition.

---

## 12. Acceptance Criteria and Proof Obligations

All six canonical AI-001 acceptance criteria must be verified individually.

| Criterion | Required proof |
|---|---|
| AI-001-AC01 — AI providers are abstracted behind the gateway | Provider-independent contracts; registry and adapter tests; gateway behavior with deterministic provider fakes; provider failures normalized |
| AI-001-AC02 — AI cannot bypass domain authorization | Trusted identity/tenant enforcement; deny-by-default behavior; adversarial cross-tenant and tool-bypass tests |
| AI-001-AC03 — Retrieval is tenant-scoped and rebuildable | Tenant-scoped retrieval; resource checks; source provenance; version/index compatibility; deterministic rebuild/refresh evidence |
| AI-001-AC04 — Model selection and cost controls are configurable | Registry allowlisting; validated configuration; bounded inputs/outputs; concurrency-safe quota tests; explicit usage/accounting status |
| AI-001-AC05 — Agent actions use authorized business tools | Typed proposal; tool schema validation; existing governed gateway; approval and idempotency checks; verified action receipt |
| AI-001-AC06 — Fallback and observability are operational | Timeout/retry behavior; permitted fallback tests; redaction tests; meaningful operational events; truthful failure reporting |

One subtask's unit test does not automatically verify every criterion.

Every criterion's evidence must point to the implementation and tests that prove that specific requirement. Record the source commit, exact Actions run or test output, relevant result, and any explicit limitation.

---

## 13. Security and Adversarial Test Matrix

The security plan should be reviewed against the current OWASP GenAI security resources and relevant risk-management guidance listed in Section 20.

At minimum, test these scenarios.

### 13.1 Identity, authorization and tenant isolation

- missing/malformed identity
- client-supplied tenant differing from trusted membership
- cross-tenant retrieval and cache leakage
- resource-level access denied
- role/permission changes after a prior context was built
- unauthorized tool invocation
- attempts by model text or retrieved instructions to authorize an action
- authorization dependency unavailable
- stale or conflicting policy evidence.

### 13.2 Prompt and context integrity

- direct prompt injection
- indirect injection embedded in retrieved property descriptions, documents, messages or web results
- retrieved text attempting to reveal secrets
- retrieved text instructing an agent to call unauthorized tools
- conflicting or stale source documents
- unsupported factual claims presented with excessive confidence
- source-reference loss during context assembly
- attempts to make the model reveal private system context.

### 13.3 Provider and output safety

- malformed provider response
- unknown model identifier
- unsupported capability
- invalid structured output
- invalid or non-finite embedding vectors
- provider timeout
- repeated transient failure
- provider rate/quota exhaustion
- incompatible fallback model
- missing, malformed or conflicting usage metadata
- secrets in exceptions, nested response objects or telemetry.

### 13.4 Agent and tool safety

- disallowed tool name
- malformed tool schema/arguments
- repeated or circular tool calls
- over-limit agent iterations
- non-idempotent mutation retry
- replay with changed arguments
- missing approval for a sensitive action
- ambiguous tool receipt after timeout
- tool dependency unavailable
- attempted unrestricted code, filesystem, shell or database access.

### 13.5 Resource and cost safety

- oversized input
- excessive retrieval documents
- oversized context/output
- concurrent requests competing for the same quota
- estimated usage mistakenly treated as exact usage
- retry amplification
- cancellation or timeout during usage accounting
- failed reservation or accounting release
- request replay that would double-charge or double-execute an action.

A critical authorization, privacy or integrity regression blocks release even when ordinary tests are green.

---

## 14. Quality Evaluation, Observability and Operational Readiness

### 14.1 AI quality evaluation

Use a deterministic set of representative HOMIO workflows, including:

- natural-language property-brief interpretation
- conversion into supported search criteria
- property comparison grounded in actual retrieved data
- explanation with source references
- handling missing information
- handling conflicting listing details
- refusal/qualification for unsupported valuation, yield, legal or financial claims
- safe response when provider/retrieval service is unavailable
- tool-selection and action-proposal correctness.

For each evaluation, preserve the input fixture, expected invariant, observed result, model/prompt version where applicable and outcome. Keep personal or confidential data out of public fixtures.

Do not set fabricated quality percentages. Agree and document measurable release thresholds before production enablement. Keep quality criteria separate from access-control and business correctness tests.

### 14.2 Observability

At minimum, the operational design should make it possible to distinguish:

- configuration failure
- model/provider resolution failure
- provider timeout or quota exhaustion
- authorization denial
- retrieval failure
- grounding/provenance problem
- usage reservation/accounting failure
- tool execution failure
- successful model response with no tool mutation
- successful authorized action with verified receipt.

Where compatible with the selected instrumentation, consider OpenTelemetry GenAI semantic conventions. Preserve secret redaction and data-minimization requirements regardless of instrumentation library.

### 14.3 Release and operational policy

Before live service enablement, define and test:

- approved provider/model configuration
- required environment settings and secret handling
- request timeout and bounded retry values
- rate/concurrency and quota limits
- data retention and deletion behavior
- monitoring and alerting ownership
- explicit kill-switch/disablement path
- known-good version and rollback procedure
- data residency/provider processing boundaries
- measured availability and quality requirements
- safe behavior when credentials, quota, retrieval or authorization service is unavailable.

The implementation must not invent SLOs or claim operational readiness without a defined and measured verification procedure.

---

## 15. GitHub, CI and Change-Control Rules

Use the existing workflows:

- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`

Do not create duplicate frontend or backend workflows.

### CI requirements

- Confirm existing path filters trigger for relevant AI package, test and workflow changes.
- Verify the actual reusable workflow and test selection before editing CI.
- Ensure newly required test paths exist on the source SHA.
- Preserve all required existing backend/ACRL and financial regressions.
- Add focused AI tests to the owning workflow only after the package and test contracts are stable and the task authorizes the wiring.
- Keep provider secrets out of workflow source, logs and committed artifacts.
- Do not label a run as testing a commit that it did not execute.
- Read the final source and relevant workflow files back from GitHub after a change.
- If a documentation-only change does not trigger a path-filtered workflow, do not modify CI just to generate an unrelated run.

### T01-specific CI requirements

For the current package-owned gateway tests, the existing compile/contract script is:

`.github/actions/homio-backend-ci/verification/scripts/compile_and_contracts.sh`

It must compile the package and explicitly execute the canonical test paths:

- `AUTONOMY_ENGINE/ai_platform/tests/test_contracts.py`
- `AUTONOMY_ENGINE/ai_platform/tests/test_model_gateway.py`
- `AUTONOMY_ENGINE/ai_platform/tests/test_public_contract_stability.py`

Use the existing `.github/workflows/backend-ci.yml` and its reusable verification workflow. Do not create a separate AI workflow.

When verifying a run:

1. Check that the tested commit SHA is the intended commit.
2. Confirm the script on that SHA actually includes the AI package compile and pytest command.
3. Inspect the test summary for the focused AI invocation separately from the agent-entrypoint test and the full regression suite.
4. Check the overall workflow and relevant jobs.
5. Do not infer AI test success from the full ACRL suite count alone.
6. If duplicate test paths are removed, verify a new successful run against the post-deletion commit.
7. Do not treat the Section 3.6 checkpoint as proof for future commits.

### File-change classification

Every target must receive one classification after live inspection:

- `ADD` — exact path is absent and no existing owner provides the responsibility.
- `UPDATE` — existing owner has a demonstrated defect or defined integration requirement.
- `VERIFY` — inspect evidence before deciding whether the file is correct.
- `NO CHANGE` — current implementation already satisfies the requirement.
- `BLOCKED` — required authority, dependency or evidence is missing.

A failed guessed URL, stale workspace or filename search alone is not proof that a source file is absent.

### Write and readback protocol

For every approved implementation batch:

1. Read live branch HEAD and canonical state.
2. Read each exact target and its current blob SHA.
3. Inspect the owner, imports, contracts and related tests.
4. Record path classifications and the planned changes.
5. Preserve the exact pre-write baseline.
6. Abort if the live branch changes unexpectedly before the write.
7. Use the owner-approved GitHub workflow or the owner's explicit GitHub UI workflow.
8. Read the saved files and exact resulting commit back from GitHub.
9. Confirm parent SHA and changed paths.
10. Run focused tests and applicable regressions.
11. Verify the relevant GitHub Actions result against the exact tested SHA.
12. Use the existing Control Center for formal state transitions.

No file is considered saved merely because content was prepared in chat. No code is considered verified merely because the commit exists.

---

## 16. Evidence Packet for Each Subtask

Each implementation batch must finish with a concise record containing:

```text
AI-001 IMPLEMENTATION EVIDENCE

Canonical repository and branch:
Observed baseline HEAD:
Canonical state blob SHA:
Current AI-001 task/subtask:
Target paths:
Path classifications:
Relevant existing owners:
Commit SHA and URL:
Changed-path list:
Remote content readback:
Focused tests and actual results:
AI package test paths:
AI package test result:
Duplicate test copies / cleanup status:
Relevant regression tests:
GitHub Actions URL:
Exact tested SHA:
Relevant job conclusions:
Acceptance criteria proven:
Security/dependency review:
Known limitations or blockers:
Canonical task status after readback:
Next task as reported by canonical state:
```

Rules:

- Mark unknown fields explicitly.
- Distinguish a local/focused test from GitHub Actions.
- Distinguish file save, code verification, acceptance-criteria verification and formal task completion.
- Keep historical failed-run records and their reasons.
- Do not invent test counts, timestamps, evidence IDs or acceptance status.
- Do not manually add a completed status to canonical state.
- Where there is a gap, report the exact blocker instead of declaring the task complete.

---

## 17. Failure, Recovery and Conflict Protocol

When an implementation or verification step fails:

1. Read the exact failing assertion, job step or API result.
2. Confirm the commit SHA actually tested.
3. Read the current target and its direct dependencies from the canonical branch.
4. Determine whether the problem is in code, configuration, test selection, authority, dependency, environment or evidence.
5. Check for an existing owner or tested equivalent before adding a file.
6. Propose the minimal ownership-correct correction.
7. Preserve unrelated passing behavior.
8. Re-run the focused failing tests and the relevant regression scope.
9. Confirm the new commit and content by remote readback.
10. Verify CI against the new applicable SHA.
11. Keep the failure in the historical audit record and record how it was resolved.

For GitHub access failures, classify the failure correctly. Recover only through permitted authenticated mechanisms; never bypass repository permissions, branch protections, rulesets, rate limits or approvals.

When a branch or canonical state changes during a batch, stop and refresh the relevant baseline. Do not use a stale manifest or prior chat response to force the old plan to continue.

---

## 18. Out of Scope Unless Separately Authorized

This blueprint does not authorize:

- Rebuilding the HOMIO / REOS platform.
- Replacing the canonical search or indexing system.
- Replacing the existing identity or tenant engines.
- Replacing ACRL, the Control Center or repository coordination.
- Creating a second project-history, resume, memory, audit or evidence system.
- Adding a new persistence layer for conversation history without approved data policy.
- Enabling arbitrary shell, database, repository or filesystem access to an LLM.
- Running sensitive mutations before authorization, approval and execution boundaries are verified.
- Enabling customer-facing live-AI status based only on a successful build.
- Modifying unrelated F01–F13 frontend functionality.
- Reworking financial logic that is already owned by the approved financial domain.
- Manually changing canonical task state.
- Bypassing GitHub permissions or formal controller transitions.
- Mixing Imperium AI into HOMIO / REOS.
- Claiming production readiness without measured verification.

Any new domain responsibility must be reviewed with its existing owner before implementation.

---

## 19. Definition of Done

### Architecture

- One verified owner per responsibility.
- Stable public/provider-independent contracts.
- No duplicate state, memory, identity, retrieval, tool or history engines.
- Customer-facing AI and development-agent continuity remain separate.
- Existing HOMIO business and governance boundaries are preserved.

### Project context and audit efficiency

- Current task is reconstructed from live canonical state.
- Current source and exact branch HEAD are verified.
- T07/T14/T16/T23/T24 ownership is reused.
- Fast resume is claimed only after the existing manifest and evidence pass validation.
- An uninitialized manifest triggers the required baseline process.
- Changed paths and affected dependents receive targeted audit when the verified delta allows it.
- Context packets include exact source and test references.
- Historical chat and stale snapshots never become task authority.
- No redundant project-history cache or duplicate audit engine is introduced.

### AI gateway and providers

- Provider-independent gateway.
- Validated inputs and outputs.
- Configured provider/model allowlist.
- Explicit errors and safe fallback.
- Bounded request, context, tool and retry use.
- Usage and cost policy enforced.

### Security and privacy

- Trusted identity and tenant context.
- Resource/action authorization at the authoritative boundary.
- No unauthorized tool execution.
- No cross-tenant retrieval/cache leakage.
- Prompt injection and untrusted output risks tested.
- Secret and sensitive-data redaction verified.
- Data retention and deletion behavior defined where persistence exists.
- Sensitive actions retain their applicable approval requirements.

### Retrieval and agents

- Retrieval is tenant-scoped and traceable.
- Derived context is rebuildable.
- Model output is distinguished from source-backed facts.
- Agent actions are bounded and authorized.
- Tool proposals are not mistaken for successful execution.
- Action receipts and idempotency rules are preserved.

### Verification and release

- Focused contract tests pass.
- Adversarial security tests pass.
- Quality/evaluation regressions pass at the agreed release threshold.
- Required existing financial, identity, retrieval, execution, ACRL and frontend regressions remain enabled and pass as applicable.
- Exact commit, changed paths and saved content are independently verified.
- Relevant Actions results apply to the exact tested SHA.
- All AI-001 acceptance criteria have individual evidence.
- The existing Control Center records the required transitions.
- T10 freeze/approval happens only after all blocking work is complete.

---

## 20. External Security and Risk References

These sources inform the review; they do not replace HOMIO's canonical architecture, policy, authorization or acceptance tests.

1. **OWASP GenAI Security Project — 2026 LLM Top 10**  
   https://github.com/GenAI-Security-Project/GenAI-LLM-Top10  
   Use for evolving checks covering prompt injection, sensitive-information disclosure, excessive agency, supply-chain risk, data/model poisoning, unbounded consumption, misinformation, hidden-context exposure, vector/embedding weaknesses and improper output handling.

2. **NIST AI Risk Management Framework — Generative AI Profile, NIST AI 600-1**  
   https://doi.org/10.6028/NIST.AI.600-1  
   Use as risk-management guidance for design, evaluation, deployment and monitoring; do not claim that referring to it alone establishes regulatory compliance.

3. **OpenTelemetry GenAI Semantic Conventions**  
   https://github.com/open-telemetry/semantic-conventions-genai  
   Consider when choosing instrumentation for GenAI spans, metrics and events. Adoption must still follow HOMIO's secret-redaction and data-minimization policies.

Review external references again before a major security/release decision; do not freeze the platform around an obsolete checklist.

---

## 21. Final Implementation Rules

This file is the single detailed AI-001 implementation blueprint. It is subordinate to the live canonical state and approved architecture.

Before every implementation batch:

1. Re-read canonical state and the live repository HEAD.
2. Read the active task/subtask and applicable task-specific acceptance policy.
3. Confirm the target files, owners, contracts and tests.
4. Use the existing fast-resume mechanism only when its current assessment validates it.
5. If the manifest or source identity is invalid, stale or unresolved, perform the required authorized reconciliation.
6. Use the exact path and action classification for each change.
7. Provide complete file content when a full replacement is required.
8. Preserve unrelated working behavior.
9. Verify the saved content, commit, tests and CI.
10. Report actual evidence and blockers without guessing.

### Editing and saving this blueprint

- The canonical destination is `REOS_CONTROL_CENTER/architecture/AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md`.
- Update this same file; do not delete it and recreate a separate copy.
- The owner may use the GitHub web editor to replace the complete content.
- After saving, read the exact file back from `reos-development` and verify its resulting commit and content.
- This documentation-only update does not, by itself, require changing backend CI or `data/state.json`.
- If the document change does not trigger a workflow because of path filters, report that fact instead of inventing a CI result.
- Future implementation batches must refresh Section 3.6 from live sources before relying on it.

**Blueprint version:** 2.0  
**Blueprint status:** Implementation reference — not execution authority  
**Original canonical task at the Version 2.0 baseline:** `AI-001-T01 — Implement AI Gateway`  
**Historical canonical state path:** `REOS_CONTROL_CENTER/data/state.json`  
**Required context/audit rule:** Reuse existing ACRL continuity and repository-intelligence ownership; no duplicate history or audit system.

**End of blueprint.**
