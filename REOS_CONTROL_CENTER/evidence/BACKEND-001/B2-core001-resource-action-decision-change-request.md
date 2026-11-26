# B2 — CORE-001 Resource/Action Decision Contract Change Request

**Request ID:** B2-CORE001-AUTHZ-001  
**Project:** HOMIO / REOS  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Status:** PROPOSED — NOT APPROVED  
**Execution task:** `BACKEND-001-B2-PRODUCTION-BINDING`  
**Scope:** Existing CORE-001 owner extension only  
**Production authorization:** NOT AUTHORIZED BY THIS DOCUMENT

---

## 1. Purpose

Formalize one canonical, contract-governed CORE-001 resource/action authorization decision owner.

The B2 production-binding task requires resource/action decisions. The existing T03 membership contract deliberately stores grants and prerequisites without making authorization decisions.

The missing decision boundary must therefore be formalized through the existing CORE-001 owner and its guarded change-control process before the public backend binds it.

This request does not approve implementation or production activation by itself.

## 2. Authoritative references

| Reference | Current source |
|---|---|
| Backend architecture | `REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure` |
| Current task state | `REOS_CONTROL_CENTER/data/state.json` |
| B4 persistence and continuity | `REOS_CONTROL_CENTER/B4 ka work plan` |
| Saved research continuity | `REOS_CONTROL_CENTER/evidence/BACKEND-001/B4-search-reference-register.md` |
| CORE-001 T03 membership owner | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership.py` |
| T03 membership contract | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership_contract.json` |
| CORE-001 T04 tenant isolation owner | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/tenant_isolation.py` |
| Backend security contract | `REOS_CONTROL_CENTER/backend/src/security/contracts.ts` |
| Existing B3 Python runtime protocol | `REOS_CONTROL_CENTER/backend/python_runtime/homio_python_runtime/protocol.py` |

## 3. Verified ownership boundary

The current CORE-001 owners have distinct responsibilities:

- **T01 Identity:** canonical identity and account facts.
- **T02 Tenant:** canonical tenant and context facts.
- **T03 Membership:** organization, role, permission, entitlement, scope, relationship and membership facts.
- **T04 Tenant isolation:** tenant, organization and membership scope consistency.

T03 explicitly excludes `authorization_decision_engine` and `policy_evaluator`.

T04 explicitly states that a valid tenant-isolation result does not grant resource/action authorization.

These boundaries must remain intact.

## 4. Proposed canonical owner

Introduce one resource/action decision capability within the existing CORE-001 identity/tenant ownership boundary.

Proposed source location:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/resource_action_authorization.py`

Proposed contract location:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/resource_action_authorization_contract.json`

Proposed regression tests:

`REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_resource_action_authorization.py`

These paths are proposals only. They must be accepted by the existing CORE-001 guarded change-control process before implementation.

This must be one bounded CORE-001 owner—not a second identity registry, membership directory, generic authorization platform, independent policy service or duplicate engine.

## 5. Required decision contract

### 5.1 Input

The decision request must be derived from the server-trusted context and the protected route's declared operation.

Required context:

- Canonical identity ID.
- Canonical account ID.
- Current authentication epoch.
- Canonical tenant ID and revision.
- Organization ID.
- Membership ID and revision.
- Declared operation/action.
- Optional protected resource ID.
- Request correlation identity.

The caller must not be permitted to supply or override trusted identity, account, tenant, organization or membership facts.

### 5.2 Output

The decision response must expose:

- `allowed`: explicit boolean decision.
- `reasonCode`: stable, non-sensitive decision reason.
- Contract/policy revision sufficient for deterministic verification and audit correlation.

The response must not expose credentials, raw tokens, secret policy data or unnecessary personal information.

### 5.3 Mandatory decision behavior

1. Default to DENY.
2. A missing or unresolved identity/account context must never produce ALLOW.
3. Missing, inactive, expired, revoked or stale membership must never produce ALLOW.
4. Tenant, organization, membership or resource scope mismatch must produce DENY.
5. Unknown resource/action operations must produce DENY.
6. A membership fact or role name alone must never be treated as authorization.
7. Permission, role, entitlement, scope and relationship facts must be interpreted only through the approved CORE-001 decision contract.
8. Missing policy information or unavailable required owner dependencies must fail closed.
9. A tenant-isolation ALLOW result must not be converted into a resource/action ALLOW result.
10. Protected mutations must be re-evaluated immediately before their handlers.
11. A decision must not mutate T03 records or take ownership of session, audit, persistence or event responsibilities.

## 6. Role and resource/action policy approval

The B2 acceptance criteria require isolation tests for:

- Buyer.
- Broker.
- Builder.
- Privileged roles.

The exact permitted and denied resource/action combinations must come from the approved CORE-001 business contract.

This request deliberately does not invent a role/action matrix.

Before implementation is authorized, the CORE-001 owner must identify the canonical policy semantics and the expected decisions for the required role-isolation cases.

A role name, frontend route or user-supplied claim cannot independently grant access.

## 7. B3 and B2 integration boundary

After the CORE-001 change is approved:

- The existing authenticated B3 private runtime bridge may expose the approved decision operation.
- Request and response fields must be versioned, validated and scope-bound.
- The existing Fastify `AuthorizationPolicyPort` will consume the canonical CORE-001 decision.
- The existing B2 mutation reauthorization hook must use the same decision owner.
- B4 PostgreSQL session/revocation, Redis rate-limit and security-audit stores remain the only corresponding persistence owners.
- ACRL must not be used for customer authorization.

No second public API or Python business API may be created.

## 8. Required tests before B2 production binding

The owner change must include tests for:

- Buyer, broker, builder and privileged-role isolation.
- Cross-tenant resource denial.
- Cross-organization denial.
- Missing membership denial.
- Revoked and expired membership denial.
- Stale membership revision denial.
- Unknown action/resource denial.
- Missing permission or prerequisite denial.
- Relationship and scope mismatch denial.
- Explicit deny precedence.
- Dependency failure and unavailable policy behavior.
- Mutation reauthorization using current context.
- No T03 schema or contract ownership leakage.

Tests must verify the actual CORE-001 decision owner. Mock authorization decisions are not production evidence.

## 9. Explicit non-goals

This change does not:

- Modify T03 into an authorization engine.
- Change T03 membership entities or lifecycle semantics.
- Replace T04 tenant isolation.
- Create another identity, account, tenant or membership registry.
- Create a generic policy engine outside CORE-001.
- Add a second session, rate-limit or audit store.
- Use ACRL as production authorization.
- Modify frontend behavior or UI.
- Declare B2 production binding complete.
- Declare overall backend or production readiness.

## 10. Guarded approval requirements

This request must pass through the existing CORE-001 guarded change-control boundary.

Required before source implementation:

1. CORE-001 owner review of the proposed responsibility and contract.
2. Dependency and impact analysis against T01–T04 and B2/B3.
3. Explicit approval of the resource/action decision semantics.
4. Authorization through the existing guarded control process.
5. Exact approval evidence and approved contract fingerprint.
6. Verification that T03 remains data-only.

No manual `state.json` edit or direct status transition is authorized by this request.

The existing B2 dependency-correction approval must not be reused as approval for this new CORE-001 owner change.

## 11. Decision requested

Approve or reject the proposed CORE-001 resource/action decision contract boundary and its role/resource/action policy ownership.

**Until the existing guarded change-control process records approval, the proposed owner remains unapproved and B2 production authorization must remain fail-closed.**

---

**Document classification:** Change request — not implementation evidence.  
**Approval status:** NOT APPROVED.  
**Production binding status:** BLOCKED ON GUARDED CORE-001 OWNER APPROVAL.
