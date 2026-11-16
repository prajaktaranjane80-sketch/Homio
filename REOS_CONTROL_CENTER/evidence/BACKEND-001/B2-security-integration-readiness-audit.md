
# BACKEND-001-B2 — Production Security Dependency Correction

**Status:** `OWNER_APPROVAL_RECEIVED — GUARDED_TRANSITION_PENDING`

**Audit date:** 2026-11-16  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Live audited HEAD:** `b347008848c1d64bcfefdd20568fcbb28c9f64f0`  
**Canonical state blob:** `dd9c4684698270adf19a9380256c94396608a27a`  
**Backend master blob:** `27b43931d1b6db48065ec41fd3574bd2dbc5ae3c`

## 1. Canonical execution status

The live canonical state confirms:

| Subtask | Status |
|---|---|
| BACKEND-001-B0 | DONE |
| BACKEND-001-B1 | DONE |
| BACKEND-001-B2 | CURRENT |
| BACKEND-001-B3 through B10 | PENDING |

The authoritative task remains:

`BACKEND-001-B2 — API security and trusted context`

No task status, gate status, canonical state or stage sequence has been changed by this audit.

## 2. Exact live source baseline

The following existing files were inspected at the live branch HEAD.

| Existing source | Blob SHA | Decision |
|---|---|---|
| `backend/src/security/api-security.ts` | `90772f934cab2c200a25808a87fd6a10b6605c13` | REUSE |
| `backend/src/security/contracts.ts` | `d03d183b61d69d2a590a88fa62f259f396eec83f` | REUSE |
| `backend/src/security/README.md` | `fa273976139316d424cc5c18c96cadf45a614540` | REUSE |
| `backend/src/app.ts` | `31b36c2bbb0ab34f47beae492c244c5309e39a9e` | REUSE |
| `backend/src/main.ts` | `ed1328d85bf8d49940a56ec38af0084807aa8aed` | REUSE |
| `backend/tests/unit/api-security.test.ts` | `b1698d8359b19f6ebfe34e83d38482186aa1855f` | REUSE |
| `backend/tests/unit/security-adapter-boundary.test.ts` | `b5f72cfe0fb56476ddfb6d675f77fc8534aa1c7b` | REUSE |
| `backend/tests/helpers/security-runtime.ts` | `dfd0d4c4566c3bd7def5e90fdd3b14569404e24c` | TEST ONLY |

The existing Fastify security guard remains the single public API ingress boundary.

It already enforces bearer authentication, trusted-context resolution, session validation, resource/action authorization, rate limiting, audit hooks, mutation reauthorization and fail-closed behavior.

It also refuses to mount protected API plugins without the complete security runtime.

No replacement of `api-security.ts` or `api-security.test.ts` is justified merely to address missing production adapters.

## 3. Latest exact-SHA CI evidence

Latest inspected backend workflow run:

- Run number: `792`
- Run ID: `42981481909`
- Tested commit: `b347008848c1d64bcfefdd20568fcbb28c9f64f0`
- Conclusion: `SUCCESS`

Source: https://github.com/prajaktaranjane80-sketch/Homio/actions/runs/42981481909

Verified results:

| Verification | Result |
|---|---:|
| Backend TypeScript test files | 7 passed |
| Backend TypeScript tests | 44 passed |
| API security tests | 21 passed |
| Security adapter boundary tests | 3 passed |
| Complete ACRL regression suite | 1,456 passed |
| TypeScript verification | PASS |
| ESLint | PASS |
| Production build | PASS |
| Reproducible dependency/build verification | PASS |

These results prove the existing fail-closed boundary and regression tests.

They do not prove production identity, session, authorization, rate-limit or audit adapters are connected.

A successful backend verification run is not a B2 completion transition.

## 4. Confirmed production dependency gaps

### 4.1 Canonical OIDC owner

Existing verifier:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/security/authentication/oidc_verifier.py`

Blob SHA:

`b78f7b9011427e74900b0a1b64978f6f27a2a37c`

The backend must reuse the existing approved OIDC access-token verifier through the authenticated private runtime boundary.

A second TypeScript or Python identity verifier must not be introduced without an approved ownership decision.

Frontend encrypted cookies are not backend authentication credentials.

### 4.2 CORE-001 identity and membership owner

Existing files:

- `AUTONOMY_ENGINE/core/identity_tenant/identity.py`
- `AUTONOMY_ENGINE/core/identity_tenant/membership.py`
- `AUTONOMY_ENGINE/core/identity_tenant/identity_contract.json`
- `AUTONOMY_ENGINE/core/identity_tenant/membership_contract.json`
- `AUTONOMY_ENGINE/core/identity_tenant/tenant_contract.json`

Existing owner source remains canonical.

The membership contract explicitly distinguishes permission grants/prerequisites from authorization decisions.

The current CORE-001 T03 contract is not itself a general resource/action authorization decision engine.

A second identity registry, tenant registry or competing authorization engine is prohibited.

The approved correction is to formalize resource/action authorization decision ownership inside the existing CORE-001 identity/membership owner, using its current contracts and tests.

### 4.3 Authenticated Python runtime bridge

The current backend source tree does not contain a verified authenticated TypeScript-to-Python domain-runtime bridge.

B3 is the canonical stage responsible for the private, versioned runtime boundary.

B2 must not bypass B3 by:

- copying Python business logic into TypeScript;
- invoking an unauthenticated internal HTTP endpoint;
- treating the ACRL controller bridge as a business API;
- accepting caller-supplied actor or tenant identity;
- introducing a second public Python API.

The B2 trusted-context contract already provides the required boundary for the bridge to preserve.

### 4.4 Durable session and revocation persistence

`REOS_CONTROL_CENTER/modules/session_engine.py` currently contains only a comment.

It is not an implemented customer-authentication session service.

It must not be repurposed as an ACRL or Control Center session module for customer login state.

Production session/revocation persistence must be implemented through the approved backend persistence boundary, with canonical account authentication-epoch/revocation ownership preserved.

### 4.5 Shared rate limiting and security audit

The current test helper is deliberately synthetic:

- Session validation returns a fixed active result.
- Authorization returns `ALLOWED`.
- Rate limiting always allows.
- Audit persistence is a no-op.
- Context resolution uses a fixed test principal/context.

These implementations are test fixtures only.

Production requires shared/distributed rate-limit enforcement and durable, minimized security audit persistence before protected handlers execute.

No in-process-only rate limiter or no-op production audit adapter is acceptable.

### 4.6 Production composition is not present

`backend/src/main.ts` currently starts without customer route plugins or a production security runtime.

`backend/src/app.ts` correctly rejects protected API plugins without all required security adapters.

A health-only backend must not be represented as a ready customer API.

This fail-closed behavior must remain intact.

## 5. Approved B2 dependency correction

The current B2 requirements need two dependencies that the original stage order places later:

1. B3 provides the authenticated private runtime boundary for the existing Python-owned OIDC and CORE-001 owners.
2. B4 provides the durable persistence foundation required for production session/revocation, shared rate limiting and security audit.

Completing B2 before these dependencies would force one of the following unsafe outcomes:

- production mocks;
- non-durable session state;
- in-process-only rate limiting;
- no-op audit persistence;
- duplicated identity or authorization logic;
- direct Python invocation outside the approved private bridge.

Those outcomes are rejected.

The owner-approved dependency correction is:

`B0 → B1 → B2-FOUNDATION → B3 → B4 → B2-PRODUCTION-BINDING → B5 → B6 → B7 → B8 → B9 → B10`

### B2-FOUNDATION

Reuse the existing B2 implementation for:

- the single Fastify `/api/v1` ingress guard;
- strict bearer-token boundary;
- minimal trusted principal/context projections;
- route security metadata and schema validation;
- fail-closed adapter contracts;
- mutation reauthorization;
- isolated security-boundary tests.

This phase does not enable customer-facing protected routes.

### B3 — Private Python runtime bridge

Reuse the existing Python OIDC and CORE-001 owners.

The bridge must provide:

- authenticated service-to-service identity;
- versioned private request/response contracts;
- trusted actor and tenant context propagation;
- correlation identity;
- strict serialization and validation;
- timeout, cancellation and failure classification;
- integration and authorization-context tests.

It must not expose a second public Python API or duplicate CORE business logic.

### B4 — PostgreSQL and durable security persistence

Reuse the approved ARCH-037 schema and the canonical backend persistence boundary.

Before migrations, verify the exact approved schema and existing migration inventory.

Required security persistence capabilities:

- durable session/revocation status;
- canonical account authentication-epoch checks;
- shared rate-limit state;
- minimized security audit events;
- tenant-safe access and transaction boundaries;
- integrity, uniqueness, migration and recovery tests.

If an entity is absent from ARCH-037, it must not be silently introduced. The required schema decision must be explicitly reconciled before implementation.

No second persistence authority or duplicate audit engine is permitted.

### B2-PRODUCTION-BINDING

After B3 and B4, complete the original B2 production security objective by wiring the six real adapters:

1. approved OIDC access-token verification;
2. durable session and revocation validation;
3. CORE-001 identity, tenant and active membership resolution;
4. CORE-001 resource/action authorization decisions;
5. shared/distributed rate limiting;
6. durable security audit persistence.

The final B2 stage must verify:

- buyer, broker, builder and privileged-role isolation;
- cross-tenant denial;
- revoked-session denial;
- unauthorized resource/action denial;
- authorization revalidation before mutations;
- audit persistence before protected handlers;
- rate-limit enforcement across instances;
- invalid-token and dependency-outage fail-closed behavior;
- no sensitive credentials or PII in logs/audit;
- no frontend cookie accepted as an API identity credential.

No customer-facing protected API route may be enabled until this final B2 stage is verified.

## 6. Canonical ownership map

| Responsibility | Canonical owner |
|---|---|
| Public API ingress and security guard | Existing Fastify B2 boundary |
| OIDC access-token verification | Existing AUTONOMY_ENGINE security/authentication owner |
| Identity and tenant membership | Existing CORE-001 owner |
| Resource/action authorization decisions | Existing CORE-001 membership owner, subject to approved contract implementation |
| Private TypeScript/Python transport | B3 backend runtime bridge |
| Durable persistence and security stores | B4 backend persistence boundary |
| Security audit persistence adapter | B4 persistence boundary |
| Developer change-impact analysis | ACRL T17 |
| Developer execution authorization | ACRL T18 |

ACRL is not a production customer authentication, authorization, session or audit runtime.

## 7. Guarded governance requirement

The repository owner has explicitly approved proceeding with the B2 dependency correction in this conversation:

`APPROVE B2 DEPENDENCY CORRECTION`

This approval authorizes preparation of the bounded correction described in this document.

It does not replace the repository's T15/T17/T18 authorization requirements.

Before changing the authoritative task sequence or state:

- T15 must produce a bounded proposal.
- T17 must analyze the actual changed repository paths and dependency impacts.
- T18 must authorize the exact scope using OIDC-verified repository-owner identity bound to the approval evidence.
- The existing Control Center must perform any canonical state transition.
- Exact-SHA Actions and post-transition readback must pass.

The existing `backend-ci.yml` currently has no B2 dependency-correction or B2 production-completion transition.

The correction must extend the existing backend CI and guarded-transition ownership. It must not create a parallel backend CI system, a second Control Center, or a generic duplicate orchestration engine.

Manual `state.json` editing is prohibited.

## 8. Required final evidence

B2 must not be marked complete until evidence identifies:

- exact source commit SHA;
- exact T15 request fingerprint;
- exact T17 impact fingerprint and changed paths;
- exact T18 authorization fingerprint;
- verified OIDC issuer and subject, without storing the bearer token;
- B3 private bridge integration results;
- B4 persistence and recovery results;
- real production-adapter integration results;
- cross-tenant and adversarial security test results;
- backend verification run ID and attempt;
- canonical Control Center transition result;
- exact post-transition state blob SHA.

A green unit-test suite by itself is insufficient.

## 9. Explicit non-goals

This correction does not authorize:

- frontend UI changes;
- a parallel backend or API application;
- a new identity or tenant registry;
- a second general authorization engine;
- a duplicate session engine;
- a duplicate audit engine;
- an ACRL production runtime dependency;
- customer route exposure before final B2 verification;
- manual state mutation;
- premature B2 or backend-gate completion.

## 10. Current truthful status

- Existing B2 security boundary: implemented.
- Existing isolated B2 tests: passing in run #792.
- Production B2 adapters: incomplete.
- B3 private runtime bridge: pending.
- B4 durable persistence: pending.
- B2 production binding: pending.
- Owner approval for dependency correction: received in this conversation.
- T15/T17/T18 guarded transition: pending.
- Canonical state: unchanged.
- B2: remains CURRENT.
- Production readiness: not established.

**This document records the approved correction direction and current evidence. It does not itself complete B2, change the canonical task sequence, authorize a production release or mutate `state.json`.**
