# HOMIO / REOS — Section 20 External Security and Risk Reference Audit

**Document ID:** `HOMIO-AI-001-SECTION-20-REFS-001`  
**Record type:** External security reference validation and risk-mapping evidence  
**Status:** THREE CANONICAL REFERENCES VERIFIED — TWO ADDITIONAL REFERENCES RECOMMENDED FOR REVIEW — PRODUCTION CONTROLS NOT CERTIFIED  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Canonical branch:** `reos-development`  
**Related blueprint:** `REOS_CONTROL_CENTER/architecture/AI-001_PLATFORM_IMPLEMENTATION_BLUEPRINT.md`  
**Related section:** Section 20 — External Security and Risk References  
**Audit date:** 2026-10-29  
**Audit baseline HEAD:** `3dc9cbdb56c0963b5af3e564151d94a136110a5c`  
**Canonical state blob SHA:** `6242f63371a725ea99447c218bbbeb46a0c5eddd`  
**Blueprint blob SHA:** `a32701e9bbba1377434598ffea8f25d3272d1c97`  
**Section 19 record blob SHA:** `b1e221d9e91166c288bff1f42f4a1e21a059f1f4`

---

## 1. Purpose and authority

This record verifies the external references listed in Section 20 of the AI-001 blueprint and records how they should inform HOMIO / REOS security, risk assessment, observability and agent boundaries.

External references are guidance and threat knowledge. They do not independently establish that HOMIO implements a control, meets a security standard, complies with a law, or is safe to release.

This record:

- Verifies the identified reference sources and their visible version/status information.
- Maps reference topics to existing HOMIO implementation and evidence owners.
- Identifies source-maturity and data-minimization cautions.
- Recommends additional references for future review without silently amending the blueprint.
- Preserves the existing Control Center, domain authorization and CI ownership boundaries.

This is an evidence record, not a new security framework, policy engine, compliance certification or canonical execution plan. It does not change `REOS_CONTROL_CENTER/data/state.json` or authorize a new task transition.

## 2. Canonical baseline and CI evidence

| Item | Verified value |
|---|---|
| Repository HEAD before this record is saved | `3dc9cbdb56c0963b5af3e564151d94a136110a5c` |
| Baseline commit | [Create Section 19 Definition of Done matrix](https://github.com/prajaktaranjane80-sketch/Homio/commit/3dc9cbdb56c0963b5af3e564151d94a136110a5c) |
| Canonical state blob | `6242f63371a725ea99447c218bbbeb46a0c5eddd` |
| Blueprint blob | `a32701e9bbba1377434598ffea8f25d3272d1c97` |
| AI-001 gate status | `APPROVED` |
| AI-001 subtasks | T01–T10 `DONE` |
| Current canonical task | `APP-001-T01` |

The latest relevant backend run at this baseline was:

- **Workflow:** HOMIO Backend and ACRL Runtime CI
- **Run:** #560
- **Run ID:** `40890200649`
- **Tested SHA:** `3dc9cbdb56c0963b5af3e564151d94a136110a5c`
- **Conclusion:** `SUCCESS`
- **URL:** https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/40890200649

The logs reported 266 Python files compiled, 15 entrypoint contract tests passed, 229 AI platform tests passed and 1,444 ACRL tests passed. The Section 14 synthetic evaluation reported 10 passed, 0 failed, 0 blocked, with `release_ready=False`.

The guarded Control Center transition and approval jobs in this run were skipped. The run does not authorize or perform a new canonical transition.

This Actions result is verification evidence for the baseline commit. It is not proof that an external standard has been implemented, that a production deployment uses it, or that security approval has been granted.

---

## 3. Existing Section 20 reference audit

### 3.1 OWASP GenAI Security Project — Top 10 for LLM Applications 2026

**Canonical source:**  
https://github.com/GenAI-Security-Project/GenAI-LLM-Top10

**Official publication:**  
https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/

**Observed edition:** 2026, published August 4, 2026 according to the official project repository.

**Audit result:** SOURCE VERIFIED — USE AS A RISK-COVERAGE REFERENCE, NOT AS A PASS/FAIL CERTIFICATION.

The 2026 list covers ten risk areas:

1. Prompt injection.
2. Sensitive information disclosure.
3. Excessive agency.
4. Supply-chain risk.
5. Data and model poisoning.
6. Unbounded consumption.
7. Misinformation.
8. Hidden-context exposure.
9. Vector and embedding weaknesses.
10. Improper output handling.

#### HOMIO mapping

| Risk area | Existing implementation/evidence owner | Required interpretation |
|---|---|---|
| Prompt injection and hidden context | `ai_platform/prompt_templates.py`, RAG pipeline and AI safety regressions | Retrieved content and user input remain untrusted. Prompt structure is not an authorization boundary. |
| Sensitive-information disclosure | `ai_platform/observability.py`, provider adapters and redaction tests | Keep credentials, raw prompts, private records and sensitive tool output out of ordinary telemetry. |
| Excessive agency | `ai_platform/agent_runtime.py`, `ai_platform/tool_bridge.py`, existing execution ToolGateway | AI proposals do not grant permission. Tool allowlists, trusted server context and authoritative authorization remain mandatory. |
| Supply-chain risk | Existing dependency configuration, GitHub workflows and code review controls | Pin and review dependencies and CI actions using their existing owners. A reference to OWASP does not prove the entire software supply chain is secured. |
| Data/model poisoning | CORE-005 search/index contracts, source/version checks and indexing regressions | Validate source provenance and tenant boundaries; do not assume these checks replace a broader poisoning assessment. |
| Unbounded consumption | `ai_platform/cost_control.py`, gateway bounds and usage-accounting tests | Preserve hard limits and fail-closed budget enforcement. Production quotas, concurrency limits and shared-datastore deployment still need operational evidence. |
| Misinformation | RAG grounding, citation validation and Section 14 synthetic evaluation | Distinguish source-backed facts from model-generated wording. Unsupported legal, financial or property claims must be qualified rather than invented. |
| Vector and embedding weaknesses | Existing CORE-005 retrieval and indexing owners | Retain tenant scoping, version validation, provenance checks and rebuildability. Do not create a parallel index merely to satisfy a reference checklist. |
| Improper output handling | Typed AI contracts, structured output validation and tool bridge | Validate output before use. Model output must never be passed directly into privileged execution without the established policy and validation boundary. |

These mappings identify where existing work should be assessed against the reference. They are not a declaration that every OWASP risk has been fully mitigated or that independent adversarial testing has been completed.

**Maintenance rule:** Review the official current edition and errata before a significant security review. Do not freeze a test suite around an old numbered list when the official reference changes.

### 3.2 NIST AI Risk Management Framework — Generative AI Profile, NIST AI 600-1

**Official publication page:**  
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

**Persistent publication identifier:**  
https://doi.org/10.6028/NIST.AI.600-1

**Observed publication:** July 26, 2024. The NIST publication page indicates an update on April 8, 2026.

**Related NIST AI RMF page:**  
https://www.nist.gov/itl/ai-risk-management-framework

**Audit result:** SOURCE VERIFIED — VOLUNTARY RISK-MANAGEMENT GUIDANCE; NOT A COMPLIANCE CLAIM.

NIST describes AI RMF as voluntary risk-management guidance. Its official AI RMF page also states that AI RMF 1.0 is being revised. The Generative AI Profile remains a useful risk-management reference, but it should not be represented as the final or sole source for all future requirements.

#### HOMIO mapping

Use this profile to structure evidence across the AI lifecycle:

- **Govern:** Maintain explicit ownership, approval boundaries and accountable risk decisions.
- **Map:** Record AI use cases, affected parties, property-data sensitivity, tenant boundaries and the consequences of an incorrect response or action.
- **Measure:** Use the existing AI test/evaluation suite, adversarial regressions, error telemetry and approved quality thresholds.
- **Manage:** Apply risk treatment, incident handling, release controls and documented residual-risk acceptance through existing governance.

The above is a proposed way to organize evidence against the NIST risk-management concepts. It does not claim that HOMIO has completed a NIST assessment or formally adopted the full framework.

Existing evidence owners should remain in place:

- `REOS_CONTROL_CENTER/evidence/AI-001/section-14-operational-readiness.md`
- Section 19 Definition of Done evidence
- AI-001 canonical acceptance records in `data/state.json`
- Existing ACRL authorization, repository coordination and evidence-resolution mechanisms

**Important restriction:** Do not write “NIST compliant,” “NIST certified” or equivalent solely because the profile has been reviewed. Any formal claim requires an explicitly defined scope, applicable criteria, evidence and authorized review.

### 3.3 OpenTelemetry GenAI Semantic Conventions

**Current dedicated repository:**  
https://github.com/open-telemetry/semantic-conventions-genai

**GenAI client inference conventions:**  
https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md

**Historical location / move notice:**  
https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/README.md

**Audit result:** CURRENT REPOSITORY VERIFIED — APPLY WITH DATA-MINIMIZATION AND STABILITY CONTROLS.

The GenAI-specific conventions are maintained in a dedicated repository. The previous location in the core semantic-conventions repository records that the GenAI conventions moved and that the old page is no longer maintained.

The conventions can inform names and meanings for GenAI spans, metrics and events. They do not require HOMIO to adopt a new telemetry backend or replace its existing observability implementation.

The current specification marks message-bearing attributes such as `gen_ai.input.messages` and `gen_ai.output.messages` as **Opt-In**. Similar attributes can contain raw prompts, outputs, user instructions or other sensitive material.

#### HOMIO instrumentation rules

1. Keep content-bearing prompt/message telemetry disabled by default.
2. Prefer allowlisted operational metadata: operation, provider/model identifier where policy permits, duration, token usage where available, bounded error classification and outcome.
3. Do not emit raw property records, contact details, credentials, private user instructions, full retrieved content or arbitrary tool arguments by default.
4. Never use trace attributes as a substitute for authoritative authorization or audit receipts.
5. Follow the existing observability owner, logging destination, access controls, retention and deletion requirements.
6. Review the stability and requirements status of each adopted attribute before pinning it in production.
7. Record the exact convention revision/schema adopted by any future instrumentation change.
8. Verify redaction and data minimization with executable tests before enabling content-bearing attributes.

**Boundary:** The existence of `ai_platform/observability.py` and passing regression tests does not prove that a production OpenTelemetry collector, exporter, destination, retention policy or alerting service has been deployed and approved.

---

## 4. Additional references recommended for future review

The following sources were identified as useful additions because AI-001 includes an agent runtime and guarded tool bridge. They are **recommendations only**; they have not been silently inserted into the canonical blueprint and are not represented as adopted controls.

### 4.1 MITRE ATLAS — Adversarial Threat Landscape for Artificial-Intelligence Systems

**Official source:**  
https://atlas.mitre.org/

**Proposed purpose:** Use its evolving adversary tactics, techniques and case studies to derive concrete threat scenarios for the AI gateway, retrieval pipeline, agent runtime and tool bridge.

Potential scenario categories include prompt/context manipulation, unauthorized capability use, data collection/exfiltration, model access abuse and harmful autonomous behavior.

**Recommended future use:** Map applicable threat scenarios to existing security tests and record which controls and evidence address each scenario. Reuse existing test and evidence ownership. Do not create a second threat database or claim that every ATLAS technique applies to HOMIO.

**Status:** RECOMMENDED FOR REVIEW — NOT AN IMPLEMENTATION OR CERTIFICATION CLAIM.

### 4.2 OWASP Agent Control Standard (ACS)

**Official resource:**  
https://genai.owasp.org/resource/agent-control-standard-acs/

**Observed publication date:** September 1, 2026.

**Proposed purpose:** Evaluate its runtime-control, inspectability, traceability and agent-policy concepts against the existing `agent_runtime.py`, `tool_bridge.py` and governed execution ToolGateway.

**Review questions:**

- Does the existing authorized execution path already provide the required policy hook and decision point?
- Are proposed actions, denials, execution outcomes and receipts separately observable?
- Can a policy be enforced independently of the model's own instructions?
- Would adopting a proposed control duplicate an existing execution, authorization or ACRL owner?
- What additional integration tests and production evidence would be required?

**Status:** RECOMMENDED FOR COMPATIBILITY REVIEW — NOT AN ADOPTED RUNTIME STANDARD.

No ACS integration, middleware layer, policy engine or new agent-control service is authorized by this recommendation alone. Any implementation proposal must first identify the existing owner, contract, gap and tests.

---

## 5. Consolidated external-reference disposition

| Reference | Current audit disposition | What it can contribute | What it does not prove |
|---|---|---|---|
| OWASP GenAI LLM Top 10 2026 | Verified current edition | AI-specific risk coverage and mitigations to evaluate | Complete mitigation, penetration-test success or release approval |
| NIST AI RMF GenAI Profile NIST AI 600-1 | Verified publication; framework status must be monitored | Lifecycle risk-management structure and evidence discipline | Legal compliance, certification or an approved HOMIO risk tolerance |
| OpenTelemetry GenAI Semantic Conventions | Verified dedicated repository; individual attribute maturity must be reviewed | Consistent GenAI telemetry naming and signal semantics | Production deployment, permission to capture content, or safe retention |
| MITRE ATLAS | Recommended future review | Adversarial AI scenarios to inform threat modeling and tests | Proof that the full technique list applies to HOMIO or that all threats are mitigated |
| OWASP Agent Control Standard | Recommended future review | Agent runtime control and traceability concepts | Adoption, compatibility with HOMIO, or authorization to add a new policy system |

---

## 6. Evidence gaps that remain open

This reference audit does not close the production-readiness limitations in the existing Section 14 operational record.

The following remain separate obligations:

- Approved AI quality-release threshold.
- Approved availability SLO and measurement window.
- Verified production provider/model configuration and server-side secret storage/rotation.
- Production tenant budget/quota, concurrency and rate-limit evidence.
- Approved provider data-processing and data-residency policy.
- Production log destination, access control, retention/deletion and alert ownership.
- Operational kill-switch procedure and tested rollback.
- Resolution of the difference between safe free-text handling of unsupported property criteria and the intended structured search behavior.
- Any independent security or adversarial assessment required by the project’s release policy.

An external reference cannot close a gap without a corresponding verified implementation, test, deployment artifact or approved decision.

The current Section 14 release decision remains **NOT READY FOR PRODUCTION ENABLEMENT**. A green CI run or a current reference list is not sufficient grounds to change that decision.

## 7. Reference maintenance protocol

Before each major AI security or release review:

1. Open each canonical reference source and verify its current edition, publication status, errata and repository location.
2. Record the review date and exact source/version when a stable edition or revision is available.
3. Distinguish published standards, evolving specifications, threat knowledge bases and emerging proposals.
4. Map each relevant risk to the existing HOMIO owner, executable test and evidence location.
5. Identify unmitigated or unverified risks explicitly rather than treating a reference as a completed control.
6. Do not duplicate the existing security, observability, retrieval, authorization or evidence systems.
7. Recheck prompt/message telemetry policy before enabling any content-bearing attribute.
8. Preserve existing approvals and use the Control Center for all formal task transitions.

For references whose latest version changes frequently, record the exact revision actually reviewed rather than writing “latest” without a revision or date.

## 8. Final determination

**SECTION 20 DISPOSITION: THREE CANONICAL REFERENCES VERIFIED; TWO ADDITIONAL REFERENCES RECOMMENDED FOR REVIEW; PRODUCTION SECURITY AND RELEASE STATUS UNCHANGED.**

The three references already listed in the AI-001 blueprint are suitable inputs to the security and risk review, with explicit qualifications:

- The OWASP LLM Top 10 is a risk-coverage reference.
- NIST AI RMF is voluntary risk-management guidance, and its framework status must be monitored.
- OpenTelemetry GenAI conventions inform instrumentation but do not override HOMIO data-minimization, authorization, retention or redaction requirements.

MITRE ATLAS and OWASP ACS are recommended candidates for a future authorized review of adversarial and agent-runtime coverage. They do not create a new task or new ownership boundary.

This record does not edit the AI-001 blueprint, change canonical state, enable customer-facing AI, certify compliance or authorize production rollout. The current canonical execution task remains `APP-001-T01` unless the existing Control Center records an authorized transition.

---

**Document end — external-reference audit evidence only; no canonical state transition performed.**
