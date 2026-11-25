

# HOMIO / REOS — B4 Physical Schema Implementation Manifest

**Task:** BACKEND-001-B4 — PostgreSQL Integration  
**Repository:** `prajaktaranjane80-sketch/Homio`  
**Branch:** `reos-development`  
**Source baseline:** `c217d23e71122ccde402e10d8898fc710be7490d`  
**Architecture authority:** ARCH-037 — Database Final Schema Design v1.0  
**Execution authority:** `REOS_CONTROL_CENTER/data/state.json`  
**Implementation owner:** `REOS_CONTROL_CENTER/backend/`  
**Migration owner:** `REOS_CONTROL_CENTER/backend/scripts/postgres/migrations/`  
**Status:** Source-traceability record; implementation and CI verification pending.

---

## 1. Purpose and authority

This manifest records the source-backed mapping between the approved ARCH-037 database architecture, canonical CORE domain models and the PostgreSQL implementation.

It is an implementation evidence index. It is not a second schema authority, a new business-domain owner or an architecture amendment.

Authority order:

1. `REOS_CONTROL_CENTER/data/state.json`
2. Approved and frozen ARCH-037
3. Canonical CORE-001 through CORE-008 source models and contracts
4. `REOS_CONTROL_CENTER/architecture/backend/plans/HOMIO_Backend_Structure`
5. Existing PostgreSQL runtime, migration runner, migration manifest and infrastructure migrations
6. This implementation traceability manifest

ARCH-037 remains approved and frozen. This work implements the existing architecture; it does not reopen or replace it.

## 2. Verified baseline

| Item | Verified value |
|---|---|
| Repository HEAD | `c217d23e71122ccde402e10d8898fc710be7490d` |
| `state.json` | `5f1a09dba8d84ee5cbc06a49f37b5e68dc75c44b` |
| `AI_AGENT_ENTRYPOINT.py` | `2e1d66cec0a8ca17b24ccf285d3133ff16ca2834` |
| `B4 ka work plan` | `84c94c82ac5b0fde7c7bdf94acca235402c465ab` |
| `HOMIO_Backend_Structure` | `f8d9cd456568cc6c8eaae0caf764123a7e859ba6` |
| Active task | `BACKEND-001-B4` |
| Execution status | `CONTROL_CENTER_DRIVEN` |
| Latest inspected CI | Run `45428157611` — failed on three ARCH-037 schema integration assertions |

The live migration directory currently has four migrations, `00000001` through `00000004`. The B4 work plan requires the additive migration sequence `00000005` through `00000011`.

## 3. Identifier and tenant compatibility contract

### 3.1 Canonical tenant identifier

PostgreSQL tenant-isolation context is UUID.

The following canonical CORE models expose `tenant_id` as a string:

- CORE-004 Project and Inventory
- CORE-006 Deal and DealPartyRelationship
- CORE-007 GovernanceDecision and ApprovalRequest
- CORE-008 CommissionContract and FinancialLedgerEntry

Their tenant values must be strictly parsed as UUIDs at the persistence boundary and stored as PostgreSQL `uuid`.

The boundary must:

- Reject malformed UUID strings.
- Reject missing tenant values where required.
- Never trim, repair or silently generate a replacement tenant ID.
- Never create a second tenant registry.
- Preserve opaque non-tenant identifiers exactly as their source owners define them.

### 3.2 Opaque identifiers that must remain strings

| Owner | Identifier | PostgreSQL mapping |
|---|---|---|
| CORE-004 | `project_id` | `text` |
| CORE-004 | `developer_id` | `text` |
| CORE-004 | `inventory_id` | `text` |
| CORE-004 | `property_id` | nullable `text` |
| CORE-004 | `unit_id` | nullable `text` |
| CORE-006 | `deal_id` | `text` |
| CORE-006 | `customer_id` | `text` |
| CORE-006 | `broker_id` | `text` |
| CORE-006 | `builder_id` | nullable `text` |
| CORE-006 | `project_id` | nullable `text` |
| CORE-006 | `unit_id` | nullable `text` |
| CORE-006 | `party_id` | `text` |
| CORE-008 | `commission_id` | `text` |
| CORE-008 | `entry_id` | `text` |
| CORE-008 | `transaction_reference` | `text` |
| CORE-008 | Financial account references | `text` inside their typed JSON representation |

Do not force these identifiers into UUID columns.

A CORE-003 `customer_id` UUID and a CORE-006 `customer_id` string are not automatically the same referential identity. CORE-006 polymorphic party references must not receive a universal identity foreign key.

### 3.3 Foreign-key restriction

A foreign key is permitted only where a canonical source relationship proves the target.

A matching field name alone is not proof.

No universal foreign key is to be created for:

- CORE-006 polymorphic party references.
- CORE-004 developer, property or unit identifiers.
- CORE-008 debit/credit account references.
- CORE-003 customer references to CORE-001 identities without a proven canonical relationship.

## 4. Canonical source inventory and immutable readback

| Owner | Source path | Blob SHA |
|---|---|---|
| CORE-001 Identity | `AUTONOMY_ENGINE/core/identity_tenant/identity.py` | `49564ab0e7b3f19d192c343bd444ba3b45ced192` |
| CORE-001 Tenant | `AUTONOMY_ENGINE/core/identity_tenant/tenant.py` | `5fdda5750f37ea14214ede72ff97c739526390d6` |
| CORE-001 Membership | `AUTONOMY_ENGINE/core/identity_tenant/membership.py` | `919868a77bf589795c383a1fbb974fc69dede6ec` |
| CORE-001 Identity contract | `AUTONOMY_ENGINE/core/identity_tenant/identity_contract.json` | `de2634bdd93fe7f268bb4870b5bab914eca6e084` |
| CORE-001 Tenant contract | `AUTONOMY_ENGINE/core/identity_tenant/tenant_contract.json` | `2e8d0b9910f8bd320f3e02841dede25232123093` |
| CORE-001 Membership contract | `AUTONOMY_ENGINE/core/identity_tenant/membership_contract.json` | `9304de1df604c1937d22cd682cfb88cc686b2fe5` |
| CORE-003 Lead | `AUTONOMY_ENGINE/core/lead_ownership/lead.py` | `9b092087c5e4b820b5ee320abdb4c5fc00adcbce` |
| CORE-003 Lead ownership | `AUTONOMY_ENGINE/core/lead_ownership/lead_ownership.py` | `dbb3917f6a3c2108bcb9de7c705cb0441758a7f7` |
| CORE-003 Ownership transfer | `AUTONOMY_ENGINE/core/lead_ownership/ownership_transfer.py` | `aaba13bb20c3494c3f32579ba7081cab5856a3a9` |
| CORE-003 Lead contract | `AUTONOMY_ENGINE/core/lead_ownership/lead_contract.py` | `15d814c1a5bce460c852c7666b646a0aa1e3391f` |
| CORE-004 Project | `AUTONOMY_ENGINE/core/inventory/project.py` | `bc34a9729197cf55d8d29bda943be3d8d09dd2a9` |
| CORE-004 Inventory | `AUTONOMY_ENGINE/core/inventory/inventory.py` | `be43bffd198d6c3f08c3aad641ed03696955f4e0` |
| CORE-006 Deal | `AUTONOMY_ENGINE/core/deal_transaction/deal.py` | `2fc25aaf118da6512e89d487a89f93cee9bc2da5` |
| CORE-006 Deal contract | `AUTONOMY_ENGINE/core/deal_transaction/deal_contract.py` | `9c753c0de05e7ff11d16bfae4fb55b870e86581b` |
| CORE-006 Deal parties | `AUTONOMY_ENGINE/core/deal_transaction/deal_parties.py` | `74256a3f6451102c2ea298cc62db6ea8e09a521f` |
| CORE-007 Governance decision | `AUTONOMY_ENGINE/core/trust_fraud_governance/governance_decision.py` | `dcb5991c78ad10e60f489e2dda72f9248a5e4f0f` |
| CORE-007 Governance policy | `AUTONOMY_ENGINE/core/trust_fraud_governance/governance_policy.py` | `a6068c5ab46976a8dabd6f2d1b6aa34098eff6c6` |
| CORE-007 Approval workflow | `AUTONOMY_ENGINE/core/trust_fraud_governance/approval_workflow.py` | `704e5e554b30e02ee38b4fa5b3358b7b0ea46175` |
| CORE-008 Financial domain | `AUTONOMY_ENGINE/core/commission_financial/financial_domain.py` | `4b6af8da3ec7687c05b0a9782da305d2f267b3dc` |
| CORE-008 Commission contract | `AUTONOMY_ENGINE/core/commission_financial/commission_contract.py` | `efbf22c1368b288840a68260a1fdcfa66be8c0b3` |
| CORE-008 Financial ledger boundary | `AUTONOMY_ENGINE/core/commission_financial/financial_ledger_boundary.py` | `b3c324aff41a449392ffef1b1d143621d6151ef6` |

## 5. Ordered migration ownership

Existing migrations are immutable:

| ID | File | Owner | Treatment |
|---|---|---|---|
| `00000001` | `00000001-core002-event-outbox.sql` | CORE-002 | Preserve |
| `00000002` | `00000002-core002-safe-tenant-context.sql` | CORE-002 | Preserve |
| `00000003` | `00000003-b4-durable-api-sessions.sql` | B4 | Preserve |
| `00000004` | `00000004-b4-minimized-security-audit.sql` | B4 | Preserve |

Required additive sequence:

| ID | File | Owner |
|---|---|---|
| `00000005` | `00000005-core001-identity-tenant.sql` | CORE-001 |
| `00000006` | `00000006-core003-lead-ownership.sql` | CORE-003 |
| `00000007` | `00000007-core004-inventory.sql` | CORE-004 |
| `00000008` | `00000008-core006-deal-transaction.sql` | CORE-006 |
| `00000009` | `00000009-core007-trust-governance.sql` | CORE-007 |
| `00000010` | `00000010-core008-financial.sql` | CORE-008 |
| `00000011` | `00000011-b4-security-audit-tenant-write-guard.sql` | B4 infrastructure |

All migrations are regular SQL files in the existing canonical migration directory. The existing migration manifest and runner remain the only migration authorities.

## 6. CORE-001 physical mapping

**Migration:** `00000005-core001-identity-tenant.sql`

### 6.1 `core001.identities`

**Source:** `Identity` in `identity.py`; `Identity` contract.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `identity_id` | `identity_id` | `uuid` | NOT NULL |
| `identity_type` | `identity_type` | `text` | NOT NULL |
| `display_name` | `display_name` | `text` | NOT NULL |
| `handle` | `handle` | `varchar(64)` | NOT NULL |
| `status` | `status` | `text` | NOT NULL / `ACTIVE` |
| `privacy_class` | `privacy_class` | `text` | NOT NULL / `INTERNAL` |
| `revision` | `revision` | `integer` | NOT NULL / `1` |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |

Keys and constraints:

- Primary key: `identity_id`.
- Unique key: canonical normalized `handle`.
- `identity_type`: `HUMAN`, `SERVICE`, `AI`, `SYSTEM`.
- `status`: `ACTIVE`, `SUSPENDED`, `DEACTIVATED`.
- `privacy_class`: `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`.
- `revision >= 1`.
- Handle is lower-case canonical text and must satisfy the source handle pattern.
- The canonical handle cannot change after identity registration.
- `created_at` is immutable at the domain boundary.
- No tenant RLS: Identity is a global CORE-001 identity record, not a tenant-bearing table.

Required index: unique `handle`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 6.2 `core001.identity_accounts`

**Source:** `IdentityAccount` in `identity.py`; `IdentityAccount` contract.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `account_id` | `account_id` | `uuid` | NOT NULL |
| `identity_id` | `identity_id` | `uuid` | NOT NULL |
| `status` | `status` | `text` | NOT NULL / `ENABLED` |
| `authentication_epoch` | `authentication_epoch` | `integer` | NOT NULL / `1` |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |

Keys and constraints:

- Primary key: `account_id`.
- Foreign key: `identity_id → core001.identities.identity_id`.
- `status`: `ENABLED`, `LOCKED`, `DISABLED`.
- `authentication_epoch >= 1`.
- `updated_at >= created_at`.
- Do not add `UNIQUE(identity_id)`: the canonical registry indexes accounts by `account_id` and does not establish a one-account-per-identity uniqueness invariant.
- No tenant RLS: account identity is global.

Required index: `identity_id`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 6.3 `core001.tenants`

**Source:** `Tenant` in `tenant.py`; `tenant_contract.json`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL |
| `tenant_kind` | `tenant_kind` | `text` | NOT NULL |
| `operating_mode` | `operating_mode` | `text` | NOT NULL |
| `display_name` | `display_name` | `text` | NOT NULL |
| `slug` | `slug` | `varchar(64)` | NOT NULL |
| `status` | `status` | `text` | NOT NULL / `PROVISIONING` |
| `isolation_profile` | `isolation_profile` | `text` | NOT NULL / `SHARED_LOGICAL` |
| `residency_mode` | `residency_mode` | `text` | NOT NULL / `GLOBAL_ALLOWED` |
| `residency_region` | `residency_region` | `text` | NULL |
| `jurisdiction` | `jurisdiction` | `text` | NULL |
| `quota_profile` | `quota_profile` | `varchar(128)` | NOT NULL / `default` |
| `owner_identity_id` | `owner_identity_id` | `uuid` | NULL |
| `primary_admin_identity_id` | `primary_admin_identity_id` | `uuid` | NULL |
| `configuration_ref` | `configuration_ref` | `jsonb` | NOT NULL |
| `security_profile_ref` | `security_profile_ref` | `jsonb` | NOT NULL |
| `region_jurisdiction_ref` | `region_jurisdiction_ref` | `jsonb` | NULL |
| `revision` | `revision` | `integer` | NOT NULL / `1` |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |

Nested JSONB source structures:

- `configuration_ref`: `reference_id`, `configuration_key`, `version`.
- `security_profile_ref`: `reference_id`, `profile_key`, `version`, `fail_closed`, `require_valid_tenant_context`.
- `region_jurisdiction_ref`: `region`, `jurisdiction`.

Keys and constraints:

- Primary key: `tenant_id`.
- Unique key: normalized `slug`.
- `tenant_kind`: `BROKERAGE`, `BUILDER`, `ENTERPRISE`, `PARTNER`, `PLATFORM`.
- `operating_mode`: `OWNED_INTERNATIONAL_BROKERAGE`, `BROKER_SAAS`, `BUILDER_SAAS`, `ENTERPRISE_WHITE_LABEL`, `PLATFORM_API_PARTNER`.
- `status`: `PROVISIONING`, `PENDING_ACTIVATION`, `ACTIVE`, `RESTRICTED`, `SUSPENDED`, `DEACTIVATING`, `DEACTIVATED`, `ARCHIVED`.
- `isolation_profile`: `SHARED_LOGICAL`, `TENANT_DEDICATED`.
- `residency_mode`: `GLOBAL_ALLOWED`, `REGION_BOUND`, `COUNTRY_BOUND`, `CUSTOM_POLICY`.
- `revision >= 1`.
- `updated_at >= created_at`.
- Slug must satisfy the source canonical slug pattern.
- Foreign keys: `owner_identity_id` and `primary_admin_identity_id` to `core001.identities.identity_id`.
- Active tenant state requires the canonical owner and primary administrator and the fail-closed security profile defined in the tenant contract.
- Configuration and security profile columns store references only; they do not create another configuration or policy owner.

RLS:

- `ENABLE ROW LEVEL SECURITY`.
- `FORCE ROW LEVEL SECURITY`.
- Restrictive tenant `FOR ALL` policy using the exact safe UUID context expression owned by `PostgresRuntime`.
- Application role is not table owner and does not bypass RLS.

Required indexes: unique `slug`; status lookup index.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 6.4 `core001.organizations`

**Source:** `Organization` in `membership.py`; membership contract.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `organization_id` | `organization_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL |
| `display_name` | `display_name` | `text` | NOT NULL |
| `slug` | `slug` | `varchar(64)` | NOT NULL |
| `status` | `status` | `text` | NOT NULL / `ACTIVE` |
| `parent_organization_id` | `parent_organization_id` | `uuid` | NULL |
| `revision` | `revision` | `integer` | NOT NULL / `1` |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |

Keys and constraints:

- Primary key: `organization_id`.
- Unique key: `(tenant_id, organization_id)` for same-tenant references.
- Unique key: `(tenant_id, slug)`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- Parent foreign key: `(tenant_id, parent_organization_id) → core001.organizations(tenant_id, organization_id)`.
- `parent_organization_id` cannot equal `organization_id`.
- `status`: `ACTIVE`, `RESTRICTED`, `SUSPENDED`, `DEACTIVATED`.
- `revision >= 1`.
- `updated_at >= created_at`.

RLS: forced tenant RLS using the exact `PostgresRuntime` tenant guard.

Required indexes: `(tenant_id, slug)` unique; `(tenant_id, parent_organization_id)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 6.5 `core001.memberships`

**Source:** `Membership` in `membership.py`; membership contract.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `membership_id` | `membership_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL |
| `organization_id` | `organization_id` | `uuid` | NOT NULL |
| `identity_id` | `identity_id` | `uuid` | NOT NULL |
| `status` | `status` | `text` | NOT NULL / `INVITED` |
| `role_ids` | `role_ids` | `uuid[]` | NOT NULL / empty array |
| `entitlement_ids` | `entitlement_ids` | `uuid[]` | NOT NULL / empty array |
| `scope_ids` | `scope_ids` | `uuid[]` | NOT NULL / empty array |
| `relationship_ids` | `relationship_ids` | `uuid[]` | NOT NULL / empty array |
| `attribute_constraints` | `attribute_constraints` | `jsonb` | NOT NULL / empty array |
| `required_assurance` | `required_assurance` | `text` | NOT NULL / `STANDARD` |
| `valid_from` | `valid_from` | `timestamptz` | NULL |
| `valid_until` | `valid_until` | `timestamptz` | NULL |
| `invited_at` | `invited_at` | `timestamptz` | NULL |
| `joined_at` | `joined_at` | `timestamptz` | NULL |
| `revision` | `revision` | `integer` | NOT NULL / `1` |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |

`attribute_constraints` stores the source `AttributeConstraint` entries: `attribute_key`, `operator`, `expected_values`.

Keys and constraints:

- Primary key: `membership_id`.
- Foreign key: `(tenant_id, organization_id) → core001.organizations(tenant_id, organization_id)`.
- Foreign key: `identity_id → core001.identities.identity_id`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- `status`: `INVITED`, `PENDING`, `ACTIVE`, `RESTRICTED`, `SUSPENDED`, `REVOKED`, `EXPIRED`.
- `required_assurance`: `BASIC`, `STANDARD`, `STRONG`, `HIGH`.
- Each UUID array must contain unique UUIDs, matching the source model.
- `valid_until > valid_from` when both values are present.
- `revision >= 1`.
- `updated_at >= created_at`.
- Do not invent role, entitlement, scope or relationship tables in this migration sequence. Their identifiers remain references owned by CORE-001's canonical contract.

RLS: forced tenant RLS using the exact `PostgresRuntime` tenant guard.

Required indexes: `(tenant_id, organization_id)`; `(tenant_id, identity_id)`; `(tenant_id, status)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

## 7. CORE-003 physical mapping

**Migration:** `00000006-core003-lead-ownership.sql`

### 7.1 `core003.leads`

**Source:** `Lead` and `LeadSource` in `lead.py`; `lead_contract.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `lead_id` | `lead_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL |
| `customer_id` | `customer_id` | `uuid` | NOT NULL |
| `status` | `status` | `text` | NOT NULL |
| `priority` | `priority` | `text` | NOT NULL |
| `source_type` | `source.source_type` | `text` | NOT NULL |
| `source_id` | `source.source_id` | `text` | NULL |
| `campaign_id` | `source.campaign_id` | `text` | NULL |
| `channel` | `source.channel` | `text` | NULL |
| `metadata` | `metadata` | `jsonb` | NOT NULL / empty object |
| `revision` | `revision` | `integer` | NOT NULL / `0` |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |

Keys and constraints:

- Primary key: `lead_id`.
- Unique key: `(tenant_id, lead_id)` for same-tenant ownership references.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- Do not create an automatic foreign key from `customer_id` to CORE-001 identities.
- `status`: `NEW`, `QUALIFYING`, `QUALIFIED`, `NURTURING`, `CONVERTED`, `LOST`, `ARCHIVED`.
- `priority`: `LOW`, `NORMAL`, `HIGH`, `URGENT`.
- `source_type`: `DIRECT`, `WEBSITE`, `PORTAL`, `REFERRAL`, `BUILDER`, `BROKER`, `PARTNER`, `CAMPAIGN`, `IMPORT`, `API`, `OTHER`.
- `revision >= 0`.
- `updated_at >= created_at`.
- `metadata` must be a JSON object.

RLS: forced tenant RLS using the exact `PostgresRuntime` tenant guard.

Required indexes: `(tenant_id, lead_id)` unique; `(tenant_id, customer_id)`; `(tenant_id, status)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 7.2 `core003.lead_ownership`

**Source:** `LeadOwnership` in `lead_ownership.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `lead_id` | `lead_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL |
| `owner_id` | `owner_id` | `uuid` | NOT NULL |
| `owner_role` | `owner_role` | `text` | NOT NULL |
| `assigned_at` | `assigned_at` | `timestamptz` | NOT NULL |
| `revision` | `revision` | `integer` | NOT NULL / `0` |
| `assignment_reference` | `assignment_reference` | `text` | NULL |

Keys and constraints:

- Primary key: `(tenant_id, lead_id)`, matching the source `binding_key`.
- Foreign key: `(tenant_id, lead_id) → core003.leads(tenant_id, lead_id)`.
- `owner_role`: `BROKERAGE`, `BROKER`, `AGENT`, `PARTNER`, `BUILDER`, `PLATFORM`.
- `revision >= 0`.
- Owner ID remains a UUID reference; do not invent a universal owner foreign key.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, owner_id)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 7.3 `core003.ownership_transfers`

**Source:** `OwnershipTransfer` in `ownership_transfer.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `transfer_id` | `transfer_id` | `uuid` | NOT NULL |
| `lead_id` | `lead_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL |
| `previous_owner_id` | `previous_owner_id` | `uuid` | NOT NULL |
| `new_owner_id` | `new_owner_id` | `uuid` | NOT NULL |
| `previous_revision` | `previous_revision` | `integer` | NOT NULL |
| `new_revision` | `new_revision` | `integer` | NOT NULL |
| `reason` | `reason` | `text` | NOT NULL |
| `transferred_at` | `transferred_at` | `timestamptz` | NOT NULL |
| `transfer_reference` | `transfer_reference` | `text` | NULL |

Keys and constraints:

- Primary key: `transfer_id`.
- Unique key: `(tenant_id, lead_id, new_revision)`, matching source `history_key`.
- Foreign key: `(tenant_id, lead_id) → core003.leads(tenant_id, lead_id)`.
- `reason`: `MANUAL`, `BUSINESS_RULE`, `REASSIGNMENT`, `TENANT_INTERNAL`, `PARTNER_CHANGE`.
- `previous_revision >= 0`.
- `new_revision = previous_revision + 1`.
- `previous_owner_id <> new_owner_id`.
- Owner IDs remain source references; no unproven identity foreign key.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, lead_id, new_revision)` unique.

Application privileges: `SELECT`, `INSERT`; no `UPDATE` or `DELETE` for historical transfer records.

## 8. CORE-004 physical mapping

**Migration:** `00000007-core004-inventory.sql`

### 8.1 `core004.projects`

**Source:** `ProjectIdentity` and `Project` in `project.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `project_id` | `identity.project_id` | `text` | NOT NULL |
| `tenant_id` | `identity.tenant_id` | `uuid` | NOT NULL after strict parsing |
| `developer_id` | `identity.developer_id` | `text` | NOT NULL |
| `project_code` | `identity.project_code` | `varchar(64)` | NOT NULL |
| `name` | `name` | `text` | NOT NULL |
| `metadata` | `metadata` | `jsonb` | NOT NULL / empty object |

Keys and constraints:

- Primary key: `(tenant_id, project_id)`.
- Unique key: `(tenant_id, project_code)`, matching `ProjectIdentity.identity_key`.
- `project_code` is normalized uppercase and follows the source pattern of 2–64 uppercase letters, digits, underscore or hyphen.
- `developer_id` and `project_id` remain opaque strings.
- `metadata` must be a JSON object.
- Do not create a developer table or external developer foreign key in B4.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, project_code)` unique; `(tenant_id, project_id)` primary key.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 8.2 `core004.inventory`

**Source:** `InventoryIdentity` and `Inventory` in `inventory.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `inventory_id` | `identity.inventory_id` | `text` | NOT NULL |
| `tenant_id` | `identity.tenant_id` | `uuid` | NOT NULL after strict parsing |
| `inventory_type` | `identity.inventory_type` | `text` | NOT NULL |
| `developer_id` | `identity.developer_id` | `text` | NOT NULL |
| `project_id` | `identity.project_id` | `text` | NOT NULL |
| `property_id` | `identity.property_id` | `text` | NULL |
| `unit_id` | `identity.unit_id` | `text` | NULL |
| `name` | `name` | `text` | NOT NULL |
| `lifecycle` | `lifecycle` | `text` | NOT NULL |
| `availability` | `availability` | `text` | NOT NULL |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |
| `version` | `version` | `integer` | NOT NULL / `1` |
| `metadata` | `metadata` | `jsonb` | NOT NULL / empty object |

Keys and constraints:

- Unique identity key: `(tenant_id, inventory_type, project_id, property_id, unit_id, inventory_id)` using `UNIQUE NULLS NOT DISTINCT`, matching the source hierarchy identity semantics.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- Same-owner project foreign key: `(tenant_id, project_id) → core004.projects(tenant_id, project_id)`.
- `inventory_type`: `DEVELOPMENT`, `PROPERTY`, `UNIT`.
- `lifecycle`: `DRAFT`, `ACTIVE`, `RESERVED`, `BLOCKED`, `SOLD`, `UNAVAILABLE`, `ARCHIVED`.
- `availability`: `AVAILABLE`, `RESERVED`, `BLOCKED`, `ALLOCATED`, `SOLD`, `UNAVAILABLE`.
- `version >= 1`.
- `updated_at >= created_at`.
- Hierarchy constraints:
  - `DEVELOPMENT`: `property_id` and `unit_id` are NULL.
  - `PROPERTY`: `property_id` is NOT NULL and `unit_id` is NULL.
  - `UNIT`: both `property_id` and `unit_id` are NOT NULL.
- Do not create property or unit foreign keys; the source says hierarchy reconstruction and parent/child validation belong to later CORE-004 owners.

RLS: forced tenant RLS.

Required indexes: tenant/project; tenant/inventory type; the complete identity key unique constraint.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

## 9. CORE-006 physical mapping

**Migration:** `00000008-core006-deal-transaction.sql`

### 9.1 `core006.deals`

**Source:** `Deal` in `deal.py`; `DealStatus` in `deal_contract.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `deal_id` | `deal_id` | `text` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL after strict parsing |
| `customer_id` | `customer_id` | `text` | NOT NULL |
| `broker_id` | `broker_id` | `text` | NOT NULL |
| `builder_id` | `builder_id` | `text` | NULL |
| `project_id` | `project_id` | `text` | NULL |
| `unit_id` | `unit_id` | `text` | NULL |
| `status` | `status` | `text` | NOT NULL |
| `version` | `version` | `integer` | NOT NULL |
| `created_at` | `created_at` | `timestamptz` | NOT NULL |
| `updated_at` | `updated_at` | `timestamptz` | NOT NULL |
| `history` | `history` | `jsonb` | NOT NULL / empty array |
| `source_of_truth` | `source_of_truth` | `text` | NOT NULL / `deal` |
| `offers` | `offers` | `jsonb` | NOT NULL / empty array |
| `negotiation` | `negotiation` | `jsonb` | NULL |
| `milestones` | `milestones` | `jsonb` | NOT NULL / empty array |
| `ownership_binding` | `ownership_binding` | `jsonb` | NULL |
| `evidence` | `evidence` | `jsonb` | NOT NULL / empty array |
| `audit_log` | `audit_log` | `jsonb` | NOT NULL / empty array |
| `participants` | `participants` | `jsonb` | NOT NULL / empty array |
| `contract_schema_version` | `contract_schema_version` | `text` | NOT NULL |

Keys and constraints:

- Primary key: `(tenant_id, deal_id)`, matching `Deal.identity_key`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- `status` values must match the canonical `DealStatus` enum in `deal_contract.py`.
- `version >= 1`.
- `updated_at >= created_at`.
- `history`, `offers`, `milestones`, `evidence`, `audit_log`, `participants` are JSON arrays.
- `negotiation` and `ownership_binding` are JSON objects when present.
- No foreign keys from `customer_id`, `broker_id`, `builder_id`, `project_id` or `unit_id` without a proven canonical mapping.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, deal_id)` primary key; `(tenant_id, status)`; `(tenant_id, customer_id)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

### 9.2 `core006.deal_parties`

**Source:** `DealPartyRelationship` in `deal_parties.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `deal_id` | `deal_id` | `text` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL after strict parsing |
| `role` | `role` | `text` | NOT NULL |
| `party_id` | `party_id` | `text` | NOT NULL |
| `relationship_version` | `relationship_version` | `integer` | NOT NULL / `1` |
| `lifecycle` | `lifecycle` | `text` | NOT NULL / `ACTIVE` |
| `metadata` | `metadata` | `jsonb` | NOT NULL / empty object |

Keys and constraints:

- Primary key: `(tenant_id, deal_id, role, party_id)`, matching source `relationship_key`.
- Foreign key: `(tenant_id, deal_id) → core006.deals(tenant_id, deal_id)`.
- `role`: `BUYER`, `CUSTOMER`, `SELLER`, `BUILDER`, `BROKER`, `REPRESENTATIVE`.
- `lifecycle`: `ACTIVE`, `SUSPENDED`, `REMOVED`.
- `relationship_version >= 1`.
- `metadata` must be a JSON object.
- `party_id` remains polymorphic text. No universal party foreign key.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, deal_id)`; `(tenant_id, party_id)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

## 10. CORE-007 physical mapping

**Migration:** `00000009-core007-trust-governance.sql`

### 10.1 `core007.governance_decisions`

**Source:** `GovernanceDecision` in `governance_decision.py`; `GovernanceActionClass` in `governance_policy.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `decision_id` | `decision_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL after strict parsing |
| `subject_id` | `subject_id` | `text` | NOT NULL |
| `correlation_id` | `correlation_id` | `text` | NOT NULL |
| `policy_id` | `policy_id` | `text` | NOT NULL |
| `policy_version` | `policy_version` | `text` | NOT NULL |
| `policy_fingerprint` | `policy_fingerprint` | `text` | NOT NULL |
| `source_evaluation_fingerprint` | `source_evaluation_fingerprint` | `text` | NOT NULL |
| `decision_type` | `decision_type` | `text` | NOT NULL |
| `action_class` | `action_class` | `text` | NOT NULL |
| `approval_required` | `approval_required` | `boolean` | NOT NULL |
| `required_authority` | `required_authority` | `text` | NULL |
| `escalation_level` | `escalation_level` | `text` | NOT NULL |
| `matched_rule_ids` | `matched_rule_ids` | `text[]` | NOT NULL |
| `reasons` | `reasons` | `text[]` | NOT NULL |
| `evidence_references` | `evidence_references` | `text[]` | NOT NULL |
| `decided_at` | `decided_at` | `timestamptz` | NOT NULL |
| `schema_version` | `schema_version` | `integer` | NOT NULL |
| `fingerprint` | `fingerprint` | `text` | NOT NULL |
| `review_state` | `review_state` | `text` | NOT NULL |
| `escalation_state` | `escalation_state` | `text` | NOT NULL |
| `human_review_reference` | `human_review_reference` | `text` | NULL |
| `decision_evidence` | `decision_evidence` | `text[]` | NOT NULL |
| `override_reference` | `override_reference` | `text` | NULL |
| `override_authorization` | `override_authorization` | `text` | NULL |
| `appeal_review_reference` | `appeal_review_reference` | `text` | NULL |
| `irreversible_action_protected` | `irreversible_action_protected` | `boolean` | NOT NULL / `true` |

Keys and constraints:

- Primary key: `decision_id`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- `decision_type`: `CONTINUE`, `REVIEW`, `APPROVAL_REQUIRED`, `ESCALATION_REQUIRED`.
- `action_class`: `INFORMATIONAL`, `REVIEW`, `HIGH_RISK`, `CRITICAL`.
- `required_authority`: `STANDARD_REVIEW`, `SENIOR_REVIEW`, `COMPLIANCE`, `SECURITY`, `FINANCIAL`, `EXECUTIVE`.
- `escalation_level`: `NONE`, `REVIEW`, `HIGH`, `CRITICAL`.
- `review_state`: `NOT_REQUIRED`, `PENDING`, `UNDER_REVIEW`, `COMPLETED`.
- `escalation_state`: `NOT_REQUIRED`, `OPEN`, `ACKNOWLEDGED`, `RESOLVED`.
- Arrays must be stored as arrays and not flattened into unrelated tables.
- `schema_version >= 1`.
- `fingerprint` must be a lowercase SHA-256 hexadecimal digest.
- This record is a governance decision, not an authorization record or replacement authorization engine.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, decision_id)`; `(tenant_id, subject_id)`; `(tenant_id, decided_at DESC)`.

Application privileges: `SELECT`, `INSERT`; no `UPDATE` or `DELETE` for immutable decision records.

### 10.2 `core007.approval_requests`

**Source:** `ApprovalRequest` in `approval_workflow.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `request_id` | `request_id` | `uuid` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL after strict parsing |
| `subject_id` | `subject_id` | `text` | NOT NULL |
| `correlation_id` | `correlation_id` | `text` | NOT NULL |
| `governance_fingerprint` | `governance_fingerprint` | `text` | NOT NULL |
| `policy_id` | `policy_id` | `text` | NOT NULL |
| `policy_version` | `policy_version` | `text` | NOT NULL |
| `requested_at` | `requested_at` | `timestamptz` | NOT NULL |
| `expires_at` | `expires_at` | `timestamptz` | NOT NULL |
| `state` | `state` | `text` | NOT NULL / `PENDING` |

Keys and constraints:

- Primary key: `request_id`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- `state`: `NOT_REQUIRED`, `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`, `CANCELLED`.
- `expires_at > requested_at`.
- `governance_fingerprint` is an immutable reference value, not a foreign key to a made-up decision relation.
- `ApprovalRecord` is a transition result, not a separate ARCH-037 relation in this migration set.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, state, expires_at)`; `(tenant_id, subject_id)`.

Application privileges: `SELECT`, `INSERT`, `UPDATE`; no `DELETE`.

## 11. CORE-008 physical mapping

**Migration:** `00000010-core008-financial.sql`

### 11.1 `core008.commission_contracts`

**Source:** `CommissionContract` and nested value objects in `commission_contract.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `commission_id` | `commission_id` | `text` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL after strict parsing |
| `entitlement` | `entitlement` | `jsonb` | NOT NULL |
| `basis` | `basis` | `jsonb` | NOT NULL |
| `rate` | `rate` | `jsonb` | NOT NULL |
| `eligibility_rules` | `eligibility_rules` | `jsonb` | NOT NULL / empty array |
| `effective_from` | `effective_from` | `timestamptz` | NOT NULL |
| `effective_to` | `effective_to` | `timestamptz` | NULL |
| `contract_version` | `contract_version` | `integer` | NOT NULL |
| `provenance` | `provenance` | `jsonb` | NOT NULL |
| `state` | `state` | `text` | NOT NULL / `DRAFT` |
| `metadata` | `metadata` | `jsonb` | NOT NULL / empty object |

Nested JSONB contents preserve the canonical source structures:

- `entitlement`: `entitlement_id`, `tenant_id`, `entitled_party`, `deal_reference`, `ownership_reference`, `provenance_reference`.
- `entitlement.entitled_party`: `party_type`, `party_id`.
- `basis`: `basis_type`, `source_reference`, optional `currency`.
- `rate`: `rate_type`, decimal `value`, optional `currency`.
- `eligibility_rules`: `rule_code`, `operator`, optional `value`, `evidence_required`.
- `provenance`: `source_type`, `source_reference`, `captured_at`, `evidence_reference`.

Keys and constraints:

- Tenant-scoped historical identity: `(tenant_id, commission_id, contract_version)`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- `contract_version >= 1`.
- `effective_to > effective_from` when present.
- `state`: `DRAFT`, `ACTIVE`, `SUSPENDED`, `EXPIRED`, `REVOKED`.
- `basis_type`: `GROSS_TRANSACTION_VALUE`, `NET_TRANSACTION_VALUE`, `FIXED_TRANSACTION_AMOUNT`, `REFERENCE_AMOUNT`.
- `rate_type`: `PERCENTAGE`, `FIXED_AMOUNT`.
- JSONB values must preserve the source value-object structure.
- No foreign key from nested deal, ownership, party or provenance references without a proven canonical target relationship.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, commission_id, contract_version)` unique; `(tenant_id, state, effective_from, effective_to)`.

Application privileges: `SELECT`, `INSERT`; no `UPDATE` or `DELETE` for immutable historical contract versions.

### 11.2 `core008.financial_ledger_entries`

**Source:** `FinancialLedgerEntry`, `LedgerAccountReference` in `financial_ledger_boundary.py`; `MonetaryAmount` and `Currency` in `financial_domain.py`.

| Column | Source field | PostgreSQL type | Nullable/default |
|---|---|---|---|
| `entry_id` | `entry_id` | `text` | NOT NULL |
| `tenant_id` | `tenant_id` | `uuid` | NOT NULL after strict parsing |
| `commission_id` | `commission_id` | `text` | NOT NULL |
| `entry_version` | `entry_version` | `integer` | NOT NULL |
| `transaction_reference` | `transaction_reference` | `text` | NOT NULL |
| `debit` | `debit` | `jsonb` | NOT NULL |
| `credit` | `credit` | `jsonb` | NOT NULL |
| `amount` | `amount.amount` | `numeric` | NOT NULL |
| `currency_code` | `amount.currency.code` | `char(3)` | NOT NULL |
| `currency_minor_unit` | `amount.currency.minor_unit` | `integer` | NOT NULL |
| `currency_rounding_mode` | `amount.currency.rounding_mode` | `text` | NOT NULL |
| `entry_timestamp` | `entry_timestamp` | `timestamptz` | NOT NULL |
| `source_reference` | `source_reference` | `text` | NOT NULL |
| `provenance_reference` | `provenance_reference` | `text` | NOT NULL |
| `metadata` | `metadata` | `jsonb` | NOT NULL / empty object |
| `immutable_fingerprint` | `immutable_fingerprint` | `text` | NOT NULL |

Nested JSONB contents:

- `debit`: `account_id`, `account_type`.
- `credit`: `account_id`, `account_type`.
- Amount currency: `code`, `minor_unit`, `rounding_mode`.

Keys and constraints:

- Primary key: `(tenant_id, entry_id, entry_version)`, matching source `identity_key`.
- Foreign key: `tenant_id → core001.tenants.tenant_id`.
- `entry_version >= 1`.
- `amount > 0`.
- `currency_code` must contain three uppercase letters.
- `currency_minor_unit` must be between 0 and 6, matching the source foundation.
- `currency_rounding_mode`: `CEILING`, `DOWN`, `FLOOR`, `HALF_DOWN`, `HALF_EVEN`, `HALF_UP`, `UP`.
- Debit and credit account IDs must differ.
- `debit` and `credit` must be JSON objects.
- `metadata` must be a JSON object.
- `immutable_fingerprint` is a lowercase SHA-256 digest.
- `amount` must be unbounded PostgreSQL `numeric`, with no precision or scale modifier. Do not use `numeric(18,2)`, `numeric(20,4)` or floating-point types.
- Do not create financial account tables or universal account foreign keys in B4.

RLS: forced tenant RLS.

Required indexes: `(tenant_id, entry_id, entry_version)` unique; `(tenant_id, commission_id)`; `(tenant_id, entry_timestamp DESC)`.

Application privileges: `SELECT`, `INSERT`; no `UPDATE` or `DELETE` for immutable ledger entries.

## 12. B4 infrastructure relations

### 12.1 `reos_infra.schema_migrations`

**Existing owner:** `bootstrap-migration-ledger.sql` and `PostgresMigrationRunner`.

Existing columns:

- `migration_id text NOT NULL`
- `migration_name text NOT NULL`
- `checksum text NOT NULL`
- `applied_at timestamptz NOT NULL DEFAULT clock_timestamp()`

Existing keys:

- Primary key: `migration_id`.
- Unique: `migration_name`.
- `migration_id` must match eight numeric digits.
- `migration_name` must match the migration manifest naming contract.
- `checksum` must be 64 lowercase hexadecimal characters.

Application role has no schema/table access. Do not modify this table or create another ledger.

### 12.2 `reos_infra.api_sessions`

**Existing migration:** `00000003-b4-durable-api-sessions.sql`.

Preserve its existing columns, constraints, append-only identity binding and revocation lifecycle:

- `session_id`
- `tenant_id`
- `account_id`
- `identity_id`
- `tenant_revision`
- `organization_id`
- `membership_id`
- `membership_revision`
- `issuer_digest`
- `token_id_digest`
- `authentication_epoch`
- `issued_at`
- `expires_at`
- `revoked_at`
- `revocation_reason_code`

Existing protections:

- Durable session identity is immutable.
- Revocation is irreversible.
- Delete is rejected.
- Tenant RLS is enabled and forced.
- Application role is not table owner and has no RLS bypass.
- Existing indexes and grants remain canonical.

Do not replace or duplicate the existing session store.

### 12.3 `reos_infra.security_audit_events`

**Existing migration:** `00000004-b4-minimized-security-audit.sql`.

Preserve its existing eight-column privacy-minimized structure:

- `event_id uuid`
- `event_type text`
- `request_id uuid`
- `occurred_at timestamptz`
- `reason_code text`
- `operation text`
- `actor_identity_reference uuid`
- `tenant_reference uuid`

Existing protections:

- Application role has `INSERT` only.
- Application role cannot `SELECT`, `UPDATE` or `DELETE`.
- A trigger rejects updates and deletes, including privileged mutation attempts.
- No request body, bearer token or credential fields may be added.

`00000011-b4-security-audit-tenant-write-guard.sql` must add the approved tenant-reference integrity guard against `core001.tenants(tenant_id)` after CORE-001 exists. It must not create a second audit table or weaken append-only behavior.

The security audit integration test must create a real CORE-001 tenant fixture before inserting a non-null `tenant_reference`, and must assert an unknown tenant reference is rejected by the new guard.

This table uses `tenant_reference`, not `tenant_id`; do not pretend it is already covered by the generic `PostgresRuntime` tenant-table scan.

## 13. RLS and privilege contract for every tenant-bearing relation

The following relations carry the canonical `tenant_id` column and must be included in the live runtime safety scan:

| Schema | Relations |
|---|---|
| `core001` | `tenants`, `organizations`, `memberships` |
| `core002` | `events`, `outbox_publications` |
| `core003` | `leads`, `lead_ownership`, `ownership_transfers` |
| `core004` | `projects`, `inventory` |
| `core006` | `deals`, `deal_parties` |
| `core007` | `governance_decisions`, `approval_requests` |
| `core008` | `commission_contracts`, `financial_ledger_entries` |
| `reos_infra` | `api_sessions` |

For every relation above:

1. Enable RLS.
2. Force RLS.
3. Ensure the application role is not the table owner.
4. Ensure the application role and every role it can inherit or assume do not have `BYPASSRLS`.
5. Install the canonical permissive application access policy where required.
6. Install the canonical restrictive tenant `FOR ALL` policy.
7. Require both `USING` and `WITH CHECK`.
8. Use the exact safe UUID expression already verified by `PostgresRuntime`.
9. Missing, empty or malformed tenant context must resolve to NULL and fail closed.
10. Do not create a duplicate transaction or tenant-context owner.

The existing canonical expression is derived from `postgres.ts`:

```sql
tenant_id = CASE
  WHEN pg_input_is_valid(
    current_setting('app.tenant_id', true),
    'uuid'
  )
  THEN current_setting('app.tenant_id', true)::uuid
  ELSE NULL::uuid
END
```

The application role must receive only the required schema/table privileges. It must not receive table ownership, schema creation, migration-ledger access, role creation, superuser or RLS-bypass capability.

## 14. Explicit exclusions and no-duplicate boundary

The following are deliberately not created as additional B4 schemas or tables:

- `core005` search schema. CORE-005 remains a derived read-side/search owner.
- A second identity/account registry.
- A second tenant registry.
- New role, permission, entitlement, scope or relationship tables not present in the approved B4 physical relation sequence.
- A universal customer or party identity table.
- A project/developer registry.
- A property or unit registry.
- A financial account registry.
- A second audit store.
- A second event bus or outbox.
- A second migration ledger.
- A new ORM, database client or transaction runtime.

CORE-001 external identity reference and other in-memory domain structures not present in the approved B4 migration inventory are not converted into new tables by inference. Any broader persistence requirement must be resolved against the existing approved ARCH-037 source, not invented inside B4.

## 15. Required verification and evidence mapping

| Requirement | Verification owner | Required assertion |
|---|---|---|
| Ordered migration sequence | Existing migration manifest and runner | Exact IDs `00000001`–`00000011`, exact names/checksums, no missing prefix |
| Replay integrity | Existing migration runner | Second run applies zero migrations |
| CORE relation existence | `postgres-arch037-schema.integration.test.ts` | All required relations exist |
| Column mapping | `postgres-arch037-schema.integration.test.ts` | Exact source-backed columns, PostgreSQL types, nullability and defaults |
| Primary/unique constraints | `postgres-arch037-schema.integration.test.ts` | Keys match this manifest |
| Foreign keys | `postgres-arch037-schema.integration.test.ts` | Only documented relationships exist and are validated |
| Tenant isolation | `postgres-arch037-schema.integration.test.ts` | Actual application login, tenant A/B read/write boundaries |
| Runtime role safety | Existing `PostgresRuntime` | No owner, superuser, inherited or assumable RLS bypass |
| Financial precision | `postgres-arch037-schema.integration.test.ts` | `core008.financial_ledger_entries.amount` formats as unbounded `numeric`, `typmod = -1` |
| Audit tenant reference | `postgres-security-audit.integration.test.ts` | Existing tenant accepted; unknown tenant rejected |
| Append-only audit | `postgres-security-audit.integration.test.ts` | App role cannot read/update/delete; privileged update/delete rejected |
| Session durability | Existing session integration tests | Session, expiry and revocation invariants preserved |
| Backup and restore | Existing `postgres-b4-recovery.integration.test.ts` | Actual B4 tables and security protections survive restore |
| Redis shared rate limit | Existing Redis integration test | Atomic shared counter, expiry, concurrency and fail-closed behavior |

The ARCH-037 integration test fixture must also use valid CORE-001 values. It must not insert `TEST` for enum-backed tenant fields or use JSONB for the string `quota_profile`. A provisioning tenant is suitable for the isolated RLS fixture when no owner/administrator identities are created.

The lead test source must use the canonical `LeadSourceType` value `OTHER`, not an unrecognized test-only enum value.

## 16. Implementation completion rule

This manifest does not mean B4 is complete.

B4 remains active until:

- Every migration from `00000005` through `00000011` is added to the canonical migration directory.
- The exact migration chain and checksums are verified by the existing runner.
- All physical columns, types, keys, constraints, foreign keys and indexes are verified against canonical source models.
- The actual PostgreSQL application-role RLS tests pass.
- Session, audit, Redis, concurrency and recovery tests pass.
- No duplicate schema, engine, repository or runtime has been introduced.
- Required evidence is committed and independently read back.
- The existing guarded Control Center transition accepts B4 completion.

No status in `state.json` is changed by this document.

