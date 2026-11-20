
# HOMIO / REOS — B4 ARCH-037 Physical Persistence Addendum Approval Request

**Document ID:** `B4-ARCH037-ADDENDUM-REQUEST-01`  
**Status:** `DRAFT — OWNER REVIEW REQUIRED — NOT APPROVED — NON-EXECUTABLE`  
**Workstream:** `BACKEND-001-B4`  
**Canonical branch:** `reos-development`  
**Repository:** `prajaktaranjane80-sketch/Homio`

## 1. Immutable source baseline

This request was reconstructed from the live repository, not from an old chat snapshot.

| Authority | Exact live value |
|---|---|
| Repository HEAD | `95085b8b98eed60121ba2e1f25212ae21bd42b2b` |
| `REOS_CONTROL_CENTER/data/state.json` blob | `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b` |
| State integrity SHA-256 | `404000d70e7f03f168be7548e591b12f936da78703c033728afa9fbd58339bef` |
| `HOMIO_Backend_Structure` blob | `f8d9cd456568cc6c8eaae0caf764123a7e859ba6` |
| `backend-ci.yml` blob | `c225c7074c5a7ad5f950c853050a66b9c03f5c3f` |
| Existing B4 schema proposal blob | `dd823d25c693ad77c27bb0be065db209a17d5c17` |
| Existing B4 compatibility contract blob | `ac70688af4059ce4f0f531cd4b3f875a4ed02318` |
| Backend package lock blob | `ba7231c76767238ab55a506423ca8ebcfa280d18` |

`state.json` identifies `BACKEND-001-B4` as the current task. ARCH-037 v1.0 is already `APPROVED` and `FROZEN`; its recorded T01–T11 work and 11 acceptance criteria are not being reopened or edited by this request.

The approved architecture record does not currently resolve to a physical table/column/key/constraint catalogue in the live repository. The user's original `Real_Estate_OS_Master_Blueprint.docx` records both Database Schema and Entity Relationship Map as `Pending`; it does not supply an approved physical catalogue. The existing B4 physical-schema proposal and identifier/security compatibility contract are both drafts, not approved schema artifacts.

## 2. Purpose and strict boundary

Create a separately reviewed physical-persistence addendum to the frozen ARCH-037 v1.0. The addendum must map the existing canonical CORE owners to PostgreSQL without changing business ownership or introducing duplicate engines.

This request does **not**:

- amend or unfreeze ARCH-037 v1.0;
- authorize domain table DDL, backfills, production migrations, or destructive changes;
- alter CORE-001 through CORE-008 domain contracts;
- promote ACRL into a production authentication, persistence, or business runtime;
- authorize an ORM, second database abstraction, duplicate identity/tenant registry, duplicate event bus, duplicate audit engine, or parallel domain model;
- change `state.json` or mark any B4 criterion verified.

## 3. Canonical owner source evidence

The following live source files determine the semantic types and relationships. The hashes are the exact blobs read on `reos-development` at the baseline above.

| Owner | Canonical source | Blob SHA | Physical-design consequence |
|---|---|---|---|
| CORE-001 identity | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/identity.py` | `49564ab0e7b3f19d192c343bd444ba3b45ced192` | Identity/account UUID authority; account includes `authentication_epoch`; credentials and bearer tokens are forbidden from identity records |
| CORE-001 tenant | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/tenant.py` | `5fdda5750f37ea14214ede72ff97c739526390d6` | Tenant identity is UUID-based |
| CORE-001 membership | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership.py` | `919868a77bf589795c383a1fbb974fc69dede6ec` | Tenant, organization, identity, membership and grant references are typed UUID relationships |
| CORE-002 event | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/event_platform/event_domain.py` | `739016f22ab3730b566d2a5a136ed1f9fb9e0606` | Event and tenant identity are UUIDs; payload/metadata remain owner-validated data |
| CORE-002 outbox | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/event_platform/event_transaction.py` | `579605ac997debefb2fb0e2e17a227413988eade` | Existing outbox contract is a boundary contract, not an implementation; publication and event belong in the same owner transaction |
| CORE-003 lead | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/lead_ownership/lead.py` | `9b092087c5e4b820b5ee320abdb4c5fc00adcbce` | Lead, tenant and customer IDs are UUIDs |
| CORE-003 current ownership | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/lead_ownership/lead_ownership.py` | `dbb3917f6a3c2108bcb9de7c705cb0441758a7f7` | Current binding key is `(tenant_id, lead_id)`; there is no `ownership_record_id` field; this file explicitly delegates transfer history elsewhere |
| CORE-003 ownership transfer | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/lead_ownership/ownership_transfer.py` | `aaba13bb20c3494c3f32579ba7081cab5856a3a9` | Immutable transfer uses `transfer_id`, `(tenant_id, lead_id, new_revision)` history key and previous/new owner IDs |
| CORE-004 project | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/inventory/project.py` | `bc34a9729197cf55d8d29bda943be3d8d09dd2a9` | IDs are strings; `project_id` is technical identity; `(tenant_id, project_code)` is the documented business identity |
| CORE-004 inventory | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/inventory/inventory.py` | `be43bffd198d6c3f08c3aad641ed03696955f4e0` | Inventory, tenant, developer, project, property and unit references are strings; valid hierarchy differs by DEVELOPMENT/PROPERTY/UNIT |
| CORE-004 hierarchy | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/inventory/inventory_hierarchy.py` | `d625e332956b7a9001a4834d1631788f56bc145e` | Relationship nodes use typed node references and tenant scope; `unit_id` alone is not established as globally unique |
| CORE-006 deal | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/deal_transaction/deal.py` | `2fc25aaf118da6512e89d487a89f93cee9bc2da5` | Deal/customer/broker/builder/project/unit identifiers remain strings at the domain boundary |
| CORE-006 deal ownership binding | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/deal_transaction/deal_ownership_integration.py` | `bb68c87bc3c68bd22b17dd29a3afc2760d4eedf2` | `ownership_record_id` is an opaque string under ARCH-011; it is not proven to reference CORE-003 current binding or transfer primary key |
| CORE-008 financial amount | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/financial_domain.py` | `4b6af8da3ec7687c05b0a9782da305d2f267b3dc` | Python `Decimal`; currency minor unit is 0–6 and rounding is explicit; no universal maximum integral magnitude is defined |
| CORE-008 ledger | `REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/commission_financial/financial_ledger_boundary.py` | `b3c324aff41a449392ffef1b1d143621d6151ef6` | Financial ledger references are typed strings; do not merge into deal persistence |

## 4. Proposed physical compatibility decisions

These are safe boundaries for the approval review. They are not permission to run SQL.

| Decision | Proposed treatment | Reason / owner boundary | Approval state |
|---|---|---|---|
| CORE-001 identity/account/tenant/membership | Preserve UUID representation and owner-issued relationships; never store raw credentials, access tokens, refresh tokens or secrets | Direct CORE-001 type contracts | `CANDIDATE — VERIFY AGAINST FIXTURES` |
| CORE-002 event/outbox | Persist event and outbox publication atomically within the originating owner's transaction; validate schema/version before JSONB persistence | Existing EventEnvelope and OutboxContract | `CANDIDATE — OWNER REVIEW` |
| CORE-003 lead/attribution/ownership | Preserve UUID IDs, tenant-composite ownership, immutable transfer rows and revision/fingerprint semantics | CORE-003 current binding and transfer are different records | `CANDIDATE — OWNER REVIEW` |
| CORE-004 project | Preserve all IDs as text; enforce tenant-scoped `project_code` identity only after data uniqueness check; do not assume globally unique `project_id` | Source defines `(tenant_id, project_code)` as business identity | `REVIEW REQUIRED — CORE-004` |
| CORE-004 inventory hierarchy | Preserve typed hierarchy path; no standalone `unit_id` FK; no ID conversion | Source fields are opaque strings and hierarchy rules are type-specific | `CANDIDATE — OWNER REVIEW` |
| CORE-006 customer | Preserve CORE-006 `customer_id` as opaque text; do not FK it to CORE-003 UUID customer references until Customer owner mapping is approved | Cross-owner representation mismatch; Customer is a future ARCH-039 owner | `BLOCKED — CUSTOMER OWNER` |
| CORE-006 party references | Keep role plus opaque party ID; no universal FK to Identity | Buyer/seller/builder/broker/representative are polymorphic roles | `BLOCKED — CORE-001 + CORE-006 + FUTURE OWNERS` |
| CORE-006 unit/project links | No `unit_id`-only FK; project FK only after a tenant-scoped physical candidate key and existing-data audit are approved | CORE-004 path is tenant/project/property/unit | `BLOCKED — CORE-004 + CORE-006` |
| CORE-006 ownership link | Preserve `ownership_record_id` as opaque ARCH-011 reference; no FK until ARCH-011 identifies the target record and lifecycle | CORE-003 current binding has no such field; transfer uses `transfer_id` | `BLOCKED — ARCH-011 + CORE-003` |
| CORE-008 monetary values | Do not select `NUMERIC(18,2)`, `NUMERIC(20,6)` or any other typmod until every amount field's maximum magnitude, scale and serialization are owner-approved | `Decimal`/minor-unit semantics do not define maximum magnitude | `BLOCKED — CORE-008` |
| Financial subjects | Preserve `(subject_type, subject_id, subject_version)` as a typed polymorphic reference; no generic FK | Multiple subject kinds share string IDs | `CANDIDATE — CORE-008 REVIEW` |

A generic `TEXT`, permissive JSONB field, nullable FK, or application-only mock must not be used to conceal a blocked ownership decision.

## 5. Durable API session decision — not yet implementable under current contracts

The existing API security contract verifies the token and calls `SessionValidationPort.isSessionActive({ principal })` **before** invoking the CORE-001 trusted-context resolver. The principal exposes issuer, subject, audiences, client ID and `jti`, but not account ID, authentication epoch, token issued-at or expiry. B3 protocol v1's identity-resolution result likewise does not return account ID/authentication epoch.

A table containing only `(issuer, jti, revoked_at)` is insufficient to satisfy the existing backend security README. Before a session table or repository is frozen, CORE-001/B2/B3 owners must approve one backward-compatible contract and call order that binds the verified token to the canonical account and current authentication epoch, exposes validated `iat`/`exp`, and defines establishment, logout, revocation, account lock, epoch rotation, expiry and outage behavior. Do not weaken completed B3 v1 or enable customer-facing protected routes as a shortcut.

## 6. Shared Redis and minimized security audit

Relevant live backend sources: `REOS_CONTROL_CENTER/backend/src/security/contracts.ts` (`d03d183b61d69d2a590a88fa62f259f396eec83f`), `REOS_CONTROL_CENTER/backend/src/security/api-security.ts` (`827b4acea62112000a88615f755ecb229b96f6eb`), and `REOS_CONTROL_CENTER/backend/src/persistence/redis-rate-limit.ts` (`31878676c7a3141bc5e94188d44761d7761bf0df`). The B3 Python bridge contract is `REOS_CONTROL_CENTER/backend/src/integrations/python_runtime/contracts.ts` (`1bb86d28790f3a606f242603e2c06ad8ac0b6e79`).

The live backend already contains `REOS_CONTROL_CENTER/backend/src/persistence/redis-rate-limit.ts` with a Lua-atomic fixed-window counter, HMAC-derived Redis keys, explicit policies for the two existing RateLimitPort buckets, and fail-closed error handling. Its unit tests cover atomic command use, HMAC key separation, input validation, concurrency shape and Redis failure. This supersedes stale draft text that says no Redis adapter exists.

Still missing are the approved production Redis client/bootstrap, production secret/key-rotation configuration, approved thresholds and outage policy, and real Redis 8 integration evidence. Unit fixture thresholds are test values, not approved production policy.

The live `SecurityAuditPort` and minimized event contract exist, but there is no PostgreSQL security-audit repository in the backend source tree. Retention, privileged read access, and tenant/global pre-context event policy remain governance decisions. API security audit must remain distinct from CORE-008 financial audit and ARCH-014 business evidence. The current `REOS_CONTROL_CENTER/backend/package-lock.json` has no `pg`, `@types/pg` or `redis` runtime client package; adding production adapters therefore also requires a reviewed dependency/lockfile change and actual runtime configuration, not a type-only interface.

## 7. Migration engine candidate — separate from domain schema approval

A candidate `PostgresMigrationRunner` has been prototyped against the existing `PostgresDriverPool`/`PostgresDriverClient` contracts without replacing `PostgresRuntime`. Its safeguards are:

- fixed-width, strictly increasing migration IDs and unique immutable names;
- SHA-256 over the exact SQL source bytes;
- no sorting or repair of an invalid manifest;
- ordered history must be an exact prefix of the current manifest;
- applied SQL/name/order drift fails closed;
- verifies both `session_user` and `current_user` against an explicitly configured migration login, and requires that login to differ from the configured API application role;
- refuses targets below the ARCH-038 minimum PostgreSQL 18.4 (`server_version_num` 180004);
- PostgreSQL advisory lock serializes migration runners;
- each migration DDL and its history row commit in one transaction;
- rollback on a failed migration;
- no rollback or automatic retry when COMMIT outcome is unknown;
- connection destruction when lock ownership, rollback, unlock or connection state is uncertain.

The runner's `reos_infra.schema_migrations` ledger is itself an infrastructure schema object and must be included in the reviewed addendum. It must be created by a dedicated migration database role/pool, separate from the runtime API role; the runner requires both role names as explicit configuration and checks the live PostgreSQL session/effective roles before any DDL. The existing Postgres runtime role guard rejects application roles that own application tables; using one shared owner role would conflict with that protection. The configured role names and grants remain database-operations decisions. No domain migration is included or authorized by this request.

## 8. Tenant and transaction boundary

The existing `REOS_CONTROL_CENTER/backend/src/persistence/postgres.ts` (`732474d1dbdf091827c072784461e12a41987312`) remains the one API transaction owner. It checks the effective database role, rejects superuser/BYPASSRLS/application-table-owner contexts, checks FORCE RLS and restrictive tenant policies, sets transaction-local `app.tenant_id`, and uses one checked-out client through COMMIT/ROLLBACK. The existing PostgreSQL 18.4 CI integration fixture verifies role/RLS behavior against test tables, not the reconstructed CORE schema.

Every approved tenant-owned relation must include an owner-consistent tenant key, `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, and a restrictive `FOR ALL` tenant guard with both `USING` and `WITH CHECK`. Cross-owner FKs must include tenant scope wherever the owner model requires tenant-consistent linkage. Repository writes may only use the originating aggregate's explicit transaction boundary; outbox insertions share the originating transaction.

## 9. Backup and recovery proof

ARCH-038 selects PostgreSQL and a WAL/PITR-oriented backup strategy, but the B4 target environment's backup, restore, recovery-point and recovery-time evidence is not present in the live branch. A generic PostgreSQL test container does not prove managed target-service backup/restore. B4 cannot pass its backup/recovery criterion until a real target environment is configured and restore evidence is captured and independently verified.

## 10. Approval and execution boundary

ARCH-037 v1.0 remains frozen. This request proposes a separate immutable record named `ARCH-037-PHYSICAL-PERSISTENCE-ADDENDUM-01`; it does not declare that record approved.

The current repository has no dedicated ARCH-037 addendum approval transition. The existing Control Center `approve-gate` command approves and advances the current whole gate and is not an acceptable substitute. T17 produces impact evidence but does not mutate state. T18 explicitly rejects architecture changes and state mutation; its policy must not be weakened to manufacture approval.

Required owner decisions before domain DDL:

1. CORE-001 confirms canonical tenant/account serialization and session binding contract.
2. CORE-002 confirms transactional outbox persistence lifecycle and idempotency uniqueness.
3. CORE-003 and ARCH-011 resolve the ownership-record linkage.
4. CORE-004 and CORE-006 resolve project, property and unit references and audit existing identifiers.
5. Customer/Builder future owners resolve polymorphic party IDs; no new Customer/Builder lifecycle is created in B4.
6. CORE-008 approves each amount field's precision/range and ledger representation.
7. Security/privacy owners approve session lifecycle, Redis limits/outage policy, audit retention and privileged read access.
8. Architecture authority approves the exact addendum and the Control Center records that approval through a dedicated guarded path without changing ARCH-037 v1.0 or relaxing T18.
9. Database operations supplies a separate migration role/pool and real backup/restore test target.

Only after these approvals may domain migration SQL, repositories and real-service integration be added. Only after exact-HEAD CI, migration/concurrency/RLS tests and backup/restore evidence pass may B4's criteria be presented to the existing guarded Control Center completion process.

## 11. Current outcome

**B4 remains `CURRENT`, not `DONE`.** The existing PostgreSQL role/RLS and transaction foundation and Redis rate-limit adapter are reusable work, not proof that the complete B4 exit condition has been met. This document is an approval request and source-reconciliation record only. It does not mutate `state.json`, authorize production DDL, or mark any gate/subtask complete.
