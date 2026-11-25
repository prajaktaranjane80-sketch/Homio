# HOMIO / REOS — B4 Physical Schema Implementation Manifest

**Project:** HOMIO / REOS  
**Repository:** prajaktaranjane80-sketch/Homio  
**Branch:** reos-development  
**Baseline commit:** c217d23e71122ccde402e10d8898fc710be7490d  
**Execution authority:** REOS_CONTROL_CENTER/data/state.json  
**Current task:** BACKEND-001-B4  
**Architecture:** ARCH-037 — Database Final Schema Design v1.0  
**Backend contract:** REOS_CONTROL_CENTER/B4 ka work plan  
**Document type:** B4 implementation traceability evidence index  
**Status:** Derived implementation mapping; not a new schema authority

---

## 1. Authority and implementation boundary

The implementation follows this order:

1. `REOS_CONTROL_CENTER/data/state.json`
2. Approved/frozen ARCH-037 and ARCH-038
3. Canonical CORE-001 through CORE-008 owner models
4. `REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure`
5. `REOS_CONTROL_CENTER/B4 ka work plan`
6. Existing PostgreSQL runtime, migration runner, migration manifest and tests

This manifest records how B4 maps canonical owner fields into the physical PostgreSQL representation. It does not create a second domain model or authorize new business entities.

The B4 implementation reuses:

- One existing `PostgresRuntime`
- One existing migration manifest
- One existing migration runner
- One existing production PostgreSQL client composition
- One existing tenant transaction boundary
- One existing Redis rate-limit owner
- One existing API security audit store

No ORM, new database client, second migration runner, duplicate tenant registry, duplicate domain engine or parallel persistence layer is introduced.

## 2. Source baseline and readback identifiers

Implementation baseline:

| Source | Verified identifier |
|---|---|
| GitHub HEAD | `c217d23e71122ccde402e10d8898fc710be7490d` |
| `data/state.json` | `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b` |
| `AI_AGENT_ENTRYPOINT.py` | `2e1d66cec0a8ca17b24ccf285d3133ff16ca2834` |
| `B4 ka work plan` | `84c94c82ac5b0fde7c7bdf94acca235402c465ab` |
| ARCH-037 integration test at baseline | `ff63ab81d5c78f9c3e9c4f3e25a0fe01cf1f15ab` |

Canonical CORE source files:

| Owner | Source file | Blob SHA |
|---|---|---|
| CORE-001 Identity | `AUTONOMY_ENGINE/core/identity_tenant/identity.py` | `49564ab0e7b3f19d192c343bd444ba3b45ced192` |
| CORE-001 Tenant | `AUTONOMY_ENGINE/core/identity_tenant/tenant.py` | `5fdda5750f37ea14214ede72ff97c739526390d6` |
| CORE-001 Membership | `AUTONOMY_ENGINE/core/identity_tenant/membership.py` | `919868a77bf589795c383a1fbb974fc69dede6ec` |
| CORE-003 Lead | `AUTONOMY_ENGINE/core/lead_ownership/lead.py` | `9b092087c5e4b820b5ee320abdb4c5fc00adcbce` |
| CORE-003 Lead ownership | `AUTONOMY_ENGINE/core/lead_ownership/lead_ownership.py` | `dbb3917f6a3c2108bcb9de7c705cb0441758a7f7` |
| CORE-003 Ownership transfer | `AUTONOMY_ENGINE/core/lead_ownership/ownership_transfer.py` | `aaba13bb20c3494c3f32579ba7081cab5856a3a9` |
| CORE-004 Project | `AUTONOMY_ENGINE/core/inventory/project.py` | `bc34a9729197cf55d8d29bda943be3d8d09dd2a9` |
| CORE-004 Inventory | `AUTONOMY_ENGINE/core/inventory/inventory.py` | `be43bffd198d6c3f08c3aad641ed03696955f4e0` |
| CORE-006 Deal | `AUTONOMY_ENGINE/core/deal_transaction/deal.py` | `2fc25aaf118da6512e89d487a89f93cee9bc2da5` |
| CORE-006 Deal parties | `AUTONOMY_ENGINE/core/deal_transaction/deal_parties.py` | `74256a3f6451102c2ea298cc62db6ea8e09a521f` |
| CORE-007 Governance decision | `AUTONOMY_ENGINE/core/trust_fraud_governance/governance_decision.py` | `dcb5991c78ad10e60f489e2dda72f9248a5e4f0f` |
| CORE-007 Approval workflow | `AUTONOMY_ENGINE/core/trust_fraud_governance/approval_workflow.py` | `704e5e554b30e02ee38b4fa5b3358b7b0ea46175` |
| CORE-008 Financial domain | `AUTONOMY_ENGINE/core/commission_financial/financial_domain.py` | `4b6af8da3ec7687c05b0a9782da305d2f267b3dc` |
| CORE-008 Financial ledger | `AUTONOMY_ENGINE/core/commission_financial/financial_ledger_boundary.py` | `b3c324aff41a449392ffef1b1d143621d6151ef6` |
| CORE-008 Commission contract | `AUTONOMY_ENGINE/core/commission_financial/commission_contract.py` | `efbf22c1368b288840a68260a1fdcfa66be8c0b3` |

Existing immutable migration baseline:

| Migration | SHA-256 blob |
|---|---|
| `00000001-core002-event-outbox.sql` | `639684197d11544c1645b0c33bd5e8b824b4a008` |
| `00000002-core002-safe-tenant-context.sql` | `5b6898055f74c3f536d09edc9dd59cf8676e8bdc` |
| `00000003-b4-durable-api-sessions.sql` | `73a367292df0bdc67303a0ab61fae000aaaf2143` |
| `00000004-b4-minimized-security-audit.sql` | `28278391025782b796ef0783af6814fac6a3dbf8` |

These four files must not be edited, renumbered, deleted or replaced.

## 3. Physical representation decisions

### 3.1 Tenant identifiers

CORE-001 exposes `Tenant.tenant_id` as UUID.

CORE-004, CORE-006, CORE-007 and CORE-008 expose tenant identifiers as strings. B4's canonical PostgreSQL tenant context is UUID.

Therefore the physical tenant columns in these schemas use PostgreSQL `UUID`.

The persistence boundary must:

- Strictly parse string tenant identifiers before database use.
- Reject malformed or empty tenant identifiers.
- Never trim or repair invalid values.
- Never generate replacement tenant identifiers.
- Serialize PostgreSQL UUID values using canonical lowercase hyphenated UUID format.
- Preserve the original domain owner and its public model contract.

No second tenant registry is permitted.

### 3.2 Nested domain values

The following mappings preserve canonical nested values without creating duplicate business owners:

- CORE-001 tenant configuration/security/region references: JSONB objects.
- CORE-001 membership attribute constraints: JSONB array.
- CORE-003 lead source: flattened source fields (`source_type`, `source_id`, `campaign_id`, `channel`).
- CORE-003 lead metadata: JSONB object.
- CORE-004 metadata: JSONB object.
- CORE-006 deal history, offers, negotiation, milestones, ownership binding, evidence and audit log: validated JSONB values.
- CORE-006 participants: persisted only in `core006.deal_parties`, not duplicated in `deals`.
- CORE-007 rule IDs, reasons and evidence references: PostgreSQL text arrays.
- CORE-007 terminal `ApprovalRecord`: optional JSONB decision record on its corresponding approval request.
- CORE-008 commission entitlement, basis, rate, eligibility rules and provenance: validated JSONB values.
- CORE-008 ledger debit/credit account references and monetary currency properties: flattened into typed physical columns.

JSONB does not authorize bypassing CORE model validation. The canonical owner validates values before persistence.

### 3.3 Financial precision

`FinancialLedgerEntry.amount` contains `MonetaryAmount.amount`, whose source type is Python `Decimal`.

The physical column is unbounded PostgreSQL `NUMERIC`, without a precision/scale typmod.

The currency's code, minor unit and rounding mode are persisted separately. The database rejects non-finite numeric values and amounts that exceed the declared currency minor-unit precision.

No arbitrary `NUMERIC(18,2)` or `NUMERIC(20,6)` limit is introduced.

### 3.4 Foreign-key restrictions

Only direct, source-proven relationships receive foreign keys.

Allowed direct relationships:

- IdentityAccount → Identity
- Tenant owner/admin identity references → Identity
- Organization → Tenant
- Organization parent → Organization in the same tenant
- Membership → Tenant, Organization in the same tenant and Identity
- Lead → Tenant
- LeadOwnership and OwnershipTransfer → Lead in the same tenant
- Project → Tenant
- Inventory → Project in the same tenant
- Deal → Tenant
- DealParty → Deal in the same tenant
- GovernanceDecision and ApprovalRequest → Tenant
- CommissionContract and FinancialLedgerEntry → Tenant

No universal FK is created for:

- CORE-003 customer ID
- CORE-003 lead owner ID
- CORE-004 developer ID
- CORE-006 customer, broker, builder or polymorphic party ID
- CORE-006 unit ID alone
- CORE-007 subject ID
- CORE-008 polymorphic subject or financial account references
- CORE-008 commission IDs where a versioned contract key has not been established

No new Customer, Builder, Payment, Identity or Search entity is created.

## 4. Relation and column traceability

### 4.1 CORE-001 — `core001`

#### `core001.identities`

Canonical source: `Identity`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `identity_id` | `identity_id` | UUID | No | Primary key |
| `identity_type` | `identity_type` | TEXT | No | IdentityType enum |
| `display_name` | `display_name` | TEXT | No | 1–120 characters |
| `handle` | `handle` | TEXT | No | Canonical lowercase; unique |
| `status` | `status` | TEXT | No | Default ACTIVE; allowed ACTIVE/SUSPENDED/DEACTIVATED |
| `privacy_class` | `privacy_class` | TEXT | No | INTERNAL/CONFIDENTIAL/RESTRICTED |
| `revision` | `revision` | INTEGER | No | Default 1; positive |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Default clock timestamp |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Default clock timestamp; not before created_at |

Tenant scope: global Identity owner; source model has no tenant_id.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: unique canonical handle.

Test owner: CORE-001 source model tests and future persistence contract tests.

#### `core001.identity_accounts`

Canonical source: `IdentityAccount`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `account_id` | `account_id` | UUID | No | Primary key |
| `identity_id` | `identity_id` | UUID | No | Unique FK to identities |
| `status` | `status` | TEXT | No | ENABLED/LOCKED/DISABLED |
| `authentication_epoch` | `authentication_epoch` | BIGINT | No | Default 1; positive |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Default clock timestamp |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Default clock timestamp; not before created_at |

Tenant scope: global IdentityAccount owner; source model has no tenant_id.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Security: credentials, password hashes, secrets and bearer tokens are not persisted here.

#### `core001.tenants`

Canonical source: `Tenant`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `tenant_id` | `tenant_id` | UUID | No | Primary key |
| `tenant_kind` | `tenant_kind` | TEXT | No | TenantKind enum |
| `operating_mode` | `operating_mode` | TEXT | No | OperatingMode enum |
| `display_name` | `display_name` | TEXT | No | Required text |
| `slug` | `slug` | TEXT | No | Canonical lowercase; unique |
| `status` | `status` | TEXT | No | TenantStatus enum; default PROVISIONING |
| `isolation_profile` | `isolation_profile` | TEXT | No | Default SHARED_LOGICAL |
| `residency_mode` | `residency_mode` | TEXT | No | Default GLOBAL_ALLOWED |
| `residency_region` | `residency_region` | TEXT | Yes | Optional |
| `jurisdiction` | `jurisdiction` | TEXT | Yes | Optional |
| `quota_profile` | `quota_profile` | TEXT | No | Default `default` |
| `owner_identity_id` | `owner_identity_id` | UUID | Yes | FK to identities |
| `primary_admin_identity_id` | `primary_admin_identity_id` | UUID | Yes | FK to identities |
| `configuration_ref` | `configuration_ref` | JSONB | No | Reference object default |
| `security_profile_ref` | `security_profile_ref` | JSONB | No | Reference object default |
| `region_jurisdiction_ref` | `region_jurisdiction_ref` | JSONB | Yes | Optional reference object |
| `revision` | `revision` | INTEGER | No | Default 1; positive |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Default clock timestamp |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Default clock timestamp; not before created_at |

Tenant scope: own tenant_id; restrictive RLS required.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: unique slug.

Security checks: active tenant requires owner and primary admin identities; restricted residency requires region/jurisdiction scope; fail-closed security reference required.

#### `core001.organizations`

Canonical source: `Organization`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `organization_id` | `organization_id` | UUID | No | Primary key |
| `tenant_id` | `tenant_id` | UUID | No | FK to tenants |
| `display_name` | `display_name` | TEXT | No | Required text |
| `slug` | `slug` | TEXT | No | Canonical lowercase |
| `status` | `status` | TEXT | No | Default ACTIVE; OrganizationStatus enum |
| `parent_organization_id` | `parent_organization_id` | UUID | Yes | Same-tenant self-reference |
| `revision` | `revision` | INTEGER | No | Default 1; positive |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Default clock timestamp |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Default clock timestamp; not before created_at |

Tenant scope: tenant_id; restrictive RLS required.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: unique `(tenant_id, slug)` and `(tenant_id, organization_id)`.

#### `core001.memberships`

Canonical source: `Membership`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `membership_id` | `membership_id` | UUID | No | Primary key |
| `tenant_id` | `tenant_id` | UUID | No | FK to tenants |
| `organization_id` | `organization_id` | UUID | No | Same-tenant Organization FK |
| `identity_id` | `identity_id` | UUID | No | FK to identities |
| `status` | `status` | TEXT | No | Default INVITED; MembershipStatus enum |
| `role_ids` | `role_ids` | UUID[] | No | Default empty array |
| `entitlement_ids` | `entitlement_ids` | UUID[] | No | Default empty array |
| `scope_ids` | `scope_ids` | UUID[] | No | Default empty array |
| `relationship_ids` | `relationship_ids` | UUID[] | No | Default empty array |
| `attribute_constraints` | `attribute_constraints` | JSONB | No | Default empty array |
| `required_assurance` | `required_assurance` | TEXT | No | Default STANDARD; AssuranceLevel enum |
| `valid_from` | `valid_from` | TIMESTAMPTZ | Yes | Optional |
| `valid_until` | `valid_until` | TIMESTAMPTZ | Yes | Later than valid_from |
| `invited_at` | `invited_at` | TIMESTAMPTZ | Yes | Optional |
| `joined_at` | `joined_at` | TIMESTAMPTZ | Yes | Optional |
| `revision` | `revision` | INTEGER | No | Default 1; positive |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Default clock timestamp |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Default clock timestamp; not before created_at |

Tenant scope: tenant_id; restrictive RLS required.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Relationship arrays remain typed UUID references. They do not create a second role, entitlement, scope or relationship owner.

### 4.2 CORE-003 — `core003`

#### `core003.leads`

Canonical source: `Lead` and nested `LeadSource`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `lead_id` | `lead_id` | UUID | No | Composite primary key with tenant_id |
| `tenant_id` | `tenant_id` | UUID | No | FK to core001.tenants |
| `customer_id` | `customer_id` | UUID | No | Opaque CORE-003 customer reference; no Customer FK |
| `status` | `status` | TEXT | No | LeadStatus enum |
| `priority` | `priority` | TEXT | No | LeadPriority enum |
| `source_type` | `source.source_type` | TEXT | No | LeadSourceType enum |
| `source_id` | `source.source_id` | TEXT | Yes | Optional |
| `campaign_id` | `source.campaign_id` | TEXT | Yes | Optional |
| `channel` | `source.channel` | TEXT | Yes | Optional |
| `metadata` | `metadata` | JSONB | No | Default empty object |
| `revision` | `revision` | INTEGER | No | Default 0; non-negative |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Default clock timestamp |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Default clock timestamp; not before created_at |

Tenant scope: tenant_id; restrictive RLS required.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: tenant/status/created_at; tenant/customer_id/created_at.

#### `core003.lead_ownership`

Canonical source: `LeadOwnership`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `lead_id` | `lead_id` | UUID | No | Composite primary key; FK to leads |
| `tenant_id` | `tenant_id` | UUID | No | Composite primary key; same-tenant FK |
| `owner_id` | `owner_id` | UUID | No | Opaque owner reference |
| `owner_role` | `owner_role` | TEXT | No | LeadOwnerRole enum |
| `assigned_at` | `assigned_at` | TIMESTAMPTZ | No | Required |
| `revision` | `revision` | INTEGER | No | Default 0; non-negative |
| `assignment_reference` | `assignment_reference` | TEXT | Yes | Optional |

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: tenant/owner/assigned_at.

#### `core003.ownership_transfers`

Canonical source: `OwnershipTransfer`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `transfer_id` | `transfer_id` | UUID | No | Primary key |
| `lead_id` | `lead_id` | UUID | No | Same-tenant FK to leads |
| `tenant_id` | `tenant_id` | UUID | No | FK to tenants |
| `previous_owner_id` | `previous_owner_id` | UUID | No | Opaque owner reference |
| `new_owner_id` | `new_owner_id` | UUID | No | Opaque owner reference; different from previous |
| `previous_revision` | `previous_revision` | INTEGER | No | Non-negative |
| `new_revision` | `new_revision` | INTEGER | No | Must equal previous_revision + 1 |
| `reason` | `reason` | TEXT | No | TransferReason enum |
| `transferred_at` | `transferred_at` | TIMESTAMPTZ | No | Required |
| `transfer_reference` | `transfer_reference` | TEXT | Yes | Optional |

Application privilege: SELECT, INSERT; no UPDATE or DELETE.

Indexes: unique tenant/lead/new_revision; tenant/transferred_at.

This table is append-only.

### 4.3 CORE-004 — `core004`

#### `core004.projects`

Canonical source: `ProjectIdentity` and `Project`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `project_id` | `identity.project_id` | TEXT | No | Composite primary key with tenant_id |
| `tenant_id` | `identity.tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `developer_id` | `identity.developer_id` | TEXT | No | Opaque reference |
| `project_code` | `identity.project_code` | TEXT | No | Tenant-scoped unique business identity |
| `name` | `name` | TEXT | No | Required text |
| `metadata` | `metadata` | JSONB | No | Default empty object |

Application privilege: SELECT, INSERT; no UPDATE or DELETE.

Indexes: unique tenant/project_code.

#### `core004.inventory`

Canonical source: `InventoryIdentity` and `Inventory`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `inventory_id` | `identity.inventory_id` | TEXT | No | Composite primary key with tenant_id |
| `tenant_id` | `identity.tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `inventory_type` | `identity.inventory_type` | TEXT | No | DEVELOPMENT/PROPERTY/UNIT |
| `developer_id` | `identity.developer_id` | TEXT | No | Opaque reference |
| `project_id` | `identity.project_id` | TEXT | No | Same-tenant Project FK |
| `property_id` | `identity.property_id` | TEXT | Yes | Optional hierarchy element |
| `unit_id` | `identity.unit_id` | TEXT | Yes | Optional hierarchy element |
| `name` | `name` | TEXT | No | Required text |
| `lifecycle` | `lifecycle` | TEXT | No | LifecycleState enum |
| `availability` | `availability` | TEXT | No | AvailabilityState enum |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Required |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Required; not before created_at |
| `version` | `version` | INTEGER | No | Default 1; positive |
| `metadata` | `metadata` | JSONB | No | Default empty object |

Hierarchy constraint:

- DEVELOPMENT: property_id and unit_id are NULL.
- PROPERTY: property_id is required and unit_id is NULL.
- UNIT: property_id and unit_id are required.

No unit_id-only foreign key is created.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: tenant/project/inventory_type; tenant/inventory_id.

### 4.4 CORE-006 — `core006`

#### `core006.deals`

Canonical source: `Deal`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `deal_id` | `deal_id` | TEXT | No | Composite primary key with tenant_id |
| `tenant_id` | `tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `customer_id` | `customer_id` | TEXT | No | Opaque reference |
| `broker_id` | `broker_id` | TEXT | No | Opaque reference |
| `builder_id` | `builder_id` | TEXT | Yes | Opaque reference |
| `project_id` | `project_id` | TEXT | Yes | Opaque reference; no guessed cross-owner FK |
| `unit_id` | `unit_id` | TEXT | Yes | Opaque reference; no unit-only FK |
| `status` | `status` | TEXT | No | DealStatus enum |
| `version` | `version` | INTEGER | No | Positive |
| `created_at` | `created_at` | TIMESTAMPTZ | No | Required |
| `updated_at` | `updated_at` | TIMESTAMPTZ | No | Required |
| `history` | `history` | JSONB | No | Default empty array |
| `source_of_truth` | `source_of_truth` | TEXT | No | Default `deal`; fixed by source contract |
| `offers` | `offers` | JSONB | No | Default empty array |
| `negotiation` | `negotiation` | JSONB | Yes | Optional typed object |
| `milestones` | `milestones` | JSONB | No | Default empty array |
| `ownership_binding` | `ownership_binding` | JSONB | Yes | Optional typed object |
| `evidence` | `evidence` | JSONB | No | Default empty array |
| `audit_log` | `audit_log` | JSONB | No | Default empty array |
| `contract_schema_version` | `contract_schema_version` | TEXT | No | Source contract version |

`participants` is deliberately persisted through `core006.deal_parties` rather than duplicated as a second JSONB representation.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: tenant/status/updated_at.

#### `core006.deal_parties`

Canonical source: `DealPartyRelationship`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `deal_id` | `deal_id` | TEXT | No | Same-tenant Deal FK |
| `tenant_id` | `tenant_id` | UUID | No | Strict UUID parse |
| `role` | `role` | TEXT | No | BUYER/CUSTOMER/SELLER/BUILDER/BROKER/REPRESENTATIVE |
| `party_id` | `party_id` | TEXT | No | Polymorphic; no universal FK |
| `relationship_version` | `relationship_version` | INTEGER | No | Default 1; positive |
| `lifecycle` | `lifecycle` | TEXT | No | ACTIVE/SUSPENDED/REMOVED |
| `metadata` | `metadata` | JSONB | No | Default empty object |

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Index: tenant/party_id.

### 4.5 CORE-007 — `core007`

#### `core007.governance_decisions`

Canonical source: `GovernanceDecision`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `decision_id` | `decision_id` | UUID | No | Composite primary key with tenant_id |
| `tenant_id` | `tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `subject_id` | `subject_id` | TEXT | No | Opaque subject reference |
| `correlation_id` | `correlation_id` | TEXT | No | Required |
| `policy_id` | `policy_id` | TEXT | No | Required |
| `policy_version` | `policy_version` | TEXT | No | Required |
| `policy_fingerprint` | `policy_fingerprint` | TEXT | No | Required |
| `source_evaluation_fingerprint` | `source_evaluation_fingerprint` | TEXT | No | Required |
| `decision_type` | `decision_type` | TEXT | No | GovernanceDecisionType enum |
| `action_class` | `action_class` | TEXT | No | GovernanceActionClass enum |
| `approval_required` | `approval_required` | BOOLEAN | No | Required |
| `required_authority` | `required_authority` | TEXT | Yes | GovernanceAuthorityClass enum |
| `escalation_level` | `escalation_level` | TEXT | No | GovernanceEscalationLevel enum |
| `matched_rule_ids` | `matched_rule_ids` | TEXT[] | No | Default empty array |
| `reasons` | `reasons` | TEXT[] | No | Default empty array |
| `evidence_references` | `evidence_references` | TEXT[] | No | Default empty array |
| `decided_at` | `decided_at` | TIMESTAMPTZ | No | Required |
| `schema_version` | `schema_version` | INTEGER | No | Positive |
| `fingerprint` | `fingerprint` | TEXT | No | SHA-256 lowercase hex |
| `review_state` | `review_state` | TEXT | Yes | GovernanceReviewState enum |
| `escalation_state` | `escalation_state` | TEXT | Yes | GovernanceEscalationState enum |
| `human_review_reference` | `human_review_reference` | TEXT | Yes | Optional |
| `decision_evidence` | `decision_evidence` | TEXT[] | No | Default empty array |
| `override_reference` | `override_reference` | TEXT | Yes | Optional |
| `override_authorization` | `override_authorization` | TEXT | Yes | Optional |
| `appeal_review_reference` | `appeal_review_reference` | TEXT | Yes | Optional |
| `irreversible_action_protected` | `irreversible_action_protected` | BOOLEAN | No | Default true |

Application privilege: SELECT, INSERT; no UPDATE or DELETE.

This is governance evidence, not an authorization engine.

#### `core007.approval_requests`

Canonical sources: `ApprovalRequest` and terminal `ApprovalRecord`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `request_id` | `request_id` | UUID | No | Composite primary key with tenant_id |
| `tenant_id` | `tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `subject_id` | `subject_id` | TEXT | No | Required |
| `correlation_id` | `correlation_id` | TEXT | No | Required |
| `governance_fingerprint` | `governance_fingerprint` | TEXT | No | Required |
| `policy_id` | `policy_id` | TEXT | No | Required |
| `policy_version` | `policy_version` | TEXT | No | Required |
| `requested_at` | `requested_at` | TIMESTAMPTZ | No | Required |
| `expires_at` | `expires_at` | TIMESTAMPTZ | No | Later than requested_at |
| `state` | `state` | TEXT | No | ApprovalState enum; default PENDING |
| `decision_record` | `ApprovalRecord` | JSONB | Yes | Terminal decision snapshot, optional |

`decision_record` contains the existing ApprovalRecord fields: request_id, state, decision_at, actor_reference, reason and fingerprint. It is not a new decision engine.

Application privilege: SELECT, INSERT, UPDATE; no DELETE.

Indexes: tenant/state/expires_at.

### 4.6 CORE-008 — `core008`

#### `core008.commission_contracts`

Canonical source: `CommissionContract`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `commission_id` | `commission_id` | TEXT | No | Part of composite primary key |
| `tenant_id` | `tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `entitlement` | `entitlement` | JSONB | No | CommissionEntitlementReference object |
| `basis` | `basis` | JSONB | No | CommissionBasis object |
| `rate` | `rate` | JSONB | No | CommissionRate object |
| `eligibility_rules` | `eligibility_rules` | JSONB | No | Array of typed rules |
| `effective_from` | `effective_from` | TIMESTAMPTZ | No | Required |
| `effective_to` | `effective_to` | TIMESTAMPTZ | Yes | Later than effective_from |
| `contract_version` | `contract_version` | INTEGER | No | Positive; part of primary key |
| `provenance` | `provenance` | JSONB | No | CommissionProvenance object |
| `state` | `state` | TEXT | No | CommissionContractState enum; default DRAFT |
| `metadata` | `metadata` | JSONB | No | Default empty object |

Primary key: `(tenant_id, commission_id, contract_version)`.

Application privilege: SELECT, INSERT; no UPDATE or DELETE. Contract versions are immutable records.

Indexes: tenant/state/effective_from.

#### `core008.financial_ledger_entries`

Canonical source: `FinancialLedgerEntry`, `LedgerAccountReference`, `MonetaryAmount` and `Currency`

| Column | Source field | PostgreSQL type | Nullable | Default / constraint |
|---|---|---|---|---|
| `entry_id` | `entry_id` | TEXT | No | Part of composite primary key |
| `tenant_id` | `tenant_id` | UUID | No | Strict UUID parse; FK to tenants |
| `commission_id` | `commission_id` | TEXT | No | Opaque CORE-008 reference |
| `entry_version` | `entry_version` | INTEGER | No | Positive; part of primary key |
| `transaction_reference` | `transaction_reference` | TEXT | No | Required |
| `debit_account_id` | `debit.account_id` | TEXT | No | Required |
| `debit_account_type` | `debit.account_type` | TEXT | No | Required |
| `credit_account_id` | `credit.account_id` | TEXT | No | Required; different from debit account |
| `credit_account_type` | `credit.account_type` | TEXT | No | Required |
| `amount` | `amount.amount` | NUMERIC | No | Unbounded; finite |
| `currency_code` | `amount.currency.code` | TEXT | No | Three uppercase letters |
| `currency_minor_unit` | `amount.currency.minor_unit` | SMALLINT | No | 0–6 |
| `currency_rounding_mode` | `amount.currency.rounding_mode` | TEXT | No | RoundingMode enum |
| `entry_timestamp` | `entry_timestamp` | TIMESTAMPTZ | No | Required |
| `source_reference` | `source_reference` | TEXT | No | Required |
| `provenance_reference` | `provenance_reference` | TEXT | No | Required |
| `metadata` | `metadata` | JSONB | No | Default empty object |

Primary key: `(tenant_id, entry_id, entry_version)`.

Application privilege: SELECT, INSERT; no UPDATE or DELETE.

Indexes: tenant/commission/entry_timestamp.

This table is append-only and does not replace an external general ledger or CORE-008 reconciliation owner.

## 5. Tenant policy and role enforcement

Every table that physically contains `tenant_id` must satisfy:

- ENABLE ROW LEVEL SECURITY
- FORCE ROW LEVEL SECURITY
- The application role is not table owner
- The application role has no superuser privilege
- The application role has no BYPASSRLS privilege
- A permissive application access policy exists
- A restrictive `FOR ALL` tenant policy exists
- `USING` and `WITH CHECK` use the same fail-closed UUID expression
- Missing or malformed tenant context resolves to NULL and denies tenant rows
- Application role has no DELETE or TRUNCATE privilege

The approved policy expression is:

```sql
tenant_id = CASE
  WHEN pg_input_is_valid(
    current_setting('app.tenant_id', true),
    'uuid'
  )
  THEN current_setting('app.tenant_id', true)::uuid
  ELSE NULL::uuid
END
