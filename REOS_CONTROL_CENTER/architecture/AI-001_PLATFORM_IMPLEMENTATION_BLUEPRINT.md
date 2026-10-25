# HOMIO / REOS
# AI-001 — Production-Grade AI Platform Implementation Blueprint

**Document ID:** HOMIO-AI-001-BLUEPRINT-001  
**Version:** 1.0  
**Status:** IMPLEMENTATION REFERENCE — NOT EXECUTION AUTHORITY  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical branch:** `reos-development`  
**Document path:** `REOS_CONTROL_CENTER/architecture/AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md`

---

## 1. Purpose

Build the HOMIO / REOS AI Platform as a secure, provider-independent, observable, cost-controlled and recoverable system.

This blueprint defines the intended file structure, module ownership, dependency rules, implementation sequence, testing requirements and completion criteria for the complete `AI-001` gate.

The objectives are to:

1. Avoid duplicate modules and competing sources of truth.
2. Stabilize public contracts before implementing provider integrations.
3. Reuse verified HOMIO / REOS domain, identity, retrieval, execution and governance infrastructure.
4. Isolate AI provider changes from domain code and user-interface code.
5. Prevent unauthorized model, tenant, retrieval and business-tool access.
6. Make failures explicit, bounded and observable.
7. Consolidate integration wiring and final regression work near the end.
8. Preserve already-passing backend, frontend, financial and ACRL behavior.
9. Require verified GitHub evidence and Control Center transitions for task completion.

**Reliability objective:** Prevent known architectural, security, integration and regression failures through explicit contracts and automated verification. No document or test suite can honestly guarantee that future defects will never occur.

---

## 2. Canonical Authority and Non-Negotiable Rules

The following sources retain their established responsibilities.

| Concern | Authority |
|---|---|
| Active gate, task and execution state | `REOS_CONTROL_CENTER/data/state.json` and the existing Control Center |
| Canonical code and committed history | GitHub `reos-development` |
| Agent operating contract | `REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py` |
| Task execution sequence | Canonical execution plan and existing Control Center |
| Business identity and tenant isolation | Existing identity and tenant domain contracts |
| Business-tool execution | Existing governed execution and tool boundaries |
| AI operator governance during platform development | Existing ACRL T15 |
| Backend verification | Existing `.github/workflows/backend-ci.yml` |
| Frontend verification | Existing `.github/workflows/frontend-ci.yml` |
| AI implementation structure | This blueprint, subordinate to canonical authority |

Rules:

- Never edit `data/state.json` manually to manufacture a task transition or gate completion.
- Never treat this document, chat history, a test fixture or an AI-generated plan as execution authorization.
- Never assume a missing file without checking the live GitHub tree.
- Never replace an existing module merely because a new implementation is convenient.
- Never create a duplicate identity engine, tenant registry, retrieval engine, tool executor, event system, agent-governance system or state store.
- Never expose provider API keys in frontend code, committed configuration, exception text or logs.
- Never trust a tenant identifier supplied by a client without establishing its authorized context.
- Never permit an LLM response to authorize itself or approve a business mutation.
- Never report an untested commit as verified.
- Never weaken an existing test, authorization rule, workflow or branch policy just to obtain a green run.
- Never claim the live AI service is connected until the real server-side path has been verified.
- Never mix the separate Imperium AI project into HOMIO / REOS.

If canonical execution state changes, reread it and reconcile this blueprint before proceeding.

---

## 3. Verified Starting Baseline

At blueprint preparation, the canonical state reports:

- Gate: `AI-001`
- Current subtask: `AI-001-T01`
- Execution mode: `CONTROL_CENTER_DRIVEN`
- Previous gate: `CORE-008`, status `APPROVED`
- Canonical source commit: `a30007031cc55674a145e040f83bfe2ae9cdf9d4`
- Canonical state blob observed: `38521091f3a40c990180ab1f6c59374ac0810745`

The baseline is time-dependent. Before each implementation batch, recheck the live branch, canonical state, target paths and relevant workflow results.

### Existing infrastructure identified during initial inventory

| Existing path | Initial disposition |
|---|---|
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/execution/tool_gateway.py` | Reuse as the governed business-tool policy boundary; audit before integration |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/execution/execution_pipeline.py` | Reuse only through its established contracts |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/` | Reuse identity, tenant and membership contracts |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/search_matching/` | Reuse domain search and retrieval capabilities |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/budgets/context_budget.py` | Reuse context-budget infrastructure where compatible |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/event_platform/event_observability.py` | Reuse event observability where compatible |
| `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/T15_AI_Operator_Autonomy/` | Preserve development-time operator governance; do not treat it as the customer-facing AI runtime |
| `REOS_CONTROL_CENTER/Frontend/src/features/f08_ai/` | Preserve the existing truthful service boundary and UI experience |

The initial inventory did not identify a clearly dedicated, complete AI model gateway and provider/model registry. This is a discovery result, not permission to assume every possible equivalent is absent.

Before declaring any new path `ADD`, search the current tree, inspect imports and dependencies, and identify any equivalent responsibility.

---

## 4. Target Architecture

The intended request path is:

```text
Authenticated Request
        |
        v
Request Contract and Input Limits
        |
        v
AI Model Gateway
        |
        +---- Model / Provider Registry
        |
        +---- Authorization and Tenant Policy
        |
        +---- Usage / Cost Controls
        |
        +---- Optional Retrieval and RAG
        |
        +---- Authorized Agent / Tool Bridge
        |
        v
Provider Adapter
        |
        v
Response Validation and Redaction
        |
        v
Auditable Response / Explicit Failure
```

Cross-cutting controls:

- Request and output limits
- Authorization at the business boundary
- Tenant-scoped retrieval
- Provider and model allowlists
- Bounded timeouts and retries
- Usage accounting and quota enforcement
- Structured, redacted observability
- Deterministic offline test doubles
- Evidence-backed result provenance
- Explicit human-approval boundaries

The model gateway coordinates model requests. It does not become the owner of business data, identity, tenant membership, property ranking, commission calculations, authorization decisions or Control Center state.

---

## 5. Proposed File Structure

Root:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/ai_platform/`

```text
ai_platform/
|
|-- __init__.py
|-- contracts.py
|-- errors.py
|-- ports.py
|-- settings.py
|-- model_registry.py
|-- model_gateway.py
|
|-- provider_adapters/
|   |-- __init__.py
|   |-- base.py
|   |-- [approved provider adapter modules added only when needed]
|
|-- embeddings.py
|-- retrieval_adapter.py
|-- rag_pipeline.py
|-- authorization.py
|-- agent_runtime.py
|-- tool_bridge.py
|-- cost_control.py
|-- resilience.py
|-- observability.py
|
|-- tests/
    |-- conftest.py
    |-- test_contracts.py
    |-- test_model_registry.py
    |-- test_model_gateway.py
    |-- test_provider_adapters.py
    |-- test_authorization_tenant_isolation.py
    |-- test_retrieval_and_rag.py
    |-- test_agent_tool_boundaries.py
    |-- test_cost_control.py
    |-- test_resilience_observability.py
    |-- test_ai_platform_integration.py
    |-- test_public_contract_stability.py
```

This is a proposed layout, not a claim that these files already exist.

Each proposed path must be reclassified against the live tree before implementation. If an equivalent verified implementation already exists, reuse or extend it rather than creating a duplicate.

Provider-specific adapter files will be added only after the approved provider strategy and existing dependency inventory are established. Do not add multiple speculative integrations at the beginning.

The HTTP/API integration location is intentionally not hard-coded here. First inspect the existing backend entry points, server framework, authentication path and deployment conventions. Add one narrow integration at the existing architectural boundary. Do not create a competing backend or expose provider credentials through the Next.js client.

---

## 6. File Ownership and Stable Interfaces

### 6.1 `contracts.py`

Owns the stable, provider-independent data contracts:

- Model request
- Model response
- Usage metadata
- Model capability description
- Request identity and tenant context references
- Evidence/source references
- Explicit completion and failure status
- Trace/correlation identifier

Requirements:

- Use typed, immutable request/result structures where appropriate.
- Validate required values and supported data types.
- Bound input and output sizes.
- Reject invalid or ambiguous requests explicitly.
- Do not place secrets, live credentials or mutable global state in contracts.
- Do not store authoritative business records in AI conversation state.

### 6.2 `errors.py`

Defines a small, stable error taxonomy covering:

- Invalid request
- Unauthorized or invalid tenant context
- Unknown or disallowed model
- Provider unavailable
- Provider timeout
- Provider response invalid
- Retrieval failure
- Usage limit exceeded
- Tool authorization denied
- Temporary dependency failure
- Internal unexpected failure

Errors must have stable machine-readable classifications and safe public messages.

Never return raw provider exception text, credentials or internal infrastructure details to end users.

### 6.3 `ports.py`

Defines dependency-inversion interfaces for:

- Text-generation provider
- Embedding provider
- Model registry
- Authorization policy
- Retrieval provider
- Usage/accounting boundary
- Tool execution boundary
- Observability sink

Interfaces must depend on contracts, not on a particular provider SDK.

Test fakes implement these interfaces without a network connection.

### 6.4 `settings.py`

Defines validated non-secret runtime configuration:

- Enabled providers
- Model allowlist
- Request and output limits
- Timeout policy
- Retry policy
- Cost and usage limits
- Retrieval limits
- Feature availability

Secrets are supplied from the approved runtime secret/configuration mechanism. Secret values must not be serialized into diagnostic reports.

Configuration defaults must be safe. Invalid settings fail during startup or request preflight rather than silently selecting an arbitrary provider.

### 6.5 `model_registry.py`

Owns selection and validation of configured models.

Requirements:

- Explicit allowlist of providers and model identifiers.
- Capability checks before dispatch.
- Bounded context/output settings.
- Approved model aliases must resolve deterministically.
- Unknown identifiers are rejected.
- No arbitrary dynamic module import based on request input.
- Do not rely on a model's claimed capabilities without validating registered configuration.
- Provider/model availability must be distinguishable from authorization.

The registry is not an identity registry and is not allowed to authorize users or tenants.

### 6.6 `model_gateway.py`

Owns orchestration of one governed AI request:

1. Validate the request contract.
2. Validate the trusted request context.
3. Resolve an allowlisted model.
4. Apply request and usage limits.
5. Call the authorization and provider interfaces.
6. Enforce timeout and retry policy.
7. Validate the provider response.
8. Record safe usage and observability data.
9. Return a typed response or an explicit error.

The gateway must not:

- Read or mutate `data/state.json` as application runtime data.
- Access business tables directly.
- Bypass the established tool boundary.
- Treat a provider response as trusted evidence.
- Silently switch tenants or models after a failure.
- Invent a successful result when no provider succeeded.

### 6.7 `provider_adapters/base.py`

Defines the shared provider-adapter contract.

Requirements:

- Map provider-specific inputs to the common request.
- Map successful provider responses to the common response.
- Normalize provider errors.
- Preserve usage metadata where the provider supplies it.
- Apply request and response bounds.
- Never log credentials or full sensitive payloads by default.

Provider-specific modules remain isolated behind this contract.

### 6.8 `embeddings.py`

Owns embedding request validation and adaptation.

Requirements:

- Use an approved embedding model from the registry.
- Validate dimensions, numeric values and finite values.
- Track model/version compatibility.
- Reject malformed or incompatible vectors.
- Avoid embedding sensitive fields unless an explicit data policy permits them.
- Do not independently implement a second vector index.

### 6.9 `retrieval_adapter.py`

Connects AI retrieval to the established HOMIO / REOS search infrastructure.

Requirements:

- Reuse existing domain search contracts.
- Require trusted tenant context.
- Apply tenant constraints before returning candidates.
- Preserve source identity and retrieval provenance.
- Validate the result contract.
- Keep property ranking and business eligibility with their existing domain owners.
- If the established retrieval service is unavailable, return a typed failure or explicitly permitted safe fallback.

No duplicate Qdrant, indexing or property-ranking system may be introduced by the AI gateway.

### 6.10 `rag_pipeline.py`

Owns evidence-grounded context assembly.

Requirements:

- Pass only authorized retrieval results to the model.
- Preserve source references and relevant provenance.
- Bound retrieved documents, context size and output size.
- Treat retrieved text as untrusted input rather than executable instruction.
- Defend against prompt injection and unauthorized tool instructions originating in retrieved documents.
- Distinguish sourced facts from model-generated interpretation.
- Reject or qualify unsupported factual claims according to the product policy.
- Rebuild derived retrieval context from authoritative domain data rather than using stale AI state as the source of truth.

### 6.11 `authorization.py`

Integrates with existing identity, tenant and applicable authorization contracts.

Requirements:

- Authorization context originates from a trusted authentication boundary.
- Client-supplied tenant IDs are not proof of membership.
- Validate access to the specific action and resource.
- Default to denial when required authorization evidence is missing.
- Avoid keeping a separate identity or tenant database in the AI package.
- Do not allow an LLM to approve its own action.
- Do not interpret a model's textual claim that a user is authorized as authorization evidence.

### 6.12 `agent_runtime.py`

Coordinates bounded agent work.

Requirements:

- Make the allowed tool set explicit.
- Validate model-proposed action structures before dispatch.
- Enforce maximum iterations, tool calls, time and context budgets.
- Detect repeated or circular tool calls.
- Require evidence and authorization for applicable actions.
- Keep proposals separate from executed actions.
- Require appropriate approval for sensitive or irreversible business mutations.
- Record why an operation stopped, succeeded or was blocked.

The agent runtime does not replace T15 operator governance or the existing execution controller.

### 6.13 `tool_bridge.py`

Connects agents to approved business tools.

Requirements:

- Reuse existing tool and execution boundaries.
- Validate action schema and arguments.
- Enforce authorization independently of model output.
- Do not provide unrestricted Python, shell, repository or database access.
- Do not bypass idempotency, audit, approval or business-domain validation.
- Do not execute mutations while the required authorization path is unimplemented or unavailable.
- Validate the resulting action receipt through the existing verification contract.

An LLM response is an untrusted action proposal until the authorized execution boundary accepts it.

### 6.14 `cost_control.py`

Owns AI-specific request limits and usage controls.

Requirements:

- Enforce configured token/context/output bounds.
- Track provider usage when available.
- Distinguish estimated usage from provider-reported usage.
- Apply per-tenant and global limits through an agreed durable accounting boundary.
- Handle concurrent requests without allowing quota overspend through race conditions.
- Make accounting idempotent where request replay is possible.
- Fail closed or follow a specifically approved policy if usage control cannot be established.
- Never treat an in-memory counter as a durable production ledger.

Reuse the existing context budget. Do not build a second general-purpose budget manager.

### 6.15 `resilience.py`

Defines safe failure handling.

Requirements:

- Explicit connection/request timeouts.
- Bounded retries only for classified transient failures.
- No unbounded retry loops.
- No retry of unauthorized operations.
- No blind retry of non-idempotent tool mutations.
- Circuit breaking or provider health suppression only if the existing runtime conventions support it.
- Fallback must preserve tenant, authorization and response-contract boundaries.
- Never invent an AI answer to disguise provider failure.
- Expose whether the response came from the requested model, a permitted alternate or a non-AI fallback.

### 6.16 `observability.py`

Provides redacted, structured operational events.

Capture where available:

- Correlation/trace ID
- Provider and model identifiers
- Operation category
- Duration and outcome
- Normalized failure classification
- Token and usage metadata
- Retry/fallback information
- Policy decision references

Do not log:

- API keys, access tokens or cookies
- Full authentication headers
- Unnecessary personally identifiable information
- Entire prompts or retrieved documents by default
- Raw provider exception objects
- Secrets embedded in nested dictionaries or error messages

Telemetry must be safe to emit even when the provider or downstream service fails.

---

## 7. File Change Protocol

Every target receives exactly one initial classification after live inspection:

- `ADD`: no equivalent owner exists and architecture permits the new responsibility.
- `UPDATE`: an existing owner has a demonstrated defect or requires a defined integration.
- `NO CHANGE`: the existing implementation already satisfies the requirement.
- `VERIFY`: evidence is incomplete and a targeted check is required.
- `BLOCKED`: authorization, dependency, interface or required evidence is missing.

No `ADD` decision may be based solely on a stale checkout, failed guessed URL or a file-name search.

### Change-size rules

1. Freeze public contracts before implementing downstream modules.
2. Prefer additive, backward-compatible interfaces.
3. Avoid unrelated refactoring during AI-001 implementation.
4. Keep provider-specific logic isolated.
5. Do not make frontend, backend workflow and provider configuration edits prematurely.
6. Collect stable integration points and wire them together in the designated final integration phase.
7. Use a full-file replacement only when necessary and provide the complete current intended file content.
8. If an existing file requires a change, inspect and preserve its unrelated working behavior.
9. Do not ask the owner to combine multiple guessed fragments into a file.
10. Before each later batch, check the exact path and latest branch HEAD again.

---

## 8. Dependency-Aware Implementation Order

The canonical subtask order remains authoritative. The architectural dependency rules below determine how each task is implemented without prematurely enabling unsafe functionality.

### Stage 0 — Preflight and file inventory

- Confirm the active canonical subtask.
- Inspect the full relevant package tree and dependencies.
- Inspect backend entry points and existing service conventions.
- Identify existing tests and their actual CI selection.
- Verify each proposed target's path and responsibility.
- Record `ADD`, `UPDATE`, `NO CHANGE`, `VERIFY` or `BLOCKED`.
- Do not change canonical state.

### Stage 1 — AI-001-T01: Implement AI Gateway

Freeze the contracts and add the minimum gateway foundation:

- `contracts.py`
- `errors.py`
- `ports.py`
- `settings.py`
- `model_gateway.py`
- `test_contracts.py`
- `test_model_gateway.py`
- `test_public_contract_stability.py`

Add or update only those files confirmed necessary by the preflight.

The gateway must work with injected test doubles and must fail explicitly when no permitted provider is configured.

Do not enable a live provider or customer-facing live AI route merely because the core interfaces exist.

### Stage 2 — AI-001-T02: Provider and model registry

Implement:

- `model_registry.py`
- `provider_adapters/base.py`
- Approved provider adapters only where required
- `test_model_registry.py`
- `test_provider_adapters.py`

Prove model allowlisting, configuration validation, provider error normalization, compatibility checks and secret-safe behavior.

### Stage 3 — AI-001-T03: Embeddings and retrieval

Implement:

- `embeddings.py`
- `retrieval_adapter.py`
- `test_retrieval_and_rag.py` retrieval-focused cases

Reuse the canonical search and indexing infrastructure. Establish tenant isolation, vector compatibility and evidence provenance before the RAG pipeline is connected to live models.

### Stage 4 — AI-001-T04: RAG pipeline

Implement:

- `rag_pipeline.py`
- Evidence/context assembly tests
- Tenant isolation and prompt-injection regressions

Do not mark retrieved data as authoritative merely because an embedding or model returned it.

### Stage 5 — AI-001-T05: Agent runtime and tools

Implement:

- `agent_runtime.py`
- `tool_bridge.py`
- `test_agent_tool_boundaries.py`

Use explicit authorization and usage-control interfaces from the start. Live sensitive tool mutations remain blocked until their required policy, tenant, approval and execution paths are implemented and verified.

### Stage 6 — AI-001-T06: AI authorization and tenant isolation

Implement:

- `authorization.py`
- `test_authorization_tenant_isolation.py`

Prove cross-tenant denial, invalid/missing identity denial, resource-level authorization and non-bypassable tool enforcement.

This subtask must strengthen the execution path introduced in T05, not create a second identity engine.

### Stage 7 — AI-001-T07: Cost controls and usage tracking

Implement:

- `cost_control.py`
- `test_cost_control.py`

Prove context/output caps, per-tenant limits, concurrent quota checks, accounting behavior and safe handling of missing usage data.

### Stage 8 — AI-001-T08: Observability and fallback

Implement:

- `resilience.py`
- `observability.py`
- `test_resilience_observability.py`

Prove bounded retry behavior, timeout handling, valid fallback boundaries, secret redaction and meaningful provider failure evidence.

### Stage 9 — AI-001-T09: AI safety, security and reliability verification

Consolidate:

- `tests/conftest.py`
- `test_ai_platform_integration.py`
- Remaining contract, adversarial and regression cases
- Existing relevant identity, search, execution and event regression suites

Finish all required implementation fixes before final workflow wiring.

### Stage 10 — Final integration and freeze preparation

Only after the core modules and interfaces are stable:

- Finalize runtime configuration wiring.
- Add the narrow backend/API integration at the verified existing service boundary.
- Wire the existing backend CI workflow to the stable AI package and regression suites.
- Update F08 live-service documentation/connection flags only when the real service path is operational and verified.
- Run the consolidated tests and existing regressions.
- Perform security and architecture review.
- Record exact commit and test evidence.
- Use the existing Control Center for completion transitions.

Do not create a second backend workflow or a new state-transition mechanism.

### Stage 11 — AI-001-T10: Freeze AI platform and agents

Freeze only after all blocking subtasks are complete, all acceptance criteria are verified, required regression suites pass, and the existing Control Center authorizes the final transition.

---

## 9. Acceptance-Criteria Traceability

All six acceptance criteria must have criterion-specific evidence.

| Criterion | Required proof |
|---|---|
| `AI-001-AC01` — AI providers are abstracted behind the gateway | Stable provider contract, registry enforcement and provider-independent gateway tests |
| `AI-001-AC02` — AI cannot bypass domain authorization | Trusted identity/tenant enforcement, deny-by-default behavior and adversarial bypass tests |
| `AI-001-AC03` — Retrieval is tenant-scoped and rebuildable | Tenant-scoped source retrieval, provenance and deterministic reconstruction tests |
| `AI-001-AC04` — Model selection and cost controls are configurable | Model allowlisting, valid configuration, bounds and concurrent usage-limit tests |
| `AI-001-AC05` — Agent actions use authorized business tools | Tool schema, authorization, execution-boundary and approval tests |
| `AI-001-AC06` — Fallback and observability are operational | Timeout/retry/fallback behavior, redaction and operational event tests |

Passing one subtask's tests does not automatically verify every acceptance criterion.

Acceptance evidence must identify the implementation commit, the actual successful CI run, the relevant test results and the observed behavior.

---

## 10. Test Strategy

### 10.1 Fast deterministic tests

Run focused tests for every module during implementation. Use deterministic fake providers and test doubles. Ordinary contract tests must not require a paid model call or live API key.

### 10.2 Adversarial security cases

Include at least:

- Missing, malformed and over-sized requests.
- Unknown or unapproved model identifiers.
- Untrusted client-supplied tenant IDs.
- Cross-tenant retrieval attempts.
- Unauthorized tool invocation.
- Malformed provider output and invalid embedding vectors.
- Prompt injection in retrieved documents.
- Secret leakage through errors or telemetry.
- Provider timeout and repeated transient failure.
- Rate/quota exhaustion and concurrent requests.
- Retry loops and circular agent tool calls.
- Attempts to make a model response self-authorize.
- Attempts to disguise failed model calls as successful AI responses.
- Provider fallback across incompatible models or forbidden data scopes.

### 10.3 Integration and regression

The final test stage must cover:

1. AI contract and gateway behavior.
2. Registry and provider adapter compatibility.
3. Retrieval and RAG provenance.
4. Identity and tenant isolation.
5. Agent/tool execution boundaries.
6. Cost, quota and usage behavior.
7. Resilience and telemetry.
8. Relevant existing domain and execution regressions.
9. Backend CI workflow behavior.
10. Frontend service-boundary behavior where integration changes it.

Do not invent expected test counts. Report the actual test counts emitted by the verified run.

### 10.4 Failure protocol

If any test fails:

1. Identify the failing assertion and actual error.
2. Inspect the exact current file and relevant dependency.
3. Establish the minimal ownership-correct fix.
4. Preserve unrelated passing behavior.
5. Run focused regressions.
6. Run the relevant wider suite after the fix.
7. Recheck the exact tested commit and GitHub Actions result.
8. Do not mark the subtask complete while required verification is failing.

---

## 11. Integration and Workflow Rules

The final wiring batch must use the existing workflow and service structure.

- Reuse `.github/workflows/backend-ci.yml`.
- Reuse `.github/workflows/frontend-ci.yml`; do not duplicate it.
- Keep backend AI provider credentials out of workflow logs and repository files.
- Keep frontend components isolated from ACRL and Control Center state files.
- Keep provider calls behind the server-side gateway.
- Do not activate `AI_LIVE_SERVICE_CONNECTED` merely because the UI builds successfully.
- Validate environment configuration and missing-secret behavior explicitly.
- Never disable existing regression steps to make a run green.
- Verify branch, commit SHA, job conclusion and actual failed/passed steps.
- Read back committed files from the canonical branch after every implementation batch.
- Use the existing controller for task transitions and final approval.

---

## 12. Completion and Evidence Rules

A subtask is complete only when:

- Its required implementation is committed.
- Its defined tests pass for the verified commit.
- Applicable existing regressions pass.
- Security and dependency boundaries remain intact.
- The canonical controller records the transition.
- The latest canonical state confirms the task status.

The AI-001 gate is complete only when:

- T01 through T10 meet their required completion policies.
- AC01 through AC06 are individually `VERIFIED`.
- Backend, security and applicable integration regressions pass.
- The exact code and workflow results are verifiable.
- The final approval occurs through the existing Control Center.
- Canonical state read-back reports the approved/frozen gate and correct next task.

Do not manually edit state JSON, create fake evidence, infer completion from file existence or treat this blueprint as an approval.

---

## 13. Out of Scope Unless Separately Authorized

This blueprint does not authorize:

- Rebuilding the entire HOMIO / REOS platform.
- Replacing the property search engine.
- Creating a second identity or tenant system.
- Creating a second agent governance or autonomy engine.
- Replacing ACRL, the Control Center or repository coordination.
- Enabling arbitrary shell/database/file access for models.
- Launching live provider calls without approved configuration.
- Inventing property data, financial facts or verified market information.
- Changing unrelated F01–F13 frontend functionality.
- Mixing another project into HOMIO / REOS.
- Bypassing Control Center, test, permission or approval rules.

Any new domain responsibility must receive an explicit architecture review before implementation.

---

## 14. Definition of Done

```text
ARCHITECTURE
  One owner per responsibility
  Stable public contracts
  No duplicate engines or state authorities

AI GATEWAY
  Provider-independent
  Validated inputs and outputs
  Explicit failures
  Bounded resource use

SECURITY
  Trusted identity and tenant scope
  Default-deny authorization
  No unauthorized tool execution
  No secret leakage

RETRIEVAL / RAG
  Tenant-scoped data
  Provenance retained
  Injection-resistant context handling
  Rebuildable derived context

OPERATIONS
  Bounded retries and timeouts
  Explicit fallback
  Usage and cost controls
  Redacted observability

TESTS
  Focused contracts
  Adversarial security
  Integration regressions
  Existing suites preserved

GITHUB
  Exact commit verified
  Actions result verified
  Saved content read back
  Canonical state transitioned by controller

RELEASE
  All blocking subtasks complete
  AC01–AC06 individually verified
  Explicit Control Center approval
```

**Blueprint status:** READY FOR REPOSITORY REVIEW AND IMPLEMENTATION PLANNING  
**Execution authority:** Existing Control Center and canonical state  
**Current canonical next task at preparation:** `AI-001-T01 — Implement AI Gateway`

**End of blueprint.**
