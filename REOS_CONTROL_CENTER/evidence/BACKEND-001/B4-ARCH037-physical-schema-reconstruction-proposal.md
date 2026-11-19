# HOMIO / REOS — B4 ARCH-037 Physical Schema Reconstruction Review

**Document type:** Architecture reconstruction proposal and B4 readiness evidence  
**Status:** DRAFT — NOT APPROVED — NON-EXECUTABLE  
**Project:** HOMIO / REOS  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Review baseline:** `e04b46aeaec69d98072fcc81a79155914f4f1865`  
**Canonical state blob:** `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b`  
**Backend master SHA:** `f8d9cd456568cc6c8eaae0caf764123a7e859ba6`  
**Master architecture SHA:** `a4749f37afa0f4d5f9de65802bb4c99d3fce9f52`  
**Review date:** 19 November 2026

---

## 1. Purpose

This document records the evidence required to reconstruct the missing physical database-schema specification for the already-approved ARCH-037 architecture.

The goal is to make B4 PostgreSQL integration implementable without:

- Introducing a second business-data model.
- Duplicating CORE-001 through CORE-008 ownership.
- Creating separate Customer, Builder, Communication or Evidence authorities.
- Weakening tenant isolation or authorization.
- Enabling production mutations before durable persistence and transaction guarantees exist.
- Treating an inferred schema as an already-approved architecture.

This is a reconstruction proposal. It does not amend ARCH-037, change the canonical project state, approve new table definitions or authorize production migrations.

## 2. Existing architectural authority

The following decisions are already approved and must be reused.

| Authority | Existing approved decision |
|---|---|
| ARCH-037 | Database Final Schema Design v1.0 |
| ARCH-038 | Technology Stack Lock v1.0 |
| ARCH-039 | HOMIO / REOS Master Architecture |
| CORE-001 | Identity, tenant and membership ownership |
| CORE-002 | Event platform ownership |
| CORE-003 | Lead and lead-ownership domain |
| CORE-004 | Inventory and project domain |
| CORE-005 | Search and matching domain |
| CORE-006 | Deal and transaction domain |
| CORE-007 | Trust, fraud and governance domain |
| CORE-008 | Commission and financial domain |
| ARCH-009 | Communication ownership |
| ARCH-014 | Evidence, consent, visit and enquiry-proof ownership |

ARCH-037 is recorded as APPROVED in canonical state, dated 15 August 2026. Its T01–T11 and AC01–AC11 records are complete.

However, the accessible approval records contain high-level completion descriptions. They do not expose the actual physical table catalogue, column definitions, SQL types, keys, constraints, indexes, tenant-policy DDL or approved migration manifest.

The approved decision and the missing physical implementation specification must therefore be treated as two different things.

## 3. Repository evidence

The live `reos-development` tree contains 2,568 entries and was not truncated during inspection.

The search found no canonical PostgreSQL migration directory, approved business-table DDL, physical schema catalogue or ERD.

The existing `AUTONOMY_ENGINE/schemas/` files are application/continuity contract schemas. For example, `session_state.schema.json` is not a PostgreSQL production session-table definition.

The backend currently has:

- One Fastify application.
- Existing security contracts and ports.
- Existing CORE-001 through CORE-008 domain owners.
- No PostgreSQL driver dependency in the current backend package manifest.
- No Redis client dependency in the current backend package manifest.
- No approved B4 migration files.

This means a generic migration runner or a collection of newly invented business tables must not be represented as completion of B4.

## 4. Existing domain-owner mapping

The following is a source-backed ownership map. It identifies the existing domain records that a physical persistence design must preserve. It is not a final table catalogue.

### CORE-001 — Identity, tenant and membership

Existing source models include:

- `Identity`
- `IdentityAccount`
- `ExternalIdentityReference`
- `Tenant`
- `TenantConfigurationReference`
- `TenantSecurityProfileReference`
- `TenantRegionJurisdictionReference`
- `TenantProvisioningIntent`
- `Organization`
- `Membership`
- `Relationship`
- `Permission`
- `Scope`
- `Entitlement`
- `Role`

The persistent design must preserve identity, account, external-identity, tenant and membership ownership here.

It must not create a second identity or membership authority inside the public Fastify application.

### CORE-002 — Event platform

Existing source models include:

- `EventEnvelope`
- `EventTraceContext`
- `OutboxContract`
- Publication state and transaction-boundary contracts.

The outbox must be committed atomically with the aggregate change it represents.

The B4 implementation must not create a second event bus or a second event-schema authority.

### CORE-003 — Lead and ownership

Existing source models include:

- `Lead`
- `LeadSource`
- `LeadAttribution`
- Lead ownership and ownership-transfer contracts.

Lead attribution and ownership history remain under CORE-003.

A lead's customer reference does not authorize the creation of an independent Customer lifecycle or Customer source of truth.

### CORE-004 — Inventory and project

Existing source models include:

- `ProjectIdentity`
- `Project`
- `InventoryIdentity`
- `Inventory`
- Inventory lifecycle and availability contracts.
- Inventory hierarchy, provenance and commercial-state contracts.

Project and inventory write ownership remains in CORE-004.

`developer_id` and other external domain references must not create a new Builder authority in B4.

### CORE-005 — Search and matching

Existing source models include:

- Search request and tenant context.
- Search identity and result contracts.
- Matching, ranking, filtering and visibility contracts.
- Hybrid retrieval and Qdrant integration.

Search indexes and AI embeddings are derived data, not a second inventory or project source of truth.

PostgreSQL/PostGIS structured search and Qdrant vector/hybrid retrieval must follow ARCH-023 and the existing CORE-005 contracts.

Derived projections must be rebuildable from approved canonical sources.

### CORE-006 — Deal and transaction

The existing `Deal` aggregate contains:

- Deal identity and tenant reference.
- Customer, broker and optional builder references.
- Project and unit references.
- Deal status and version.
- Lifecycle history.
- Offers and negotiation.
- Transaction milestones.
- Ownership binding.
- Evidence references.
- Audit references.
- Deal participants.

CORE-006 owns deal state and transaction lifecycle.

It does not own commission calculation, invoicing or settlement. Those remain with CORE-008.

Customer, Builder, Project and Unit references must remain references to their respective owners.

### CORE-007 — Trust, fraud and governance

Existing source models include:

- Trust scoring model and signals.
- Trust score contributions and records.
- Fraud detection policy, findings and assessments.
- Governance decisions and escalation/review contracts.
- Approval and dispute-governance boundaries.

CORE-007 remains the trust, fraud and governance decision owner.

The persistence layer must not reimplement these decision engines.

### CORE-008 — Commission and financial

Existing financial models include:

- `Currency`
- `MonetaryAmount`
- `FinancialSubject`
- `FinancialIdentity`
- `FinancialDomainRecord`
- Ledger account and ledger-entry contracts.
- Commission contract, entitlement and calculation.
- Allocation and participant split.
- Invoice, settlement and reconciliation.
- Dispute, release, adjustment and tax.
- Financial audit, statement and closeout.

Financial values use Python `Decimal` semantics and explicit currency/minor-unit and rounding rules.

PostgreSQL persistence must use exact decimal types. Floating-point storage or arithmetic is not permitted as canonical financial representation.

CORE-008 remains the commission and financial authority; no second ledger or settlement engine may be introduced.

## 5. Non-negotiable authority boundaries

The canonical Master Architecture explicitly defines these boundaries:

| Responsibility | Required owner |
|---|---|
| Customer lifecycle and business truth | Future dedicated Customer domain |
| Builder lifecycle and business truth | Future dedicated Builder domain |
| Communication content and delivery history | ARCH-009 |
| Evidence, consent and proof records | ARCH-014 |
| Identity, tenant and membership | CORE-001 |
| Lead ownership and attribution | CORE-003 |
| Inventory and project | CORE-004 |
| Deal and transaction | CORE-006 |
| Commission and financial truth | CORE-008 |
| Developer continuity and reconstruction | ACRL |

No B4 migration may create a competing owner for any responsibility above.

ACRL state, checkpoints, recovery metadata and handoff data must never become production business records.

## 6. Critical schema blockers discovered

### 6.1 Identifier type mismatch

The existing source contracts do not use one consistent identifier representation.

| Existing owner | Identifier representation observed |
|---|---|
| CORE-001 | UUID for identity and tenant identifiers |
| CORE-002 | UUID for event and tenant identifiers |
| CORE-003 | UUID for lead, tenant and customer references |
| CORE-004 | String identifiers for project, inventory and tenant |
| CORE-006 | String identifiers for deal, tenant and party references |
| CORE-008 | String identifiers for financial identity and tenant |

There is also a direct cross-owner issue:

- CORE-003 `Lead.customer_id` is UUID.
- CORE-006 `Deal.customer_id` is string.
- CORE-001 tenant identity uses UUID.
- CORE-004, CORE-006 and CORE-008 expose tenant identifiers as strings.

A database migration must not silently choose UUID or TEXT for all domains without a compatibility decision.

Required resolution before DDL:

1. Define one canonical identifier serialization and validation contract.
2. Define how existing UUID values are represented across TypeScript and Python.
3. Define how CORE-004, CORE-006 and CORE-008 tenant strings bind to CORE-001 tenant identity.
4. Define which cross-domain references can be enforced with real foreign keys.
5. Preserve opaque references where the target domain has no approved lifecycle owner.
6. Add contract tests for round-trip conversion, invalid identifiers and tenant mismatch.

No production foreign-key design should be frozen before this resolution.

### 6.2 Tenant and Row-Level Security

The approved backend master requires database-level tenant enforcement where PostgreSQL Row-Level Security is used.

The final design must specify:

- Which tables are tenant-scoped.
- Which tables are global or platform-scoped.
- How tenant context is established by the trusted server.
- The exact transaction-local tenant-context mechanism.
- Application database roles that cannot bypass RLS.
- Whether FORCE ROW LEVEL SECURITY is required for each table.
- Explicitly controlled administrative access.
- Fail-closed behavior when tenant context is missing.
- Connection-pool reuse and tenant-context cleanup behavior.

Application-level `WHERE tenant_id = ...` filters alone are not sufficient proof.

Cross-tenant negative tests must execute against the real PostgreSQL service using the same non-owner application role used by the integration runtime.

### 6.3 Customer and Builder references

Customer and Builder are future dedicated architecture boundaries in ARCH-039.

B4 must not create `customers` or `builders` tables as a shortcut.

Existing CORE models may retain opaque references, but no independent Customer or Builder lifecycle may be introduced through a persistence adapter.

### 6.4 Financial precision and history

The physical model must preserve:

- Explicit currency code.
- Currency minor-unit semantics.
- Approved rounding policy.
- Exact decimal storage.
- Immutable posted financial entries.
- Reversal and adjustment rather than destructive history mutation.
- Idempotent settlement.
- Reconciliation and audit linkage.
- Concurrency protection.

The final numeric precision and scale for each financial field must be derived from the approved CORE-008 contracts and reviewed against all financial calculations. A single arbitrary precision/scale must not be applied to every financial concept without evidence.

### 6.5 Event/outbox transaction ownership

The aggregate owner and CORE-002 event owner must have an explicit transaction contract.

Required behavior:

- Aggregate state and its outbox record commit atomically.
- Event IDs, correlation IDs, causation IDs, tenant context and version are preserved.
- Duplicate publication and consumer replay are idempotent.
- Failed publication is recoverable.
- No event is published before its owning database transaction commits.

A second event registry or independent outbox authority must not be introduced.

### 6.6 Durable API session and revocation storage

The existing Fastify security contract defines `SessionValidationPort`.

It uses the verified external principal's token identifier (`jti`) for session/revocation validation. The raw bearer token must never be persisted.

B4 must provide durable backing persistence for the existing port, without wiring production routes prematurely.

The persisted contract must define expiry, revocation, issuer/subject binding, tenant context where applicable, concurrency and cleanup/retention behavior.

### 6.7 Shared rate-limit state

ARCH-038 locks Redis 8 for shared cache and ephemeral coordination.

The rate-limit implementation must use shared/distributed state, not per-process in-memory counters.

The selected Redis client and exact dependency version must be pinned in the package lockfile. Atomic increment/window behavior, expiry, concurrency and fail-closed/degraded behavior must be tested across independent clients.

Rate-limit counters are ephemeral coordination state; they must not become a second business database.

### 6.8 Minimized security audit persistence

The existing `SecurityAuditPort` requires PII-minimized structured audit persistence through the approved audit owner.

The design must define:

- Allowed event types and fields.
- Tenant and actor scope.
- Correlation and request identifiers.
- Append-only or immutable-history behavior.
- Retention and access controls.
- Redaction and privacy boundaries.
- Audit-write failure behavior.

Raw bearer tokens, passwords, secrets and unnecessary personal data must never be stored.

Security audit events must remain distinct from ARCH-014 business evidence and CORE-008 financial audit records.

## 7. Approved stack to reuse

The following technology decisions are already locked and should be reused:

| Area | Approved choice |
|---|---|
| Public API | Fastify 5 |
| Runtime | Node.js 24 |
| Language | TypeScript |
| Authoritative relational database | PostgreSQL 18.4+ |
| Node PostgreSQL driver | `node-postgres` |
| Shared rate-limit/cache coordination | Redis 8 |
| Event transport | Kafka |
| Long-running critical workflows | Temporal |
| Structured spatial search | PostgreSQL/PostGIS |
| Vector/hybrid search | Qdrant |
| Large binary artifacts | S3-compatible object storage |

No new ORM or second persistence framework is proposed.

PostgreSQL remains the authoritative relational store. Redis, Qdrant and S3 must retain their approved responsibilities and must not become competing business-data authorities.

## 8. Required migration and repository controls

Once the physical schema is formally approved, implementation must use:

1. Immutable, versioned SQL migration files.
2. Deterministic migration ordering.
3. SHA-256 migration integrity checks.
4. Database migration locking.
5. Duplicate and out-of-order migration rejection.
6. Fail-closed handling of checksum mismatch.
7. Explicit migration transaction behavior.
8. Expand-migrate-contract compatibility for destructive or breaking changes.
9. Explicit approval for destructive schema changes.
10. Tenant-aware migration validation.
11. Recovery and rollback/reconciliation procedures.
12. `node-postgres` parameterized queries and explicit transaction boundaries.

Previously applied migrations must never be silently edited or replaced.

The exact migration metadata table and migration-runner contract must be included in the approved physical schema specification before implementation.

## 9. Required B4 test matrix

The following evidence is required before B4 can be closed.

| Test group | Required scenarios |
|---|---|
| Schema integrity | Approved schema fingerprint, expected objects, missing/extra objects |
| Migration ordering | Fresh install, ordered upgrade, duplicate application, out-of-order rejection |
| Migration integrity | Correct checksum, tampered checksum, modified historical migration |
| Concurrent migration | Two migration runners, lock timeout, interrupted execution |
| Tenant security | Tenant A/B isolation, missing context, forged context, cross-tenant writes |
| Pool safety | Transaction-local tenant context does not leak to another pooled request |
| Repository ownership | One write owner per aggregate; no cross-domain direct writes |
| Transactions | Commit, rollback, nested failure, connection loss and retry |
| Event consistency | Atomic outbox, duplicate delivery, crash recovery and replay |
| Financial safety | Exact decimals, currency mismatch, rounding, stale version and concurrent settlement |
| Session security | Active, expired, revoked, unknown and cross-tenant session |
| Rate limiting | Concurrent clients, shared counters, expiry, Redis outage and recovery |
| Audit security | Minimized fields, redaction, append-only behavior and audit failure handling |
| Backup/recovery | Backup integrity, restore, PITR and post-restore consistency |
| Reproducibility | Clean `npm ci`, locked dependencies, build and integration suites |

Integration evidence must identify the exact source SHA and actual PostgreSQL/Redis service versions used.

A test that was not executed against the real target service must not be reported as passed.

## 10. Required implementation sequence after approval

The implementation sequence must remain inside the current B4 task and must not advance unrelated gates.

1. Resolve identifier and tenant-contract compatibility.
2. Produce the complete physical schema specification from existing canonical owners.
3. Review keys, relations, uniqueness, indexes, RLS, privacy, financial precision and retention.
4. Obtain the required architecture amendment approval and persist its evidence through the authorized Control Center process.
5. Freeze the approved schema manifest and establish its immutable fingerprint.
6. Implement the approved migrations and migration integrity runner.
7. Implement PostgreSQL pool, repository and explicit transaction boundaries.
8. Implement tenant enforcement and real PostgreSQL negative tests.
9. Implement durable session/revocation and minimized security audit persistence for the existing ports.
10. Implement shared Redis rate-limit storage.
11. Add migration, concurrency, recovery and backup/restore verification.
12. Reconcile exact-SHA Actions evidence and required B4 acceptance criteria.

The B3 Python bridge must remain read-only until the approved durable transaction and idempotency owner is implemented and verified.

B2 production binding remains after B4.

## 11. Architecture-change and freeze boundary

The current canonical state records:

- ARCH-037 as APPROVED.
- `no_silent_architecture_changes = true`.
- `architecture_before_code = true`.
- An architecture-change human-approval gate.
- A requirement for a change request, duplicate/dependency/impact review and explicit user approval before changing the authoritative sequence.

The existing T02 architecture-lock component is read-only.

The existing T18 authorization policy explicitly forbids:

- State mutation.
- Execution by the authorization guard.
- Authority promotion.
- Architecture changes.
- Self-approval.

The existing `architecture/freeze_guard.py` denies mutation of an already-approved architecture gate.

The current backend CI workflow has guarded transitions for backend activation, B1 completion, B2 dependency correction and B3 completion, alongside existing specific AI-001 and CORE-008 transitions. It does not contain a guarded ARCH-037 physical-schema amendment transition.

Therefore:

- This proposal does not claim T18 approval.
- T18 must not be weakened to authorize architecture mutation.
- `state.json` must not be manually edited.
- ARCH-037 must not be marked amended or re-approved from this document.
- No SQL migration may be treated as approved using this document alone.
- Any required amendment must use a single canonical Control Center-owned approval path, with authenticated owner approval, bounded change scope, impact analysis, evidence and remote readback.
- No parallel approval engine or duplicate architecture authority may be created.

The owner's direction on 19 November 2026 is to proceed with the safest reconstruction approach. That instruction is not represented as a completed cryptographic Control Center approval or an already-approved schema amendment.

## 12. B4 exit conditions

B4 must remain CURRENT until all eight B4 acceptance criteria have real evidence:

1. Only the approved ARCH-037 schema and canonical owners are used.
2. Migrations have deterministic ordering and integrity checks.
3. Tenant access is enforced at the target persistence boundary.
4. Repositories and transaction boundaries have explicit write ownership.
5. Durable session and revocation storage is supported.
6. Shared rate-limit state and minimized audit persistence are supported.
7. Migration, concurrency, backup and recovery tests pass.
8. No second schema or persistence authority is introduced.

Backend gate-level AC01–AC10 must not be marked complete merely because B4 is complete.

Production readiness must not be claimed from a green development CI run alone.

---

## Final review result

**ARCH-037 approval exists. The accessible physical schema specification does not.**

The current codebase provides substantial domain-owner contracts, but identifier/tenant compatibility and physical persistence decisions must be resolved before safe DDL can be frozen.

This document establishes the reconstruction evidence and implementation boundaries. It is deliberately non-executable until the required architecture approval and schema freeze evidence exist.

**Document status: DRAFT — NOT APPROVED — NON-EXECUTABLE.**
