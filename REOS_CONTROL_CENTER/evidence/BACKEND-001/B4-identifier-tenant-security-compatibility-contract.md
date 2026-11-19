# HOMIO / REOS — B4 Identifier, Tenant and Security Persistence Compatibility Contract

**Document type:** Source-backed engineering compatibility review  
**Status:** DRAFT — NOT APPROVED — NON-EXECUTABLE  
**Scope:** BACKEND-001-B4 PostgreSQL integration  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Baseline HEAD:** `307d8898151fd00bcdf74feccfef64bf26ff7726`  
**Canonical state blob:** `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b`  
**Backend master SHA:** `f8d9cd456568cc6c8eaae0caf764123a7e859ba6`  
**ARCH-039 master SHA:** `a4749f37afa0f4d5f9de65802bb4c99d3fce9f52`  
**Review date:** 19 November 2026

---

## 1. Decision boundary

This document defines source-backed persistence compatibility requirements and identifies unresolved owner decisions.

It does not:

- Amend or replace approved ARCH-037.
- Establish a new Customer, Builder, Identity, Deal or Financial owner.
- Approve physical SQL tables or migrations.
- Change `state.json`.
- Enable production session validation or protected customer routes.
- Authorize B3 protocol mutation or version changes.
- Introduce a new persistence framework, registry or orchestration layer.

Every proposed physical-schema rule below is classified as one of:

- **SOURCE FACT:** Explicitly present in an existing owner contract.
- **IMPLEMENTATION REQUIREMENT:** Needed to preserve the approved architecture.
- **CANDIDATE DECISION:** Proposed for formal review; not yet approved.
- **BLOCKER:** Cannot be implemented safely without the identified owner decision.

## 2. Canonical identifier contract

### 2.1 The fundamental rule

HOMIO / REOS must not force every identifier into UUID or TEXT indiscriminately.

The source code contains two intentionally different identifier families:

1. Native UUID identifiers in CORE-001, CORE-002 and CORE-003.
2. Opaque string identifiers in CORE-004, CORE-006 and CORE-008.

The correct persistence boundary must preserve the semantic meaning of each owner identifier.

A TypeScript string used to serialize a UUID does not mean the underlying database identifier should automatically become TEXT.

Likewise, a non-empty string accepted by a domain model must not automatically be converted into UUID.

### 2.2 Source-backed identifier matrix

| Owner | Identifier | Source type | Required persistence treatment |
|---|---|---|---|
| CORE-001 | identity_id | UUID | PostgreSQL UUID |
| CORE-001 | account_id | UUID | PostgreSQL UUID |
| CORE-001 | reference_id | UUID | PostgreSQL UUID |
| CORE-001 | tenant_id | UUID | PostgreSQL UUID |
| CORE-001 | organization_id | UUID | PostgreSQL UUID |
| CORE-001 | membership_id | UUID | PostgreSQL UUID |
| CORE-001 | permission_id | UUID | PostgreSQL UUID |
| CORE-001 | role_id | UUID | PostgreSQL UUID |
| CORE-001 | entitlement_id | UUID | PostgreSQL UUID |
| CORE-001 | scope_id | UUID | PostgreSQL UUID |
| CORE-002 | event_id | UUID | PostgreSQL UUID |
| CORE-002 | publication_id | UUID | PostgreSQL UUID |
| CORE-002 | correlation_id | UUID | PostgreSQL UUID |
| CORE-002 | causation_id | UUID or null | PostgreSQL UUID or NULL |
| CORE-003 | lead_id | UUID | PostgreSQL UUID |
| CORE-003 | tenant_id | UUID | PostgreSQL UUID |
| CORE-003 | customer_id | UUID | PostgreSQL UUID in Lead |
| CORE-003 | owner_id | UUID | PostgreSQL UUID where the canonical owner confirms identity semantics |
| CORE-004 | project_id | string | PostgreSQL TEXT |
| CORE-004 | inventory_id | string | PostgreSQL TEXT |
| CORE-004 | property_id | string or null | PostgreSQL TEXT or NULL |
| CORE-004 | unit_id | string or null | PostgreSQL TEXT or NULL |
| CORE-004 | developer_id | string | PostgreSQL TEXT |
| CORE-004 | tenant_id | string | Candidate canonical UUID serialization; validate before migration |
| CORE-006 | deal_id | string | PostgreSQL TEXT |
| CORE-006 | tenant_id | string | Candidate canonical UUID serialization; validate before migration |
| CORE-006 | customer_id | string | Opaque until Customer ID contract is approved |
| CORE-006 | broker_id | string | Opaque until the precise identity relationship is approved |
| CORE-006 | builder_id | string or null | Opaque future Builder reference |
| CORE-006 | project_id | string or null | TEXT; cross-owner reference requires verified key |
| CORE-006 | unit_id | string or null | TEXT; no direct unit-only FK |
| CORE-006 | party_id | string | Polymorphic reference; no universal FK |
| CORE-008 | financial_id | string | PostgreSQL TEXT |
| CORE-008 | tenant_id | string | Candidate canonical UUID serialization; validate before migration |
| CORE-008 | subject_id | string | PostgreSQL TEXT |
| CORE-008 | entry_id | string | PostgreSQL TEXT |
| CORE-008 | account_id reference | string | PostgreSQL TEXT until ledger-owner key contract is confirmed |

The matrix is an owner-compatibility map, not permission to create those tables independently.

### 2.3 Canonical tenant representation

**SOURCE FACT**

CORE-001's `Tenant.tenant_id` is UUID.

CORE-004, CORE-006 and CORE-008 expose `tenant_id` as non-empty strings.

**CANDIDATE DECISION**

The preferred physical representation is one canonical PostgreSQL UUID tenant key referencing CORE-001's tenant identity.

The string-based owner models should be adapted at the repository boundary:

`Python/TypeScript domain string → strict UUID parser → PostgreSQL UUID`

On reads:

`PostgreSQL UUID → canonical lowercase hyphenated UUID string`

Requirements:

- Reject malformed UUID strings.
- Reject empty values.
- Never trim, repair or guess an invalid tenant identifier.
- Never silently generate a different tenant ID.
- Preserve the exact tenant relationship on every read and write.
- Use canonical serialization for equality, hashing and composite-key construction.

**BLOCKER**

Before implementation, scan all existing CORE-004, CORE-006 and CORE-008 constructors, fixtures and serialized historical evidence to verify that their tenant strings are genuinely UUID serializations.

The current domain validators only require non-empty text in those owners. UUID compatibility must not be claimed merely because the TypeScript trusted-context contract validates UUIDs.

If any historical tenant identifier is not a canonical UUID, a separately reviewed compatibility migration is required.

## 3. Domain-specific identifier and ownership rules

### 3.1 CORE-001 — Identity and tenant

Relevant sources:

- `AUTONOMY_ENGINE/core/identity_tenant/identity.py`
- `AUTONOMY_ENGINE/core/identity_tenant/tenant.py`
- `AUTONOMY_ENGINE/core/identity_tenant/membership.py`
- `AUTONOMY_ENGINE/core/identity_tenant/identity_contract.json`

Canonical entities include:

- Identity
- IdentityAccount
- ExternalIdentityReference
- Tenant
- Organization
- Membership
- Relationship
- Permission
- Scope
- Entitlement
- Role

Required relationship semantics:

- IdentityAccount.identity_id references the canonical identity.
- ExternalIdentityReference.identity_id references the canonical identity.
- Organization.tenant_id references the canonical tenant.
- Membership preserves its canonical tenant, identity and organization relationships.
- Permission, role, entitlement and scope relationships preserve their existing UUID ownership.
- Parent organization relationships must remain tenant-consistent.
- Role and entitlement scope must not silently cross tenants.

Recommended database checks include tenant-composite foreign keys where the approved schema uses matching tenant-scoped keys.

The database schema must not introduce a second Identity or Membership table owned by the Fastify application.

### 3.2 CORE-002 — Events and outbox

Relevant sources:

- `AUTONOMY_ENGINE/core/event_platform/event_domain.py`
- `AUTONOMY_ENGINE/core/event_platform/event_transaction.py`

`EventEnvelope` explicitly uses UUID for:

- event_id
- tenant_id
- producer_id
- correlation_id
- causation_id

`OutboxContract` explicitly uses UUID for:

- publication_id
- event_id
- tenant_id

The `TransactionalPublicationBoundary` is an infrastructure protocol. CORE-002 explicitly does not own database transactions.

Required behavior:

- The aggregate owner's database transaction and its outbox record must commit atomically.
- A failed transaction must not leave an independently committed outbox record.
- A publisher must not expose an uncommitted event.
- Recovery must use the canonical event and publication identities.
- Duplicate publication and consumer replay must preserve CORE-002 idempotency semantics.
- Event schema and producer ownership must remain with CORE-002.

No second event bus, outbox registry or event-schema authority may be introduced.

### 3.3 CORE-003 — Lead and ownership

Relevant sources:

- `AUTONOMY_ENGINE/core/lead_ownership/lead.py`
- `AUTONOMY_ENGINE/core/lead_ownership/lead_attribution.py`
- `AUTONOMY_ENGINE/core/lead_ownership/lead_ownership.py`

`Lead` uses UUID for:

- lead_id
- tenant_id
- customer_id

`LeadAttribution` also uses UUID for lead_id and tenant_id.

Lead ownership has tenant-scoped identity and revision semantics.

Required behavior:

- Ownership binding remains under CORE-003.
- Lead attribution and historical ownership must remain traceable.
- Tenant-scoped uniqueness must be enforced at the database boundary.
- Lead ownership transfer must not overwrite historical ownership truth.
- Customer IDs must not be silently assigned to a new Customer table.

A deal's ownership link may reference a canonical CORE-003 lead after the source identifier is strictly normalized and the exact tenant/lead key is verified.

`ownership_record_id` must remain opaque until the canonical ownership-record identity is fully specified.

### 3.4 CORE-004 — Project and inventory hierarchy

Relevant sources:

- `AUTONOMY_ENGINE/core/inventory/project.py`
- `AUTONOMY_ENGINE/core/inventory/inventory.py`

`ProjectIdentity` uses:

- project_id: string
- tenant_id: string
- developer_id: string
- project_code: string

Its documented stable business identity is:

`tenant_id + project_code`

`InventoryIdentity` uses:

- inventory_id: string
- tenant_id: string
- developer_id: string
- project_id: string
- property_id: optional string
- unit_id: optional string

Its identity key includes the complete hierarchy path:

`tenant + inventory_type + project + property + unit + inventory`

Required persistence constraints:

- Project and inventory identifiers remain opaque TEXT.
- Tenant scope must be preserved.
- Inventory hierarchy rules must be enforced.
- Development inventory must not carry property or unit identity.
- Property inventory must have a property identity and no unit identity.
- Unit inventory must carry both property and unit identities.
- Inventory must remain bound to its canonical project owner.

**Critical FK restriction**

`unit_id` alone is not proven to be a unique, globally addressable target.

The existing hierarchy uses project and property context to distinguish inventory records.

Therefore, a foreign key from `Deal.unit_id` to `Inventory.unit_id` alone is not approved.

A valid unit relationship requires the exact canonical composite target key to be established and approved first.

`developer_id` must not be converted into a new Builder authority.

### 3.5 CORE-005 — Search and matching

Search is a derived read and retrieval boundary.

Search identity, filters, visibility and ranking must preserve the tenant and source-owner context.

Qdrant vectors and search projections must be rebuildable from canonical inventory and approved sources.

They must not become a second inventory source of truth.

### 3.6 CORE-006 — Deal and transaction

Relevant sources:

- `AUTONOMY_ENGINE/core/deal_transaction/deal.py`
- `AUTONOMY_ENGINE/core/deal_transaction/deal_parties.py`
- `AUTONOMY_ENGINE/core/deal_transaction/deal_ownership_integration.py`

The Deal aggregate uses string identifiers for:

- deal_id
- tenant_id
- customer_id
- broker_id
- builder_id
- project_id
- unit_id

Deal parties use:

- deal_id: string
- tenant_id: string
- party_id: string
- role: typed enum

The party roles are polymorphic:

- BUYER
- CUSTOMER
- SELLER
- BUILDER
- BROKER
- REPRESENTATIVE

Required behavior:

- Deal remains the sole transaction lifecycle owner.
- Deal party history remains within the deal aggregate boundary.
- Deal ownership and lead references preserve the existing ARCH-011/CORE-003 linkage.
- Customer and Builder references remain opaque until their future domain owners are approved.
- Financial obligations reference CORE-008 rather than moving financial logic into CORE-006.

A single `party_id` column must not have a universal foreign key to Identity. Different party roles may refer to different authorities.

**Candidate cross-owner relationships**

`Deal.project_id` and CORE-004 `ProjectIdentity.project_id` are both string-based references to a project.

A tenant-composite foreign key may be considered after:

1. Existing project IDs are validated.
2. Project uniqueness is formally defined.
3. The canonical tenant serialization is verified.
4. The approved ARCH-037 key strategy is reconciled.

`Deal.unit_id` has no approved direct FK to a unit-only field.

`Deal.customer_id` cannot safely receive a Customer foreign key because the Customer lifecycle owner is a future dedicated domain in ARCH-039.

### 3.7 CORE-007 — Trust, fraud and governance

Existing trust, fraud and governance records retain their own authority.

Persistence adapters must preserve:

- Tenant scope.
- Immutable review and decision history.
- Version and provenance.
- Evidence references.
- Approval and escalation linkage.
- Replay and concurrency protections.

The backend must not introduce a second policy-decision or fraud engine.

### 3.8 CORE-008 — Financial identity and ledger

Relevant sources:

- `AUTONOMY_ENGINE/core/commission_financial/financial_domain.py`
- `AUTONOMY_ENGINE/core/commission_financial/financial_ledger_boundary.py`
- `AUTONOMY_ENGINE/core/commission_financial/commission_financial_audit.py`

CORE-008 uses TEXT-based identifiers for its financial aggregate and typed subject references.

`FinancialSubject` uses a subject type plus subject ID and subject version.

The same subject ID representation is used across several different subject types.

Therefore:

- A generic `subject_id` foreign key is not valid.
- A subject-specific FK requires an approved subject-type mapping.
- Financial tenant scope must be preserved.
- Financial records must not be merged into CORE-006 deal storage.
- Commission financial audit remains distinct from API security audit and ARCH-014 business evidence.

`Currency` defines an explicit currency code, minor unit and rounding mode.

`MonetaryAmount` uses Python `Decimal` and rejects binary floating-point values.

**Precision blocker**

The current CORE-008 source does not define a maximum integral magnitude for every financial amount type.

The physical schema must not guess `NUMERIC(18,2)`, `NUMERIC(20,6)` or a single precision for every amount.

Before freezing numeric precision:

1. Inventory every financial field and maximum business magnitude.
2. Confirm supported currency precision.
3. Confirm rounding behavior.
4. Test maximum and minimum values.
5. Verify serialization between Python `Decimal`, PostgreSQL NUMERIC and TypeScript strings.
6. Verify arithmetic and round-trip integrity.

## 4. Cross-domain foreign-key decision matrix

| Relationship | Current treatment | Reason |
|---|---|---|
| Account → Identity | Candidate native UUID FK | Direct source relationship |
| External identity → Identity | Candidate native UUID FK | Direct source relationship |
| Organization → Tenant | Candidate native UUID FK | Direct source relationship |
| Membership → Identity/Tenant/Organization | Candidate composite/native UUID FKs | Owner defines these relationships |
| Lead Attribution → Lead | Candidate native UUID FK | Same canonical owner |
| Lead Ownership → Lead | Candidate tenant-scoped UUID FK | Same canonical owner |
| Inventory → Project | Candidate tenant-scoped composite FK | Both are CORE-004 |
| Deal → Project | Candidate tenant-scoped composite FK | Same project reference; uniqueness must be proven |
| Deal → Unit | BLOCKED | `unit_id` alone is not a proven unique key |
| Deal → Lead | Candidate normalized reference | Deal ownership binding uses lead_id as a CORE-003 reference |
| Deal → Customer | No FK | Customer is a future owner |
| Deal → Builder | No FK | Builder is a future owner |
| Deal Party → Identity | No universal FK | `party_id` is polymorphic |
| Financial Subject → Domain entity | No generic FK | Subject type is polymorphic |
| Security Audit → CORE-008 audit | No FK | Different audit authority |
| API audit → ARCH-014 evidence | No FK | Different evidence authority |
| Outbox → event identity | Candidate native UUID relation | CORE-002 event/publication relationship |

These are candidate physical relationships. They are not a substitute for the missing approved ARCH-037 table catalogue and keys.

## 5. Canonical UUID transport contract

The existing TypeScript security and B3 bridge contracts represent UUIDs as strings.

The persistence adapter must:

- Validate UUID syntax before database use.
- Use one canonical lowercase hyphenated serialization.
- Reject malformed values.
- Reject unsupported UUID versions if the source contract requires UUIDv4/approved versions.
- Never convert arbitrary IDs by guessing.
- Never use JavaScript numbers for identifiers.
- Never strip leading or trailing characters to make an invalid ID pass.
- Keep the source owner's semantic identifier type unchanged.

The B3 bridge currently has UUID validation for trusted identity, tenant, organization, membership and correlation identifiers.

The B3 bridge must remain read-only until its approved durable mutation/idempotency contract exists.

## 6. PostgreSQL tenant boundary

### 6.1 Required connection model

The approved backend master requires database-level tenant isolation.

The production persistence design must establish:

- Explicit PostgreSQL application role.
- Non-owner application privileges.
- No `BYPASSRLS` privilege for the ordinary runtime role.
- Tenant context established by trusted server-side resolution.
- Transaction-local tenant context.
- Tenant context cleared automatically at transaction completion.
- Fail-closed behavior if tenant context is absent or malformed.
- Explicit and audited administrative access.
- Separate migration/owner role from ordinary runtime role.

### 6.2 Pooled connection safety

Tenant context must be transaction-local.

Required sequence:

1. Check out one PostgreSQL client.
2. Begin the transaction.
3. Establish the canonical tenant context using a parameterized statement.
4. Perform all tenant-bound queries on that same client.
5. Commit or roll back.
6. Release the client only after transaction completion.

Do not establish tenant context through session-level pooled-connection state that can leak into the next request.

Do not use `pool.query` to execute different statements of one transaction.

### 6.3 Real database isolation tests

Application-level tenant filters are not sufficient proof.

The test suite must use the actual non-owner runtime role and PostgreSQL service to test:

- Tenant A cannot read Tenant B.
- Tenant A cannot update Tenant B.
- Tenant A cannot delete Tenant B.
- Missing tenant context is denied.
- Invalid tenant context is denied.
- Cross-tenant foreign-key references are rejected.
- Administrative access is restricted.
- Pooled connection reuse does not leak context.

## 7. Durable API session and revocation — critical contract gap

### 7.1 Existing owner facts

CORE-001 `IdentityAccount` contains:

- account_id
- identity_id
- status
- authentication_epoch
- created_at
- updated_at

Its source documentation explicitly states that credentials, sessions and authentication material do not belong in the IdentityAccount object.

The existing backend security README requires durable session validation to include:

- Session status.
- Canonical CORE-001 account authentication epoch.
- Revocation state.

The B2 `SessionValidationPort` currently receives only a `VerifiedExternalPrincipal` containing:

- issuer
- subject
- audiences
- clientId
- tokenId (`jti`)

It does not receive:

- accountId
- authenticationEpoch
- token issued-at
- token expiry

### 7.2 Existing call-order problem

The current Fastify security flow is:

1. Verify bearer token.
2. Call `SessionValidationPort.isSessionActive({ principal })`.
3. Resolve CORE-001 trusted context.
4. Authorize the operation.
5. Persist minimized audit event.
6. Continue to handler.

Therefore the session validator cannot consume the already-resolved account ID or membership context.

It would need a separate trusted CORE-001 account resolution path, or the security port and execution order would need an approved contract update.

### 7.3 Existing B3 protocol gap

B3 protocol version 1 allows:

- `oidc.verify_access_token`
- `core001.identity.resolve`
- `core001.tenant.resolve_context`
- `core001.membership.resolve`

The current OIDC projection returns issuer, subject, audiences, clientId and tokenId.

Although the Python verifier validates token expiry and issuance claims, those timestamps are not returned in the principal contract.

The current `core001.identity.resolve` result returns identity ID and external reference ID, not account ID or authentication epoch.

The existing `IdentityRegistry` can retrieve an account by account ID, but the external identity resolution path does not return the account ID.

### 7.4 Why a simple revocation table is insufficient

Persisting only `(issuer, jti, revoked_at)` does not prove all required security behavior.

It does not, by itself, establish:

- The current canonical account.
- The account's current authentication epoch.
- Whether the account is still enabled.
- Whether the token is expired.
- Whether the session is active under the authoritative account lifecycle.
- Whether a revocation check is occurring against the canonical identity.

No raw bearer token may be persisted.

### 7.5 Required contract resolution

Before declaring durable session support complete, the owner-controlled design must define:

1. How an access token is bound to the canonical CORE-001 identity and account.
2. How the current account authentication epoch is resolved.
3. How verified token issuance and expiry timestamps are made available.
4. How a session is established and becomes durable.
5. How logout, revocation, account lock, identity suspension and epoch rotation invalidate existing access.
6. How unknown, expired and revoked sessions fail closed.
7. How session creation and revocation behave during outages and retries.
8. How token identifiers are retained or minimized without storing bearer credentials.

**Candidate technical approach**

Reuse CORE-001 as the identity/account authority and the existing B3 authenticated runtime boundary as the private transport.

A versioned, backward-compatible contract revision may be needed to expose the verified token timestamps and the canonical account/authentication context.

The session adapter should consume only trusted verified information and canonical owner results. It must not build an independent IdentityRegistry or second account database.

The final design must choose and test one exact account-epoch invalidation protocol before an API session table is frozen.

**BLOCKER**

The current B2 session port and B3 v1 protocol do not yet expose all the data required by the approved backend security README.

Do not claim that a denylist alone closes this gap.

Do not silently alter the completed B3 contract or enable protected routes.

Any protocol change requires compatibility analysis, regression tests and the existing guarded owner-approval boundary.

## 8. Shared Redis rate-limit persistence

### 8.1 Existing port

The existing `RateLimitPort` has only two bucket categories:

- `api-ip`
- `api-identity-tenant`

The adapter receives a string key and returns an allow/deny decision with optional retry-after seconds.

There is no production Redis adapter in the current backend source tree.

### 8.2 Required design

The implementation must use shared Redis state rather than in-process counters.

The design must specify:

- Approved threshold for each bucket.
- Window duration.
- Atomic counter/window update.
- Counter expiry.
- Retry-after calculation.
- Concurrent request behavior.
- Multi-instance behavior.
- Redis outage behavior.
- Recovery after an outage.
- Key rotation/namespace policy.
- Tenant fairness and abuse protection.

Raw IP addresses and identity identifiers must not be exposed in logs or used as unrestricted Redis keys.

Use a keyed HMAC-derived key representation where appropriate, with secrets outside the source tree and a defined rotation strategy.

Rate-limit policy thresholds must be explicit configuration, not invented by the storage adapter.

Redis must remain ephemeral coordination infrastructure, not a second business database.

## 9. Minimized API security audit persistence

### 9.1 Existing owners and restrictions

The repository contains:

- `AUTONOMY_ENGINE/observability/audit.py`: local JSONL recorder.
- `AUTONOMY_ENGINE/execution/execution_audit.py`: in-memory execution audit boundary.
- `CORE-008/commission_financial_audit.py`: financial audit chain.

None is the canonical PostgreSQL API security audit adapter.

The existing API security contract defines `SecurityAuditPort`.

It records only the approved minimized event fields:

- eventType
- requestId
- occurredAt
- reasonCode
- operation
- actorIdentityId
- tenantId

### 9.2 Required persistence behavior

The B4 storage adapter must persist the existing security audit event without inventing a second audit engine.

Requirements:

- Append-only or otherwise immutable audit history.
- Server-generated event/request identifiers.
- Timezone-aware timestamps.
- Canonical actor and tenant references where available.
- Explicit event-type and reason-code validation.
- No raw access token.
- No password, secret or authorization header.
- No email or OIDC subject.
- No request body.
- No unnecessary client IP.
- No cross-tenant audit visibility.
- Defined retention and restricted audit access.
- Duplicate request handling and concurrency safety.

Protected requests already fail closed when the audit port is unavailable.

That behavior must be tested against the real PostgreSQL service.

API security audit must remain separate from CORE-008 financial audit and ARCH-014 business evidence.

## 10. Approved dependency and transaction boundary

The approved stack is:

- PostgreSQL 18.4+.
- `node-postgres` as the Node.js PostgreSQL access driver.
- Redis 8 for shared ephemeral coordination.

Implementation rules:

- No new ORM.
- No parallel persistence framework.
- No hidden in-memory production fallback.
- Parameterized SQL only.
- Explicit connection-pool ownership.
- Explicit transaction ownership.
- One checked-out PostgreSQL client for every transaction.
- Connection release in `finally`.
- Safe rollback handling.
- Bounded connection acquisition and query timeouts.
- No retry of ambiguous mutations without durable idempotency identity.
- No raw SQL access from route handlers.

Before adding dependencies, update the existing package manifest and exact lockfile in the same implementation change.

Pin exact approved versions and verify with clean `npm ci` and the reproducible-build checks.

## 11. Concrete repository implementation constraints

The existing canonical backend is:

`REOS_CONTROL_CENTER/backend/`

Its current source has one Fastify application and existing security and B3 runtime owners.

The future B4 database migration directory remains conditional on approved physical schema and ownership.

Do not add:

- A second backend application.
- A second API ingress.
- A new Python HTTP service.
- A second identity or tenant registry.
- A new generic domain repository framework.
- A generic database abstraction that duplicates node-postgres.
- A new event bus or audit engine.
- A parallel idempotency registry.
- A duplicate CORE aggregate model set.
- A Customer or Builder business table without its approved owner.

Use the existing Fastify security ports, CORE owners and private Python runtime boundary.

## 12. Mandatory B4 adversarial compatibility tests

### Identifier tests

- Canonical UUID round-trip across TypeScript, Python and PostgreSQL.
- Uppercase UUID normalization at the approved serialization boundary.
- Invalid UUID rejection.
- Non-UUID opaque project/inventory/deal/financial identifiers remain unchanged.
- No numeric coercion of IDs.
- No whitespace repair.
- No empty identifier acceptance.
- No accidental conversion of `unit_id` into an inventory primary key.

### Tenant tests

- CORE-001 UUID tenant maps to the canonical persistence tenant.
- String-based owner tenant IDs reject non-UUID values if UUID serialization is approved.
- Wrong tenant is rejected at repository and database boundaries.
- Composite references cannot cross tenants.
- RLS denies reads and writes for another tenant.
- Pool reuse does not leak tenant context.

### Domain ownership tests

- CORE-003 lead identity remains UUID.
- CORE-004 project/inventory identities remain opaque strings.
- CORE-006 deal and polymorphic party identifiers retain their source semantics.
- CORE-008 financial subject IDs remain typed opaque references.
- Future Customer/Builder domains are not simulated by duplicate tables.
- No generic foreign key is created for polymorphic subject or party references.

### Financial tests

- Exact Decimal round-trip.
- Binary floating-point rejection.
- Currency/minor-unit and rounding behavior.
- Maximum and minimum approved amount values.
- Numeric overflow rejection.
- Ledger immutability.
- Reversal and adjustment integrity.
- Cross-currency arithmetic rejection.

### Session tests

- Verified token with active canonical account.
- Expired token.
- Revoked token.
- Unknown session.
- Disabled or locked account.
- Authentication epoch rotation.
- Identity suspension.
- Missing account binding.
- OIDC/JWKS dependency outage.
- Session persistence outage.
- Replay and duplicate revocation.
- No raw bearer token in database, logs or audit.

The tests must validate the approved session-epoch design, not merely a synthetic `jti` denylist.

### Redis and audit tests

- Shared rate limit across independent clients.
- Concurrent counter updates.
- Expiry and retry-after correctness.
- Redis outage and recovery.
- Audit insertion before protected handler execution.
- Audit database failure returns the existing fail-closed response.
- No unnecessary PII or credentials in persisted events.
- Append-only audit tampering detection or denial.

### Migration and recovery tests

- Fresh install.
- Ordered upgrade.
- Duplicate migration rejection.
- Modified historical migration checksum rejection.
- Concurrent migration runners.
- Interrupted migration.
- Restore and post-restore verification.
- Point-in-time recovery test.
- Tenant isolation after recovery.
- No data loss in the canonical event/outbox transaction.

All database integration tests must execute against the actual PostgreSQL service using the application role, not a privileged migration owner.

## 13. Open decision register

| ID | Decision | Status | Must be resolved by |
|---|---|---|---|
| B4-ID-01 | Confirm CORE-004/006/008 tenant strings are canonical UUID serializations | BLOCKED | Existing owner model + fixture audit |
| B4-ID-02 | Confirm Customer ID representation across CORE-003 and CORE-006 | BLOCKED | Customer architecture owner |
| B4-ID-03 | Confirm project_id physical uniqueness and tenant-composite key | REVIEW REQUIRED | CORE-004 owner |
| B4-ID-04 | Define the canonical unit reference key for Deal | BLOCKED | CORE-004 + CORE-006 |
| B4-ID-05 | Define which polymorphic party roles resolve to which canonical owners | BLOCKED | CORE-001 + CORE-006 + future domain owners |
| B4-ID-06 | Define CORE-003 ownership_record_id identity contract | BLOCKED | CORE-003 owner |
| B4-ID-07 | Define per-field financial precision and maximum magnitude | BLOCKED | CORE-008 owner |
| B4-SEC-01 | Bind verified OIDC principal to account ID and authentication epoch | BLOCKED | CORE-001 + security contract owner |
| B4-SEC-02 | Expose verified token issued-at and expiry claims | BLOCKED | Existing OIDC/B3 protocol owners |
| B4-SEC-03 | Define durable session establishment and revocation lifecycle | BLOCKED | Security/session owner |
| B4-SEC-04 | Align session port and API security call order | BLOCKED | Existing B2 security owner |
| B4-SEC-05 | Approve rate-limit thresholds, windows and outage policy | REVIEW REQUIRED | Security/policy owner |
| B4-SEC-06 | Approve security audit retention and privileged read policy | REVIEW REQUIRED | Privacy/security governance |
| B4-ARCH-01 | Reconcile reconstructed physical schema with frozen ARCH-037 | BLOCKED | Authorized architecture approval |

No blocked decision may be hidden by a generic `TEXT` column, nullable foreign key, permissive JSON field or mock implementation.

## 14. Required implementation order after the decisions are approved

1. Complete the source and fixture audit for tenant and identifier compatibility.
2. Resolve B4-ID-01 through B4-ID-07 with their existing owners.
3. Resolve B4-SEC-01 through B4-SEC-06 without weakening B2, B3 or T18.
4. Build the exact physical entity/key/constraint/index/RLS catalogue.
5. Reconcile it with the approved ARCH-037 specification and complete the required architecture approval process.
6. Freeze the approved schema fingerprint.
7. Add immutable SQL migrations and migration-integrity validation.
8. Add the existing backend's PostgreSQL pool and repository implementations.
9. Add transaction-local tenant context and real PostgreSQL RLS tests.
10. Add durable session/revocation persistence only after session creation and authentication-epoch contracts are complete.
11. Add shared Redis rate limiting and minimized PostgreSQL security audit persistence.
12. Run migration, concurrency, cross-tenant, backup, restore and recovery tests.
13. Re-run exact-SHA backend and ACRL CI.
14. Request the guarded B4 Control Center transition only when every B4 criterion has evidence.

## 15. Current execution status

**Baseline HEAD:** `307d8898151fd00bcdf74feccfef64bf26ff7726`

**Canonical state:** `BACKEND-001-B4 CURRENT`

**Backend gate AC01–AC10:** PENDING

**B4 acceptance criteria:** Not yet verified

**Physical migrations:** Not implemented

**Durable production session binding:** Not implemented

**Redis production adapter:** Not implemented

**PostgreSQL security audit adapter:** Not implemented

**Production readiness:** Not claimed

This document is evidence for the next design and implementation decisions. It is not approval, migration evidence or B4 completion evidence.

**Final document status: DRAFT — NOT APPROVED — NON-EXECUTABLE.**
