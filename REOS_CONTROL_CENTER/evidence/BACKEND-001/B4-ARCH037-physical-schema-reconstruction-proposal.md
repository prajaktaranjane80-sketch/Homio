# HOMIO / REOS — B4 Physical Persistence Schema Reconstruction and Approval Package

**Document type:** Source-backed physical-schema catalogue and architecture-change review  
**Status:** DRAFT — NOT APPROVED — NON-EXECUTABLE  
**Gate:** BACKEND-001 / BACKEND-001-B4  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Baseline HEAD:** `9a58dc5c4d4ea3acd47ae8b33b6e7801d9b44ae0`  
**Canonical state SHA:** `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b`  
**Backend master SHA:** `f8d9cd456568cc6c8eaae0caf764123a7e859ba6`  
**Master architecture SHA:** `a4749f37afa0f4d5f9de65802bb4c99d3fce9f52`  
**Review date:** 19 November 2026

---

## 1. Purpose and decision boundary

This package reconstructs a physical-persistence catalogue from the current canonical CORE owner models and approved database technology decisions.

Its purpose is to make PostgreSQL implementation specific, testable and traceable without creating a competing business-data model.

This document does **not** approve new physical SQL, alter frozen ARCH-037 v1.0, change `state.json`, or authorize production migrations. Every relation name and physical mapping below is a candidate for owner review until the approved schema manifest is formally established.

The source hierarchy is:

1. `REOS_CONTROL_CENTER/data/state.json` — sole task and approval-state authority.
2. Approved ARCH-037 and ARCH-038 records — architecture authority.
3. Existing CORE-001 through CORE-008 source models — domain field and ownership authority.
4. Existing B4 master — implementation sequence and acceptance authority.
5. This document — reconstruction evidence only.

No table may be created merely because it appears in this proposal.

## 2. Live findings

### 2.1 Approved architecture decisions

ARCH-037 is APPROVED and frozen. T01–T11 and AC01–AC11 are recorded complete.

The archived approval events say that the approved design covered:

- Canonical entity inventory and source-of-truth ownership.
- Keys, relationships, cardinality and referential integrity.
- Tenant isolation and authorization context.
- Indexes, uniqueness, nullability and financial constraints.
- Immutable domain events, audit separation and transactional outbox.
- Retention, legal hold, backup, recovery and point-in-time recovery.
- Immutable versioned migrations, ordering, checksums and destructive-change control.
- Normalization, duplication, security, privacy and performance review.

The live approval records do not contain the column-level table catalogue, exact SQL types, physical key definitions, RLS DDL or approved migration manifest.

### 2.2 Repository and history findings

The live repository tree contains no canonical PostgreSQL business schema, approved ERD, SQL migration directory or physical table catalogue.

The `reos-development` history available for this repository begins on 25 August 2026. ARCH-037's recorded approval date is 15 August 2026. The accessible branch history therefore does not recover the original approval artifact.

The user's accessible Library search also found backend audit/reference files, but no original ARCH-037 SQL or table catalogue.

The existing backend has one Fastify application, security ports and the authenticated private Python runtime. It does not yet contain a PostgreSQL adapter, Redis adapter, PostgreSQL driver dependency or approved database migrations.

### 2.3 Current execution and CI

- B4 remains CURRENT.
- B4 acceptance criteria remain pending.
- Backend gate AC01–AC10 remain pending.
- Latest Actions run #861 passed on the baseline SHA above.
- The latest run verifies the current backend and ACRL regression suites; it does not verify PostgreSQL integration.
- Production release readiness is still false with 18 separately reported Section 14 blockers. Those blockers must not be silently mixed into B4 or marked resolved by a database change.

## 3. Source-backed table catalogue — candidate relations

All relation names below are **provisional**. Source fields are preserved; candidate SQL types are shown only where their representation is clear. Unknown or polymorphic references are deliberately not given invented foreign keys.

### 3.1 CORE-001 — Identity, tenant and membership

| Candidate relation | Canonical source model | Candidate primary key | Persistence notes |
|---|---|---|---|
| `core001_identities` | `Identity` | `identity_id UUID` | Identity type, display name, canonical handle, status, privacy class, revision and timestamps |
| `core001_identity_accounts` | `IdentityAccount` | `account_id UUID` | Identity FK, account status, monotonic authentication epoch and timestamps |
| `core001_external_identity_references` | `ExternalIdentityReference` | `reference_id UUID` | Identity FK, provider, case-sensitive subject, status, revision and linked timestamp |
| `core001_tenants` | `Tenant` | `tenant_id UUID` | Tenant kind, operating mode, status, isolation and residency modes, region, jurisdiction, quota profile, owner/admin identity references, configuration/security references and revision |
| `core001_tenant_provisioning_intents` | `TenantProvisioningIntent` | `intent_id UUID` | Tenant FK, idempotency key, provisioning state, revision and timestamps |
| `core001_organizations` | `Organization` | `organization_id UUID` | Tenant FK, parent organization, status, slug and revision |
| `core001_permissions` | `Permission` | `permission_id UUID` | Platform/authorization vocabulary; resource, action, capability, sensitivity and assurance |
| `core001_scopes` | `Scope` | `scope_id UUID` | Tenant and optional organization; resource type and resource IDs are typed references |
| `core001_relationships` | `Relationship` | `relationship_id UUID` | Tenant and subject identity; target type and target ID remain polymorphic |
| `core001_entitlements` | `Entitlement` | `entitlement_id UUID` | Optional tenant for platform scope; permission/scope links and typed policy requirements |
| `core001_roles` | `Role` | `role_id UUID` | Optional tenant and organization; permission, entitlement and scope relationships |
| `core001_memberships` | `Membership` | `membership_id UUID` | Tenant, organization and identity; status, validity, revision and invitation/join timestamps |

Candidate normalized relationship tables:

- `core001_role_permissions`
- `core001_role_entitlements`
- `core001_role_scopes`
- `core001_entitlement_permissions`
- `core001_entitlement_scopes`
- `core001_membership_roles`
- `core001_membership_entitlements`
- `core001_membership_scopes`
- `core001_membership_relationships`

The relationship tables must carry enough tenant context to enforce same-tenant references where the source owner defines tenant ownership.

`AttributeConstraint` and `RelationshipRequirement` are immutable nested value objects, not independent business owners. Their representation must be frozen as a reviewed schema choice: normalized child relations if database-level querying/integrity is required, otherwise validated JSONB value objects. They must not become an untyped policy engine.

`Scope.resource_ids` are typed UUID references with a resource type. They must not receive a universal foreign key because the target resource owner is polymorphic.

Candidate constraints and indexes:

- Unique normalized identity handle.
- Unique external identity `(provider_normalized, subject)`; provider normalization is case-insensitive while subject remains case-sensitive.
- Unique tenant slug.
- Tenant-scoped organization slug uniqueness.
- Tenant-consistent organization parent relationship.
- Positive revision and authentication-epoch checks.
- Validity ranges must reject `valid_until < valid_from`.
- Role and entitlement keys must respect global versus tenant scope.
- A membership uniqueness rule must be verified against the existing CORE-001 registry before freezing it; do not assume multiple membership semantics.

**Security restriction:** credentials, password hashes, bearer tokens, refresh tokens, secrets, private keys and session tokens are explicitly forbidden from Identity and IdentityAccount persistence.

### 3.2 CORE-002 — Event envelope and transactional outbox

| Candidate relation | Canonical source model | Candidate primary key | Persistence notes |
|---|---|---|---|
| `core002_event_envelopes` | `EventEnvelope` | `event_id UUID` | Event/schema versions, tenant, producer, correlation/causation, occurred/observed timestamps, payload, trace context, ordering metadata and idempotency key |
| `core002_outbox_publications` | `OutboxContract` | `publication_id UUID` | Event FK, tenant, event fingerprint, creation timestamp and publication state |

`payload` and `metadata` may use JSONB after the existing CORE-002 event contract validates them. JSONB must not bypass event schema/version validation.

The aggregate owner remains responsible for its transaction. The outbox record must be inserted in that same PostgreSQL transaction. A publisher must never observe an uncommitted event.

Delivery attempts, retry queues and dead-letter persistence may only be added where an existing CORE-002 record contract defines their identity and lifecycle. Do not invent a second event registry or duplicate Kafka ownership.

Required constraints:

- Event and publication identity uniqueness.
- Positive schema and event versions.
- Tenant/correlation/causation consistency.
- Idempotency uniqueness according to the approved producer and tenant scope.
- Immutable event history after publication.

### 3.3 CORE-003 — Lead attribution and ownership protection

| Candidate relation | Canonical source model | Candidate primary key | Persistence notes |
|---|---|---|---|
| `core003_leads` | `Lead` | `lead_id UUID` | Tenant, customer reference UUID, lifecycle state, priority, source, metadata, revision and timestamps |
| `core003_lead_attributions` | `LeadAttribution` | Candidate composite key | Lead and tenant, source type/reference, attribution time, evidence and campaign references |
| `core003_lead_ownership` | `LeadOwnership` | Candidate composite key | Lead, tenant, owner identity, role, assignment time, revision and assignment reference |
| `core003_ownership_transfers` | `OwnershipTransfer` | `transfer_id UUID` | Immutable previous/new owner, previous/new revision, reason and transfer time |

The physical design must preserve ownership history and prevent an ownership transfer from silently overwriting prior owner evidence.

`Lead.customer_id` is UUID in CORE-003. It is not permission to create a new Customer table or lifecycle inside B4.

Candidate indexes include tenant/status/created-time lead retrieval and tenant/owner assignment retrieval. Exact uniqueness must be reconciled with the existing CORE-003 registry and transfer rules.

### 3.4 CORE-004 — Project, inventory hierarchy and provenance

| Candidate relation | Canonical source model | Candidate key | Persistence notes |
|---|---|---|---|
| `core004_projects` | `ProjectIdentity` / `Project` | `(tenant_id, project_id)` | Project ID, developer ID, project code, name and metadata |
| `core004_inventory` | `InventoryIdentity` / `Inventory` | `(tenant_id, inventory_id)` | Type, developer, project/property/unit hierarchy, name, lifecycle, availability, timestamps, version and metadata |
| `core004_inventory_relationships` | `InventoryRelationship` | `(tenant_id, relationship_id)` | Typed parent/child node references and relationship version |
| `core004_inventory_lifecycle_history` | `InventoryLifecycleHistory` | `(tenant_id, transition_id)` | Immutable lifecycle transition, old/new state and version, actor and reason |
| `core004_inventory_availability_history` | `AvailabilityTransition` | `(tenant_id, transition_id)` | Immutable old/new availability state/version and reservation/allocation references |
| `core004_inventory_sources` | `InventorySource` | `(tenant_id, source_id)` | Source type/reference, developer reference, acquisition/channel references and metadata |
| `core004_inventory_provenance` | `InventoryProvenance` | Candidate composite key | Inventory, tenant, source and provenance version |
| `core004_provenance_evidence` | `ProvenanceEvidenceReference` | Candidate composite key | Evidence reference, type, fingerprint, source and recorded time |
| `core004_provenance_history` | `ProvenanceHistoryEntry` | Candidate composite key | Inventory, tenant, version, fingerprint, time and change reference |

The canonical project identity includes `tenant_id + project_code`. Project identifiers remain opaque strings.

Inventory identity includes the hierarchy path: tenant, inventory type, project, property, unit and inventory. The physical key and partial uniqueness rules must preserve DEVELOPMENT/PROPERTY/UNIT distinctions.

**Do not create a foreign key on `unit_id` alone.** The current owner model does not establish that it is a globally unique target. A unit reference must include the verified project/property hierarchy.

`developer_id` and `builder_developer_id` are references. They do not create a Builder lifecycle or source of truth.

### 3.5 CORE-005 — Search and matching

CORE-005 search requests, matching, ranking, visibility and retrieval remain derived/read-side responsibilities.

PostgreSQL/PostGIS structured search and Qdrant vector/hybrid retrieval must preserve tenant filters and source provenance. Qdrant vectors and search projections must be rebuildable from canonical owners.

B4 must not create a competing project/inventory index authority. Search projection persistence belongs to its approved integration contract and must not be confused with canonical inventory persistence.

### 3.6 CORE-006 — Deal and transaction lifecycle

| Candidate relation | Canonical source model | Candidate key | Persistence notes |
|---|---|---|---|
| `core006_deals` | `Deal` | `(tenant_id, deal_id)` candidate | Deal status/version, canonical party/project references, timestamps and contract version |
| `core006_deal_history` | `DealHistoryEntry` | `(tenant_id, deal_id, version)` | Immutable ordered lifecycle history |
| `core006_deal_parties` | `DealPartyRelationship` | Candidate composite key | Polymorphic role and party reference, relationship version/lifecycle and metadata |
| `core006_deal_offers` | `DealOffer` | `(tenant_id, offer_id)` candidate | Status/version, terms, timestamps and superseded offer reference |
| `core006_deal_negotiations` | `DealNegotiation` | `(tenant_id, negotiation_id)` candidate | Active offer and historical offer references |
| `core006_deal_milestones` | `DealTransactionMilestone` | `(tenant_id, milestone_id)` candidate | Ordered transition, deal version, occurrence time and evidence-required flag |
| `core006_deal_ownership_bindings` | `DealOwnershipBinding` | `(tenant_id, binding_id)` candidate | Lead/ownership record/owner references and ARCH-011 authority version |
| `core006_deal_evidence_references` | `DealEvidenceReference` | `(tenant_id, evidence_id)` candidate | References ARCH-014-owned evidence; does not duplicate evidence ownership |
| `core006_deal_audit_entries` | `DealAuditEntry` | `(tenant_id, audit_id)` candidate | Deal-specific lifecycle audit; separate from API security and financial audit |

Deal party roles include BUYER, CUSTOMER, SELLER, BUILDER, BROKER and REPRESENTATIVE. `party_id` is polymorphic and must not have one universal FK to Identity.

`Deal.customer_id`, `broker_id`, `builder_id`, `project_id` and `unit_id` remain source-compatible strings at the domain boundary. Their foreign-key eligibility must be decided by verified owner mapping, not by matching field names.

`DealEvidenceReference` points to ARCH-014. B4 must not create a second evidence store.

CORE-006 owns transaction lifecycle. Commission calculation, allocation, invoice and settlement remain CORE-008.

### 3.7 CORE-007 — Trust, fraud, risk and governance

Candidate relation families:

| Candidate relation | Canonical source model | Important ownership rule |
|---|---|---|
| `core007_trust_signals` | `TrustSignal` | Preserve tenant/subject, signal version, source/evidence provenance and confidence |
| `core007_trust_scores` | `TrustScore` | Preserve model version/fingerprint, contributions and trust version |
| `core007_fraud_findings` | `FraudFinding` | UUID identity and tenant; immutable detection/evidence state |
| `core007_fraud_assessments` | `FraudAssessment` | Assessment version, findings, policy fingerprint and tripwire result |
| `core007_risk_assessments` | `RiskAssessment` | Risk score/level, versioned factors, evaluation trace and input fingerprints |
| `core007_governance_evaluations` | `GovernanceEvaluation` | Policy, rule provenance, disposition, fingerprints and review state |
| `core007_governance_decisions` | `GovernanceDecision` | Decision type, action class, authority, reasons, evidence references and fingerprint |
| `core007_approval_requests` | `ApprovalRequest` | Requested/expiry times, approval state and governance fingerprint |
| `core007_approval_records` | `ApprovalRecord` | Decision time, actor reference, reason and fingerprint |
| `core007_escalation_hooks` | `EscalationHook` | Tenant-scoped escalation state and evidence references |
| `core007_governance_evidence_links` | `EvidenceLink` | ARCH-014 evidence references and provenance; never a second evidence owner |

`subject_id` and target references remain polymorphic where the source model defines them as such. Do not attach generic FKs to a guessed domain table.

Tuples of rule IDs, evidence references, source references and evaluation traces may be normalized or retained as validated JSONB according to access patterns and immutable-history requirements. This is a schema decision requiring review, not an automatic JSONB shortcut.

### 3.8 CORE-008 — Commission and financial records

| Candidate relation | Canonical source model | Candidate key | Persistence notes |
|---|---|---|---|
| `core008_financial_domain_records` | `FinancialDomainRecord` / `FinancialIdentity` | `(tenant_id, financial_id)` | Typed subject reference, state, optional amount and metadata |
| `core008_commission_contracts` | `CommissionContract` | `(tenant_id, commission_id, contract_version)` candidate | Entitlement, basis, rate, eligibility rules, effective interval, provenance and state |
| `core008_commission_calculations` | `CommissionCalculation` | `(tenant_id, calculation_id, calculation_version)` candidate | Basis/source/formula, exact amounts, eligibility/provenance, idempotency key and state |
| `core008_calculation_bases` | `CommissionCalculationBasis` | Candidate composite key | Source version, captured time, amount, basis code and attributes |
| `core008_commission_entitlements` | `CommissionEntitlement` | Candidate composite key | Contract/calculation versions, entitled party/amount, eligibility and authorization references |
| `core008_commission_allocations` | `CommissionAllocation` | `(tenant_id, allocation_set_id)` candidate | Total amount, linked calculation and allocation fingerprint |
| `core008_commission_allocation_lines` | `CommissionAllocationLine` | `(allocation_set_id, rank)` candidate | Party, entitlement, amount and exact ratio |
| `core008_participant_splits` | `CommissionParticipantSplit` | Candidate composite key | Deal/lead/ownership/version/fingerprint bindings and exact amount split |
| `core008_commission_invoices` | `CommissionInvoice` | `(tenant_id, invoice_id, invoice_version)` candidate | Issuer/payer/payee references, currency, totals, due/issue time, external ref and provenance |
| `core008_invoice_lines` | `CommissionInvoiceLine` | `(invoice_id, line_id)` candidate | Typed line, amount, sequence and metadata |
| `core008_commission_settlements` | `CommissionSettlement` | `(tenant_id, settlement_id, settlement_version)` candidate | Mode, amount, beneficiary, external reference, authorization and state |
| `core008_external_settlement_evidence` | `CommissionExternalSettlementEvidence` | Candidate composite key | External/provider reference, observed amount/time and source version |
| `core008_reconciliations` | `CommissionReconciliation` | `(tenant_id, reconciliation_id, reconciliation_version)` candidate | Expected/observed/variance amounts, external evidence and reconciliation provenance |
| `core008_commission_adjustments` | `CommissionAdjustment` | `(tenant_id, adjustment_id, adjustment_version)` candidate | Dispute/settlement/reconciliation references, reason, authorization and amount |
| `core008_commission_disputes` | `CommissionDispute` | `(tenant_id, dispute_id, dispute_version)` candidate | Claimant, disputed amount, evidence, resolution and authorization references |
| `core008_commission_releases` | `CommissionRelease` | `(tenant_id, release_id, release_version)` candidate | Statement, invoice/settlement/reconciliation/tax references, checks and release state |
| `core008_commission_statements` | `CommissionStatement` | `(tenant_id, statement_id, statement_version)` candidate | Gross, adjustment, invoice, settlement, reconciliation, tax, withholding and outstanding totals |
| `core008_tax_assessments` | `CommissionTaxAssessment` | `(tenant_id, assessment_id, assessment_version)` candidate | Taxable base, tax/withholding components, net effect and authority references |
| `core008_tax_components` | `CommissionTaxComponent` | `(assessment_id, component_id)` candidate | Exact rate, base/amount, jurisdiction and rule version |
| `core008_commission_closeouts` | `CommissionCloseout` | `(tenant_id, closeout_id, closeout_version)` candidate | Statement, outstanding/variance references, authorization and closeout state |
| `core008_financial_audit_records` | `CommissionFinancialAuditRecord` | `(tenant_id, commission_id, sequence)` candidate | Append-only audit entry, previous and current fingerprints |
| `core008_financial_idempotency` | `FinancialIdempotencyRecord` | `(tenant_id, operation, idempotency_key)` candidate | Command fingerprint, first-seen time and metadata |
| `core008_allocation_snapshots` | `CommissionAllocationSnapshot` | `(tenant_id, allocation_set_id)` candidate | Canonical payload and immutable snapshot fingerprint |
| `core008_calculation_history` | `CommissionCalculationHistoryEntry` | Candidate composite key | Calculation ID/version/fingerprint |
| `core008_invoice_history` | `CommissionInvoiceHistoryEntry` | Candidate composite key | Invoice ID/version/state/amount/fingerprint |
| `core008_settlement_history` | `CommissionSettlementHistoryEntry` | Candidate composite key | Settlement ID/version/state/fingerprint |
| `core008_reconciliation_history` | `CommissionReconciliationHistoryEntry` | Candidate composite key | Reconciliation version/state/variance/fingerprint |
| `core008_dispute_history` | `CommissionDisputeHistoryEntry` | Candidate composite key | Dispute version/state/resolution/fingerprint |
| `core008_release_history` | `CommissionReleaseHistoryEntry` | Candidate composite key | Release version/state/fingerprint |
| `core008_tax_history` | `CommissionTaxHistoryEntry` | Candidate composite key | Assessment version/tax/withholding/fingerprint |
| `core008_closeout_history` | `CommissionCloseoutHistoryEntry` | Candidate composite key | Closeout version/state/fingerprint |

History rows and snapshots must retain the source owner’s version and fingerprint semantics. They must not be silently collapsed into a mutable current row.

`LedgerAccountReference` is an opaque ledger-authority reference. CORE-008's immutable ledger-entry model does not create a new chart-of-accounts authority or independently certify account balances. No B4 table may invent an external general-ledger owner.

#### Financial numeric and currency rule

**SOURCE FACT**

- `Currency.minor_unit` is an integer from 0 through 6.
- `Currency.rounding_mode` is one of the explicit CORE-008 rounding modes.
- `MonetaryAmount` uses Python `Decimal`.
- Binary floating-point monetary inputs are rejected.
- Monetary values are quantized to the currency quantum.
- The current domain model does not define one maximum integral magnitude or one universal SQL precision for all financial concepts.

**CANDIDATE DECISION**

Use PostgreSQL exact `NUMERIC` values without imposing an arbitrary universal `(precision, scale)` at this stage. Persist the currency code and the minor-unit/rounding semantics required to reproduce the value at the record's version.

Before freeze, each monetary field must be classified as one of:

- Currency-bound `MonetaryAmount`.
- Non-currency Decimal rate.
- Non-currency Decimal ratio.
- Integer minor units where the owning contract explicitly chooses them.

The database checks must reject values that violate the associated minor-unit rule. The exact field-level constraint strategy must be approved before SQL is frozen.

Do not use `DOUBLE PRECISION` or JavaScript floating-point arithmetic as the financial source of truth.

## 4. Cross-owner relationship decisions

| Relationship | Candidate treatment | Current restriction |
|---|---|---|
| IdentityAccount → Identity | UUID FK | Same CORE-001 owner |
| ExternalIdentityReference → Identity | UUID FK | Same CORE-001 owner |
| Organization → Tenant | UUID FK | Same CORE-001 owner |
| Membership → Tenant/Organization/Identity | Tenant-consistent composite FKs | Same CORE-001 owner |
| Role/Entitlement → Permission/Scope | Join-table FKs | Verify global versus tenant scope |
| LeadAttribution → Lead | UUID FK | Same CORE-003 owner |
| LeadOwnership → Lead | Tenant-scoped UUID FK | Same CORE-003 owner |
| Inventory → Project | Composite tenant/project FK | Same CORE-004 owner |
| Deal → Project | Candidate composite FK | Requires confirmed string-key uniqueness and tenant mapping |
| Deal → Unit | No direct unit-only FK | Full hierarchy key is required |
| Deal → Customer | No FK | Customer lifecycle owner is future architecture |
| Deal → Builder | No FK | Builder lifecycle owner is future architecture |
| Deal Party → Identity | No universal FK | Party ID is polymorphic |
| Financial Subject → Domain record | No generic FK | Subject type is polymorphic |
| Financial ledger account reference → account | No B4-created account table | Ledger account owner is not defined by this record |
| Deal evidence → ARCH-014 | Evidence reference only | ARCH-014 remains evidence owner |
| API audit → financial audit | No FK | Separate audit owners |
| API audit → ARCH-014 evidence | No FK | Separate audit/evidence semantics |
| Outbox publication → EventEnvelope | UUID FK | Same CORE-002 owner |

All tenant-bound FKs must include tenant identity where the owning model supports it. A cross-tenant FK must be impossible, not merely discouraged by application code.

## 5. Identifier and tenant compatibility — unresolved freeze conditions

The current model type mismatch is real:

- CORE-001, CORE-002 and CORE-003 use UUID tenant and entity identifiers.
- CORE-004 uses string tenant/project/inventory identifiers.
- CORE-006 uses string tenant/deal/party references.
- CORE-008 uses string tenant/financial identifiers.
- CORE-003 `Lead.customer_id` is UUID while CORE-006 `Deal.customer_id` is string.

No physical DDL may silently choose one type for all domains.

Required owner decisions:

1. Confirm whether CORE-004/006/008 tenant strings are always canonical serialized CORE-001 UUIDs in production.
2. Confirm the compatibility parser and canonical serialization used by TypeScript/Python repositories.
3. Determine which string identifiers are opaque IDs and which are references to UUID-owned objects.
4. Define whether cross-owner FKs can be enforced for each reference.
5. Reject malformed or ambiguous tenant identifiers. Never auto-convert, generate or repair a tenant ID.
6. Prove that tenant aliases or legacy identifiers do not exist before migration.

The persistence adapter must not weaken the source owner's own identifier validation.

## 6. Tenant RLS and database privilege model

The following is a candidate enforcement model for architecture review.

### 6.1 Role separation

Candidate roles:

- Schema owner role — owns the physical schema; never used by Fastify at runtime.
- Migration role — applies approved migrations only.
- Runtime role — ordinary Fastify database access; not table owner and has no `BYPASSRLS`.
- Restricted read role — only where an approved reporting use case exists.

No service must connect with a superuser or schema-owner credential.

### 6.2 Transaction-local tenant context

The final schema must use one reviewed transaction-local tenant-context contract.

The current owner models establish a trusted tenant UUID in CORE-001. The physical persistence mapping for string-based owners remains a blocker until the identifier contract is approved.

Candidate request sequence:

1. Verify credentials and trusted context through existing security owners.
2. Acquire one PostgreSQL client from the canonical pool.
3. Begin a transaction.
4. Establish the tenant context transaction-locally with parameterized `set_config`.
5. Perform the repository operation using the same client.
6. Commit or roll back.
7. Release the client only after transaction completion.

Do not use session-level tenant variables on pooled connections. Do not run pieces of a transaction through `pool.query`.

### 6.3 Required RLS policies

For every tenant-scoped relation, review:

- RLS enabled.
- Whether FORCE ROW LEVEL SECURITY is required.
- Tenant-read policy.
- Tenant-insert policy.
- Tenant-update policy with both old-row and new-row checks.
- Tenant-delete policy where deletion is permitted at all.
- Fail-closed behavior when context is absent.
- Cross-tenant foreign-key enforcement.
- Administrative access and audit requirements.

The application runtime role must not bypass RLS.

Real PostgreSQL tests must execute under the same non-owner role as the application. Mock-only tenant tests are insufficient.

## 7. Durable security persistence and ordering dependency

### 7.1 Existing API security contract

The existing `SessionValidationPort` receives a verified principal containing issuer, subject, audiences, client ID and token ID (`jti`).

The principal does not currently contain:

- Canonical account ID.
- Authentication epoch.
- Verified issued-at timestamp.
- Verified expiry timestamp.

CORE-001 `IdentityAccount` owns account status and `authentication_epoch`. Credentials and sessions are explicitly outside the identity model.

### 7.2 Existing B3 boundary

B3 protocol v1 returns minimized OIDC claims and existing CORE-001 identity/tenant/membership results. It does not return the canonical account ID and current authentication epoch through the external identity-resolution operation.

The current API flow validates session before the trusted-context resolver runs.

Therefore, a simple `jti` denylist is not enough to prove the approved account-epoch revocation guarantee.

### 7.3 B4 blocking decision

Before creating a production session/revocation schema, the owner-controlled contract must define:

1. How a verified OIDC principal is bound to a canonical CORE-001 account.
2. How current account status and authentication epoch are resolved.
3. How token issuance and expiry claims are made available to the trusted backend.
4. How session establishment, revocation, logout and epoch rotation are persisted.
5. How unknown, expired, disabled, suspended and revoked states fail closed.
6. How an outage or ambiguous response is handled without creating an authentication bypass.
7. How idempotent revocation and concurrent requests behave.

Do not persist raw bearer tokens.

Do not invent a session-creation API in B4. Do not change B3 protocol v1 or enable protected production routes as a shortcut. Any required B3 compatibility change must go through the existing owner/guard boundary.

## 8. Redis rate-limit persistence

The existing `RateLimitPort` has two buckets: `api-ip` and `api-identity-tenant`.

The adapter must use shared Redis 8 state, not per-process memory.

The implementation design must specify:

- Atomic counter/window behavior.
- Expiry and retry-after calculation.
- Concurrent request handling across multiple backend instances.
- HMAC-derived pseudonymous keys where identity/IP material is used.
- Secret storage and rotation.
- Threshold and window policy supplied by the security owner.
- Redis outage and recovery behavior.
- No hidden local-memory fallback in production.

The current port does not supply approved thresholds. The storage adapter must not invent production rate-limit policy.

## 9. API security audit persistence

The existing `SecurityAuditPort` is intentionally minimized.

The physical design must preserve only its approved fields:

- Event type.
- Request ID.
- Occurred-at timestamp.
- Reason code.
- Operation.
- Optional actor identity ID.
- Optional tenant ID.

It must exclude credentials, authorization headers, bearer tokens, passwords, secrets, request bodies and unnecessary personal data.

The API audit store must remain separate from:

- CORE-008 commission/financial audit.
- CORE-006 deal lifecycle audit.
- ARCH-014 business evidence.
- ACRL continuity/checkpoint records.

The existing protected-request flow fails closed when its audit port is unavailable. PostgreSQL tests must prove that behavior.

## 10. Migration, checksum and recovery design

After physical schema approval, the candidate migration system must preserve these invariants:

- Immutable versioned SQL files.
- Stable lexicographic or explicit dependency ordering.
- SHA-256 checksum per migration.
- A single migration lock preventing concurrent migration runners.
- Applied migration identity and checksum recorded transactionally.
- Duplicate migration rejection.
- Out-of-order dependency rejection.
- Modified historical migration rejection.
- Fail-closed behavior when checksums differ.
- Explicit transaction and non-transactional migration handling.
- Expand-migrate-contract compatibility.
- Explicit destructive-change approval.
- Restore and post-restore integrity verification.
- Exact schema fingerprint in migration evidence.

A prior migration must never be edited in place. A correction must be a new migration.

The migration ledger relation and its exact columns must be approved in the physical schema manifest before implementation.

## 11. Required physical-schema test evidence

| Area | Required real-service evidence |
|---|---|
| Schema fingerprint | Exact expected tables, columns, constraints, indexes and RLS policies |
| Fresh install | Empty PostgreSQL 18.4+ database migrates deterministically |
| Upgrade | Previous approved schema upgrades in dependency order |
| Checksum | Historical SQL alteration is rejected |
| Migration concurrency | Two migration runners cannot race |
| Interrupted migration | Recovery leaves a valid, verifiable state |
| Tenant isolation | Read/write/update/delete cross-tenant negative tests |
| Pool safety | Tenant context cannot leak between reused connections |
| FK integrity | Invalid owner references and cross-tenant links are rejected |
| Domain ownership | No duplicate aggregate/write owner |
| Decimal safety | Decimal round-trip, currency mismatch, minor-unit and rounding rules |
| Ledger integrity | Append-only behavior, fingerprint verification, reversal/adjustment history |
| Outbox | Aggregate and event publication record commit atomically |
| Session | Revocation, account status and authentication-epoch invalidation |
| Redis | Shared counters, expiry, concurrent clients, outage/recovery |
| Security audit | PII minimization, tamper control and fail-closed behavior |
| Backup | Backup verification, restore and point-in-time recovery on target PostgreSQL |
| Reproducibility | Exact `npm ci`, build and integration suites |

The CI evidence must include the exact source SHA and actual PostgreSQL/Redis service versions. A unit test or mocked database must not be reported as target-service proof.

## 12. Required implementation sequence

This sequence stays within BACKEND-001-B4:

1. Complete source/fixture compatibility audit for CORE-001 through CORE-008.
2. Resolve tenant and cross-domain identifier mappings.
3. Freeze the table catalogue, keys, FKs, checks, unique constraints and indexes.
4. Freeze all tenant RLS policies and database-role privileges.
5. Freeze financial numeric semantics and version/history behavior.
6. Resolve the B2 session/account-epoch/B3 protocol dependency before designing durable session storage.
7. Obtain a formal owner-approved ARCH-037 amendment/addendum where the physical catalogue differs from the frozen approval.
8. Add the approved schema fingerprint and immutable migration manifest.
9. Implement the existing Fastify backend's node-postgres infrastructure and transaction boundaries.
10. Implement migrations and real PostgreSQL integration tests.
11. Implement tenant RLS, repositories, event outbox and audit persistence.
12. Implement the session/revocation persistence contract after its owner decision.
13. Implement shared Redis rate-limit storage.
14. Run concurrency, negative tenant, backup, restore and PITR evidence.
15. Re-run Actions at the exact source SHA and reconcile every B4 acceptance criterion.
16. Request the guarded Control Center B4 transition only after all criteria have evidence.

B3 remains read-only until B4 establishes an approved durable transaction/idempotency owner. B2 production binding remains after B4.

## 13. Architecture-change governance gap

The live state contains two approved change requests:

- `CR-BACKEND-001` — backend workstream activation.
- `CR-BACKEND-001-B2-DEPENDENCY` — B2 dependency correction.

The existing Control Center CLI exposes task/gate validation and approval commands, but no generic architecture-amendment request/approval command.

T18 is an authorization-only guard. It cannot mutate `state.json`, the repository or approved architecture. The freeze guard prevents direct mutation of an APPROVED architecture node.

Therefore, none of the following is acceptable:

- Directly editing `state.json`.
- Overwriting the frozen ARCH-037 v1.0 record.
- Reusing the B1/B2/B3 transition for an unrelated architecture amendment.
- Relaxing T18 or the freeze guard.
- Creating a second approval engine.
- Treating a DRAFT evidence document as owner approval.

The required governance path is to extend the existing canonical Control Center mutation boundary with a narrowly scoped, guarded ARCH-037 addendum request/approval path. It must preserve ARCH-037 v1.0 as immutable history, use T17 impact analysis and T18 authorization, bind owner approval to the exact request fingerprint and source SHA, and record the approved addendum through an external guarded executor with remote readback.

**This governance path does not currently exist in the live repository.** It is a prerequisite to freezing a reconstructed schema that changes or fills decisions not represented in the accessible ARCH-037 approval artifact.

The current document does not claim that this new governance path has been implemented or approved.

## 14. Current result

| Item | Verified status |
|---|---|
| ARCH-037 v1.0 | APPROVED and frozen |
| ARCH-038 v1.0 | APPROVED |
| CORE owner models | Existing source-of-truth boundaries identified |
| Physical table catalogue | Reconstruction draft only |
| Canonical approved SQL/ERD | Not located |
| PostgreSQL adapter | Not implemented |
| PostgreSQL migrations | Not implemented |
| Tenant RLS | Not implemented or tested against target DB |
| Durable session/revocation | Contract dependency unresolved |
| Redis rate-limit adapter | Not implemented |
| API security audit adapter | Not implemented |
| Backup/restore/PITR | No B4 target-service evidence |
| B4 acceptance criteria | Pending |
| Backend gate AC01–AC10 | Pending |
| Latest backend/ACRL CI | Run #861 PASS |
| Production release readiness | Not ready; separate Section 14 blockers remain |

**No B4 completion or production-readiness claim is made.**

**Final document status: DRAFT — NOT APPROVED — NON-EXECUTABLE.**
