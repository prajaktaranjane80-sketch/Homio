# B2 — CORE-001 Identity Context and Resource/Action Authorization Change Request

**Request ID:** B2-CORE001-AUTHZ-001  
**Project:** HOMIO / REOS  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Status:** PROPOSED — NOT APPROVED  
**Execution task:** `BACKEND-001-B2-PRODUCTION-BINDING`  
**Scope:** Bounded extensions to existing CORE-001 owners and the authenticated B3 contract  
**Production authorization:** NOT AUTHORIZED BY THIS DOCUMENT

---

## 1. Purpose

B2 Production Binding requires one canonical resource/action authorization decision owner using existing HOMIO identity, tenant and membership authorities.

The current implementation has the correct ownership separation, but its contracts do not yet carry all information needed to make and verify a production authorization decision.

This request formalizes the required extensions before implementation. It does not authorize production activation, protected customer routes or completion of B2.

The change must extend existing owners. It must not introduce another identity registry, membership directory, persistence owner, public API, generic policy engine or parallel backend.

## 2. Verified current source baseline

The following live repository sources were inspected for this request.

| Existing authority | Source path | Verified blob SHA |
|---|---|---|
| Execution state | `REOS_CONTROL_CENTER/data/state.json` | `3482877a8e321f9d81782270bb44cfaeec297496` |
| Backend technical master | `REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure` | `f8d9cd456568cc6c8eaae0caf764123a7e859ba6` |
| T01 identity owner | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/identity.py` | `49564ab0e7b3f19d192c343bd444ba3b45ced192` |
| T03 membership owner | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership.py` | `919868a77bf589795c383a1fbb974fc69dede6ec` |
| T03 membership contract | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership_contract.json` | `9304de1df604c1937d22cd682cfb88cc686b2fe5` |
| T03 contract regression test | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_t03_d_contract.py` | `16721b8308d098d639e3bceea7e0f7b94607d525` |
| T04 tenant isolation owner | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/tenant_isolation.py` | `d96a41cd85b61b67d1a3c789750d441d71078a5b` |
| Fastify security contracts | `REOS_CONTROL_CENTER/backend/src/security/contracts.ts` | `97aad9487b841c364b1a64581416eeded37560bd` |
| B3 runtime contracts | `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/contracts.ts` | `1bb86d28790f3a606f242603e2c06ad8ac0b6e79` |
| B3 TypeScript client | `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/client.ts` | `f7791f5c330c0237cec4c710d1f41c6dcc0d0ef8` |
| B3 Python protocol | `REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/protocol.py` | `20ba424574b08452abd25d2923e719e88408b0d8` |
| Existing Fastify security boundary | `REOS_CONTROL_CENTER/backend/src/security/api-security.ts` | `1bf49feca47a16d1180b737d4a53d6ad216c3f8c` |
| Current backend CI workflow | `.github/workflows/backend-ci.yml` | `42a7b08b9272e2663028b332e1708a8c8f77fa22` |

These hashes are a verified source baseline, not permanent pins. The guarded implementation must revalidate live hashes before authorizing a transition.

## 3. Existing owner boundaries — must remain intact

### T01 — Identity

Canonical identity, external identity references, account association, account status and authentication epoch remain owned by the existing T01 identity owner.

The current `IdentityRegistry.resolve_external()` resolves an external identity to an `identityId`. The current registry provides `get_account(account_id)`, but does not expose a canonical account lookup by `identityId`.

The B3 `core001.identity.resolve` response currently contains `identityId` and `referenceId`; it does not return the canonical account ID or authentication epoch required by the Fastify trusted context.

**Required extension:** Extend the existing T01 owner so a verified external identity can be associated with its canonical account and current authentication epoch without trusting a client-supplied account ID.

Account cardinality must be explicit. If an identity has no unambiguous eligible account, resolution must fail closed. The implementation must not silently select an account or create a second account registry.

### T02 — Tenant

The existing T02 tenant authority remains responsible for canonical tenant identity, lifecycle, revision and tenant context.

No new tenant registry or tenant source of truth is permitted.

### T03 — Membership, roles, permissions and prerequisites

T03 remains the canonical data owner for:

- Membership and membership revision.
- Roles and their permission and entitlement references.
- Permission resource/action definitions.
- Entitlements and their prerequisites.
- Tenant-bound scopes.
- Relationship references and requirements.
- Attribute constraints.
- Required assurance declarations.

`MembershipDirectory` remains a structural data owner. It must not become an authorization decision engine.

### T04 — Tenant isolation

T04 remains the tenant-boundary verification owner.

A T04 `ALLOW` result proves only that the tenant boundary is consistent. It does not grant a resource/action permission.

### B3 — Authenticated private runtime bridge

B3 remains the single private TypeScript-to-Python runtime boundary.

The resource/action decision must be invoked through this existing authenticated protocol. No second public Python API or separate authorization service is permitted.

### B4 — Persistence

B4 remains the only owner for durable sessions, revocation, shared rate limits and PII-minimized security audit persistence.

The new CORE-001 decision owner must not create replacement stores.

## 4. Verified contract gaps that must be resolved

### 4.1 Account identity and authentication epoch

The Fastify `TrustedRequestContext` requires:

- `identityId`
- `accountId`
- `authenticationEpoch`
- `tenantId` and `tenantRevision`
- `organizationId`
- `membershipId` and `membershipRevision`

The current B3 runtime context contains identity and account IDs, but does not carry `authenticationEpoch`. The current identity resolution response does not provide the canonical account ID or epoch.

**Required result:** The existing T01 resolver must return the canonical identity/account association and authentication epoch. B3 must validate and propagate those values as server-derived context. Client input must never establish or override them.

### 4.2 Resource/action decision operation

The current B3 allowlist contains:

- `oidc.verify_access_token`
- `core001.identity.resolve`
- `core001.tenant.resolve_context`
- `core001.membership.resolve`

It has no resource/action decision operation.

**Required extension:** Add one versioned private operation, `core001.authorization.authorize`, to the existing B3 protocol. It must call the new CORE-001 decision owner using the injected canonical T01–T04 owners. It must not copy their business logic into TypeScript or create another domain owner.

The request must use the authenticated trusted runtime context and the protected route's declared operation/resource. It must reject caller-supplied identity, account, tenant, organization or membership overrides.

### 4.3 Assurance and attribute context

T03 contains `required_assurance` and attribute constraints. The current B3 trusted runtime context and verified principal response do not expose a verified assurance level or a canonical set of subject attributes for evaluating those constraints.

**Required rule:**

- Assurance must come from a verified, approved authentication source and be mapped explicitly to the CORE-001 assurance contract.
- Attributes must come from an existing trusted CORE-001 source.
- Neither may be accepted from frontend input or unverified token claims.
- An unresolved assurance or attribute prerequisite must result in DENY.
- The authorization implementation must never ignore an applicable prerequisite merely because the current transport does not provide its value.

The exact trusted assurance and attribute mappings must be reviewed and approved before the decision owner is implemented.

### 4.4 Explicit deny representation

The current T03 contract defines positive permission grants and declarative prerequisites. It does not define an explicit `DENY` permission/effect field or a canonical deny-rule entity.

Therefore this change must **not invent an explicit-deny model inside T03**.

For this approved scope, default-deny means:

- ALLOW is possible only when a complete, active, exact resource/action grant path is proven.
- Missing, unknown, inactive, expired, revoked, stale or mismatched prerequisites produce DENY.
- No complete matching grant produces DENY.
- A role name or membership fact alone never produces ALLOW.

An explicit deny-override feature is outside this request. It would require a separate approved CORE-001 contract change and must not be simulated by undocumented rules.

## 5. Proposed canonical decision owner

Create one bounded decision capability inside the existing CORE-001 identity/tenant ownership boundary.

Proposed files:

1. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/resource_action_authorization.py`
2. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/resource_action_authorization_contract.json`
3. `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_resource_action_authorization.py`

The owner must consume the existing T01, T02, T03 and T04 authorities through injected owner references. It must not maintain shadow copies or parallel registries.

Its only responsibility is to return a deterministic resource/action decision from current trusted context and canonical owner facts.

## 6. Required decision contract

### 6.1 Trusted input

The decision request must contain:

- Canonical identity ID.
- Canonical account ID.
- Current authentication epoch.
- Canonical tenant ID and revision.
- Organization ID.
- Membership ID and revision.
- Protected operation/action.
- Resource type and optional resource ID.
- Correlation identity.
- Verified assurance and trusted attributes only when their canonical source has been approved and resolved.

Identity, account, tenant, organization and membership data must be derived from the authenticated server context and revalidated against the existing owners.

### 6.2 Required decision evaluation

The CORE-001 decision owner must evaluate the following in a deterministic, fail-closed order:

1. Resolve the canonical identity and account association through T01.
2. Confirm account status and authentication epoch are current.
3. Resolve the tenant and current tenant revision through T02.
4. Verify tenant/resource/membership boundary consistency through T04.
5. Resolve the active membership through T03 and match identity, tenant, organization, membership ID and revision.
6. Resolve the role and entitlement grant references from the exact membership.
7. Match the requested resource/action against canonical T03 permission definitions. Do not infer access from a role label.
8. Verify role and entitlement status, validity and required permission references.
9. Verify tenant, organization and resource scopes against the requested resource.
10. Verify relationship requirements against current, active, tenant-bound relationship facts.
11. Evaluate all applicable attribute constraints using only approved trusted attribute sources.
12. Evaluate required assurance using only the approved verified assurance mapping.
13. Return DENY when any required owner, context value, prerequisite or policy fact is absent, stale, ambiguous or unavailable.

The evaluation must be read-only. It must not mutate T01–T04 records or own session, audit, persistence or event responsibilities.

### 6.3 Output

The decision response must contain:

- `allowed`: explicit boolean.
- `reasonCode`: stable, non-sensitive reason code.
- Contract/policy revision.
- Relevant owner revisions needed for deterministic verification and audit correlation.

It must not expose bearer tokens, credentials, private policy internals or unnecessary personal information.

### 6.4 Denial behavior

The following conditions must never return ALLOW:

- Unknown operation or resource.
- Missing or ambiguous identity/account association.
- Inactive account or stale authentication epoch.
- Missing, inactive, revoked, expired or stale membership.
- Tenant, organization, membership or resource scope mismatch.
- Missing permission grant.
- Inactive role or entitlement.
- Invalid relationship or unsatisfied relationship requirement.
- Unresolved required assurance or attribute constraint.
- Missing or unavailable required owner dependency.
- Invalid or unavailable policy contract.

## 7. Role isolation policy

B2 requires buyer, broker, builder and privileged-role isolation tests.

The decision owner must evaluate the canonical T03 role, permission, entitlement and scope records. It must not hardcode an invented role/action matrix based only on labels.

The CORE-001 owner must approve the canonical role fixtures and resource/action expectations used by the tests. The same decision evaluator must be used for all role categories.

A role label by itself is never authorization.

## 8. B3 integration requirements

The existing B3 protocol must be extended without creating another bridge.

Required affected source owners:

- `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/contracts.ts`
- `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/client.ts`
- `REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/protocol.py`
- The existing TypeScript and Python B3 protocol regression tests.
- `REOS_CONTROL_CENTER/backend/src/security/contracts.ts` for any approved trusted-context contract extension.

Required changes:

1. Propagate the T01-derived account ID and authentication epoch in trusted runtime context.
2. Add the versioned `core001.authorization.authorize` operation to the existing operation allowlist.
3. Validate exact request and response schemas.
4. Bind the authorization request to the existing trusted actor and tenant context.
5. Invoke the existing CORE-001 decision owner.
6. Preserve correlation identity, timeout, cancellation and dependency-failure behavior.
7. Reject missing, stale, mismatched and malformed trusted context.
8. Keep the bridge private and service-to-service authenticated.
9. Do not add an alternate public authorization API.
10. Do not use ACRL as a customer security runtime.

The approved contract must be covered by cross-language TypeScript/Python tests.

## 9. Required regression and adversarial tests

The CORE-001 owner tests must cover:

- Exact permission/resource/action match.
- Missing permission default-deny.
- Buyer, broker, builder and privileged-role isolation using approved canonical fixtures.
- Inactive account and stale authentication epoch.
- Missing and ambiguous account association.
- Missing, inactive, revoked, expired and stale membership.
- Cross-tenant and cross-organization denial.
- Tenant, organization and resource scope mismatch.
- Inactive role and entitlement.
- Missing or invalid permission references.
- Relationship mismatch, revocation and validity-window failure.
- Attribute constraint mismatch.
- Required assurance unavailable or insufficient.
- Unknown operation and unknown resource denial.
- Missing owner dependency and dependency outage.
- Malformed decision input and output.
- No authorization mutation inside T03.
- No change to T04 tenant-isolation ownership.
- No duplicate identity, account, tenant or membership registry.

B3 integration tests must additionally prove:

- Caller-supplied trusted identity/account/tenant fields cannot override server-derived context.
- Account ID and authentication epoch are validated through T01.
- The operation is available only through the authenticated private runtime.
- Invalid and unavailable dependencies fail closed.
- TypeScript and Python request/response contracts remain compatible.

B2 integration tests must prove that the existing Fastify `AuthorizationPolicyPort` consumes this decision owner and that protected mutations are reauthorized immediately before handlers.

No mock authorization decision may be treated as production evidence.

## 10. Guarded change-control requirements

The existing T15, T17 and T18 components must be reused.

The live backend workflow currently has no dedicated CORE-001 resource/action change-approval transition. The existing B2 dependency-correction transition is narrowly scoped to its previous approved change and must not be reused.

A separate, bounded CORE-001 approval transition must therefore be added using the existing guard components:

1. T15 produces a bounded proposal for this exact request.
2. T17 performs dependency and impact analysis on the exact changed paths.
3. T18 validates explicit owner approval against the exact proposal, impact and approval-scope fingerprints using the existing GitHub OIDC identity verifier.
4. A separate external executor verifies exact source SHA, canonical state, master reference, CORE-001 source hashes and this request's current content.
5. The existing Control Center remains the only state writer.
6. The executor records the approved change request in the root `change_requests` collection and emits the corresponding Control Center event.
7. The transition must preserve `CORE-001-T10` as DONE and must not reopen, rewrite or complete CORE-001 subtasks.
8. `BACKEND-001-B2-PRODUCTION-BINDING` must remain CURRENT.
9. No B2 acceptance criterion may be marked complete by this approval.
10. Exact-SHA CI, post-transition integrity verification and remote readback are mandatory.

The transition may record only the approved owner-extension scope. It does not authorize production customer routes or claim B2 completion.

## 11. Explicit non-goals

This request does not:

- Convert T03 into an authorization engine.
- Change T03 into a session, authentication, audit or persistence owner.
- Replace T04 tenant isolation.
- Create another identity, account, tenant or membership registry.
- Create a parallel authorization service or generic policy platform.
- Introduce explicit-deny records into T03.
- Invent buyer/broker/builder/privileged permission mappings.
- Trust frontend cookies or caller-provided identity context.
- Create another B3 bridge or public Python API.
- Create another B4 session, rate-limit or audit store.
- Use ACRL for customer authentication or authorization.
- Modify frontend UI.
- Complete B2 Production Binding.
- Declare the backend or production release ready.

## 12. Approval decision requested

The CORE-001 owner must review and approve:

1. The T01 account-resolution extension and account-cardinality behavior.
2. The B3 trusted-context and private authorization-operation extension.
3. The resource/action decision owner within existing CORE-001.
4. Default-deny semantics based on complete canonical grants and prerequisites.
5. The absence of an explicit-deny model in this scope.
6. The trusted assurance and attribute source requirements.
7. The role-isolation fixtures and expected resource/action decisions.
8. The exact proposed source paths and regression coverage.
9. The dedicated T15/T17/T18 guarded approval transition.

**Until the existing guarded change-control process records this approval, these proposed extensions remain unapproved and B2 production binding must remain fail-closed.**

---

**Document classification:** Revised change request — not implementation evidence.  
**Approval status:** NOT APPROVED.  
**Production binding status:** BLOCKED ON GUARDED CORE-001 OWNER APPROVAL.  
**Existing CORE-001 T10 foundation:** Preserved and frozen.  
**Current execution task:** `BACKEND-001-B2-PRODUCTION-BINDING` — remains CURRENT.
