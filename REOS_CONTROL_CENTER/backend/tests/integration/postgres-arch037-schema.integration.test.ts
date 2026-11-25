import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import {
  createB4PostgresTestDatabase,
  type B4PostgresTestDatabase
} from "../helpers/postgres-b4-test-database.js";

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
const requiredSetting =
  process.env.HOMIO_REQUIRE_POSTGRES_INTEGRATION;

if (
  requiredSetting !== undefined &&
  requiredSetting !== "0" &&
  requiredSetting !== "1"
) {
  throw new Error(
    "HOMIO_REQUIRE_POSTGRES_INTEGRATION must be either 0 or 1."
  );
}

const integrationRequired = requiredSetting === "1";

const adminUrlConfigured =
  typeof adminUrl === "string" &&
  adminUrl.length > 0 &&
  adminUrl === adminUrl.trim();

const postgresSuite =
  integrationRequired || adminUrlConfigured
    ? describe
    : describe.skip;

const MANIFEST_URL = new URL(
  "../../../evidence/BACKEND-001/B4-physical-schema-implementation-manifest.md",
  import.meta.url
);

const EXPECTED_MIGRATION_IDS = Array.from(
  { length: 11 },
  (_, index) => String(index + 1).padStart(8, "0")
);

const OWNER_BY_SCHEMA: Readonly<Record<string, string>> = {
  core001: "CORE-001",
  core002: "CORE-002",
  core003: "CORE-003",
  core004: "CORE-004",
  core006: "CORE-006",
  core007: "CORE-007",
  core008: "CORE-008",
  reos_infra: "B4"
};

const REQUIRED_SCHEMAS = [
  "core001",
  "core002",
  "core003",
  "core004",
  "core006",
  "core007",
  "core008",
  "reos_infra"
] as const;

const REQUIRED_RELATIONS = [
  "core001.identities",
  "core001.identity_accounts",
  "core001.tenants",
  "core001.organizations",
  "core001.memberships",
  "core002.events",
  "core002.outbox_publications",
  "core003.leads",
  "core003.lead_ownership",
  "core003.ownership_transfers",
  "core004.projects",
  "core004.inventory",
  "core006.deals",
  "core006.deal_parties",
  "core007.governance_decisions",
  "core007.approval_requests",
  "core008.commission_contracts",
  "core008.financial_ledger_entries",
  "reos_infra.schema_migrations",
  "reos_infra.api_sessions",
  "reos_infra.security_audit_events"
] as const;

interface ManifestColumn {
  readonly name: string;
  readonly postgresType: string;
  readonly nullable: boolean;
  readonly defaultDescription: string;
}

type PhysicalSchemaManifest = Readonly<
  Record<string, readonly ManifestColumn[]>
>;

interface RelationRow {
  readonly relation_name: string;
  readonly exists: boolean;
}

interface ApplicationRoleRow {
  readonly oid: string;
  readonly rolcanlogin: boolean;
  readonly rolinherit: boolean;
  readonly rolsuper: boolean;
  readonly rolcreatedb: boolean;
  readonly rolcreaterole: boolean;
  readonly rolreplication: boolean;
  readonly rolbypassrls: boolean;
}

interface ApplicationIdentityRow {
  readonly session_user: string;
  readonly current_user: string;
}

interface MigrationLedgerRow {
  readonly migration_id: string;
  readonly migration_name: string;
  readonly checksum: string;
}

interface ColumnCatalogRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly column_name: string;
  readonly formatted_type: string;
  readonly nullable: boolean;
  readonly default_expression: string | null;
}

interface ConstraintCatalogRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly constraint_name: string;
  readonly constraint_type: string;
  readonly validated: boolean;
  readonly definition: string;
  readonly columns: string[];
  readonly referenced_relation: string | null;
  readonly referenced_columns: string[] | null;
}

interface IndexCatalogRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly index_name: string;
  readonly index_definition: string;
  readonly is_unique: boolean;
  readonly is_valid: boolean;
  readonly is_ready: boolean;
  readonly predicate: string | null;
}

interface RelationOwnerRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly relation_owner: string;
  readonly schema_owner: string;
}

interface TenantTableRow {
  readonly relation_oid: string;
  readonly schema_name: string;
  readonly relation_name: string;
  readonly rls_enabled: boolean;
  readonly rls_forced: boolean;
  readonly application_role_is_owner: boolean;
}

interface TenantPolicyRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly policy_name: string;
  readonly permissive: boolean;
  readonly command: string;
  readonly applies_to_application_role: boolean;
  readonly using_expression: string | null;
  readonly check_expression: string | null;
}

interface FunctionCatalogRow {
  readonly schema_name: string;
  readonly function_name: string;
  readonly function_owner: string;
  readonly security_definer: boolean;
  readonly configuration: string[] | null;
  readonly application_can_execute: boolean;
  readonly public_can_execute: boolean;
  readonly identity_arguments: string;
}

interface TriggerCatalogRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly trigger_name: string;
  readonly trigger_definition: string;
  readonly enabled: string;
  readonly internal: boolean;
}

interface FinancialTypeRow {
  readonly formatted_type: string;
  readonly typmod: number;
}

/*
 * The transaction query API requires row types to satisfy
 * Record<string, unknown>. Keep the explicit selected columns while
 * satisfying that shared query contract.
 */
interface LeadRow extends Record<string, unknown> {
  readonly tenant_id: string;
  readonly lead_id: string;
}

interface ExpectedKeyConstraint {
  readonly name: string;
  readonly relation: string;
  readonly kind: "p" | "u" | "f";
  readonly columns: readonly string[];
  readonly referencedRelation?: string;
  readonly referencedColumns?: readonly string[];
}

function primary(
  name: string,
  relation: string,
  columns: readonly string[]
): ExpectedKeyConstraint {
  return {
    name,
    relation,
    kind: "p",
    columns
  };
}

function unique(
  name: string,
  relation: string,
  columns: readonly string[]
): ExpectedKeyConstraint {
  return {
    name,
    relation,
    kind: "u",
    columns
  };
}

function foreign(
  name: string,
  relation: string,
  columns: readonly string[],
  referencedRelation: string,
  referencedColumns: readonly string[]
): ExpectedKeyConstraint {
  return {
    name,
    relation,
    kind: "f",
    columns,
    referencedRelation,
    referencedColumns
  };
}

const EXPECTED_KEY_CONSTRAINTS: readonly ExpectedKeyConstraint[] = [
  primary("identities_pkey", "core001.identities", ["identity_id"]),
  primary("identity_accounts_pkey", "core001.identity_accounts", ["account_id"]),
  primary("tenants_pkey", "core001.tenants", ["tenant_id"]),
  primary("organizations_pkey", "core001.organizations", ["organization_id"]),
  primary("memberships_pkey", "core001.memberships", ["membership_id"]),

  primary("leads_pkey", "core003.leads", ["tenant_id", "lead_id"]),
  primary("lead_ownership_pkey", "core003.lead_ownership", ["tenant_id", "lead_id"]),
  primary("ownership_transfers_pkey", "core003.ownership_transfers", ["transfer_id"]),

  primary("projects_pkey", "core004.projects", ["tenant_id", "project_id"]),
  primary("inventory_pkey", "core004.inventory", ["tenant_id", "inventory_id"]),

  primary("deals_pkey", "core006.deals", ["tenant_id", "deal_id"]),
  primary("deal_parties_pkey", "core006.deal_parties", [
    "tenant_id",
    "deal_id",
    "role",
    "party_id"
  ]),

  primary("governance_decisions_pkey", "core007.governance_decisions", [
    "tenant_id",
    "decision_id"
  ]),
  primary("approval_requests_pkey", "core007.approval_requests", [
    "tenant_id",
    "request_id"
  ]),

  primary("commission_contracts_pkey", "core008.commission_contracts", [
    "tenant_id",
    "commission_id",
    "contract_version"
  ]),
  primary("financial_ledger_entries_pkey", "core008.financial_ledger_entries", [
    "tenant_id",
    "entry_id",
    "entry_version"
  ]),

  unique("identities_handle_key", "core001.identities", ["handle"]),
  unique("tenants_slug_key", "core001.tenants", ["slug"]),
  unique("organizations_tenant_identity_key", "core001.organizations", [
    "tenant_id",
    "organization_id"
  ]),
  unique("organizations_tenant_slug_key", "core001.organizations", [
    "tenant_id",
    "slug"
  ]),
  unique("ownership_transfers_revision_key", "core003.ownership_transfers", [
    "tenant_id",
    "lead_id",
    "new_revision"
  ]),
  unique("projects_tenant_project_code_key", "core004.projects", [
    "tenant_id",
    "project_code"
  ]),

  foreign(
    "identity_accounts_identity_fk",
    "core001.identity_accounts",
    ["identity_id"],
    "core001.identities",
    ["identity_id"]
  ),
  foreign(
    "tenants_owner_identity_fk",
    "core001.tenants",
    ["owner_identity_id"],
    "core001.identities",
    ["identity_id"]
  ),
  foreign(
    "tenants_primary_admin_identity_fk",
    "core001.tenants",
    ["primary_admin_identity_id"],
    "core001.identities",
    ["identity_id"]
  ),
  foreign(
    "organizations_tenant_fk",
    "core001.organizations",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "organizations_parent_fk",
    "core001.organizations",
    ["tenant_id", "parent_organization_id"],
    "core001.organizations",
    ["tenant_id", "organization_id"]
  ),
  foreign(
    "memberships_tenant_fk",
    "core001.memberships",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "memberships_organization_fk",
    "core001.memberships",
    ["tenant_id", "organization_id"],
    "core001.organizations",
    ["tenant_id", "organization_id"]
  ),
  foreign(
    "memberships_identity_fk",
    "core001.memberships",
    ["identity_id"],
    "core001.identities",
    ["identity_id"]
  ),

  foreign(
    "leads_tenant_fk",
    "core003.leads",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "lead_ownership_lead_fk",
    "core003.lead_ownership",
    ["tenant_id", "lead_id"],
    "core003.leads",
    ["tenant_id", "lead_id"]
  ),
  foreign(
    "ownership_transfers_lead_fk",
    "core003.ownership_transfers",
    ["tenant_id", "lead_id"],
    "core003.leads",
    ["tenant_id", "lead_id"]
  ),

  foreign(
    "projects_tenant_fk",
    "core004.projects",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "inventory_tenant_fk",
    "core004.inventory",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "inventory_project_fk",
    "core004.inventory",
    ["tenant_id", "project_id"],
    "core004.projects",
    ["tenant_id", "project_id"]
  ),

  foreign(
    "deals_tenant_fk",
    "core006.deals",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "deal_parties_deal_fk",
    "core006.deal_parties",
    ["tenant_id", "deal_id"],
    "core006.deals",
    ["tenant_id", "deal_id"]
  ),

  foreign(
    "governance_decisions_tenant_fk",
    "core007.governance_decisions",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "approval_requests_tenant_fk",
    "core007.approval_requests",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),

  foreign(
    "commission_contracts_tenant_fk",
    "core008.commission_contracts",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  ),
  foreign(
    "financial_ledger_entries_tenant_fk",
    "core008.financial_ledger_entries",
    ["tenant_id"],
    "core001.tenants",
    ["tenant_id"]
  )
];

const EXPECTED_CHECK_CONSTRAINTS: Readonly<
  Record<string, readonly string[]>
> = {
  "core001.identities": [
    "identities_identity_type_check",
    "identities_display_name_check",
    "identities_handle_check",
    "identities_status_check",
    "identities_privacy_class_check",
    "identities_revision_check",
    "identities_time_order_check"
  ],
  "core001.identity_accounts": [
    "identity_accounts_status_check",
    "identity_accounts_authentication_epoch_check",
    "identity_accounts_time_order_check"
  ],
  "core001.tenants": [
    "tenants_kind_check",
    "tenants_operating_mode_check",
    "tenants_status_check",
    "tenants_isolation_profile_check",
    "tenants_residency_mode_check",
    "tenants_slug_check",
    "tenants_display_name_check",
    "tenants_quota_profile_check",
    "tenants_configuration_ref_object_check",
    "tenants_security_profile_ref_object_check",
    "tenants_region_jurisdiction_ref_check",
    "tenants_residency_scope_check",
    "tenants_active_owner_check",
    "tenants_revision_check",
    "tenants_time_order_check"
  ],
  "core001.organizations": [
    "organizations_display_name_check",
    "organizations_slug_check",
    "organizations_status_check",
    "organizations_revision_check",
    "organizations_time_order_check",
    "organizations_not_own_parent_check"
  ],
  "core001.memberships": [
    "memberships_status_check",
    "memberships_required_assurance_check",
    "memberships_attribute_constraints_array_check",
    "memberships_validity_check",
    "memberships_revision_check",
    "memberships_time_order_check"
  ],
  "core003.leads": [
    "leads_status_check",
    "leads_priority_check",
    "leads_source_type_check",
    "leads_source_id_check",
    "leads_campaign_id_check",
    "leads_channel_check",
    "leads_metadata_object_check",
    "leads_revision_check",
    "leads_time_order_check"
  ],
  "core003.lead_ownership": [
    "lead_ownership_owner_role_check",
    "lead_ownership_revision_check",
    "lead_ownership_assignment_reference_check"
  ],
  "core003.ownership_transfers": [
    "ownership_transfers_previous_owner_check",
    "ownership_transfers_previous_revision_check",
    "ownership_transfers_new_revision_check",
    "ownership_transfers_reason_check",
    "ownership_transfers_reference_check"
  ],
  "core004.projects": [
    "projects_project_id_check",
    "projects_developer_id_check",
    "projects_project_code_check",
    "projects_name_check",
    "projects_metadata_object_check"
  ],
  "core004.inventory": [
    "inventory_id_check",
    "inventory_developer_id_check",
    "inventory_project_id_check",
    "inventory_property_id_check",
    "inventory_unit_id_check",
    "inventory_type_check",
    "inventory_hierarchy_check",
    "inventory_name_check",
    "inventory_lifecycle_check",
    "inventory_availability_check",
    "inventory_time_order_check",
    "inventory_version_check",
    "inventory_metadata_object_check"
  ],
  "core006.deals": [
    "deals_deal_id_check",
    "deals_customer_id_check",
    "deals_broker_id_check",
    "deals_builder_id_check",
    "deals_project_id_check",
    "deals_unit_id_check",
    "deals_status_check",
    "deals_version_check",
    "deals_time_order_check",
    "deals_history_array_check",
    "deals_source_of_truth_check",
    "deals_offers_array_check",
    "deals_negotiation_object_check",
    "deals_milestones_array_check",
    "deals_ownership_binding_object_check",
    "deals_evidence_array_check",
    "deals_audit_log_array_check",
    "deals_contract_schema_version_check"
  ],
  "core006.deal_parties": [
    "deal_parties_role_check",
    "deal_parties_party_id_check",
    "deal_parties_relationship_version_check",
    "deal_parties_lifecycle_check",
    "deal_parties_metadata_object_check"
  ],
  "core007.governance_decisions": [
    "governance_decisions_subject_check",
    "governance_decisions_correlation_check",
    "governance_decisions_type_check",
    "governance_decisions_action_class_check",
    "governance_decisions_authority_check",
    "governance_decisions_approval_authority_check",
    "governance_decisions_escalation_level_check",
    "governance_decisions_review_state_check",
    "governance_decisions_escalation_state_check",
    "governance_decisions_schema_version_check",
    "governance_decisions_fingerprint_check"
  ],
  "core007.approval_requests": [
    "approval_requests_subject_check",
    "approval_requests_correlation_check",
    "approval_requests_state_check",
    "approval_requests_time_order_check",
    "approval_requests_decision_record_check"
  ],
  "core008.commission_contracts": [
    "commission_contracts_commission_id_check",
    "commission_contracts_entitlement_object_check",
    "commission_contracts_basis_object_check",
    "commission_contracts_rate_object_check",
    "commission_contracts_eligibility_array_check",
    "commission_contracts_provenance_object_check",
    "commission_contracts_metadata_object_check",
    "commission_contracts_effective_window_check",
    "commission_contracts_version_check",
    "commission_contracts_state_check"
  ],
  "core008.financial_ledger_entries": [
    "financial_ledger_entries_entry_id_check",
    "financial_ledger_entries_commission_id_check",
    "financial_ledger_entries_transaction_reference_check",
    "financial_ledger_entries_debit_account_id_check",
    "financial_ledger_entries_debit_account_type_check",
    "financial_ledger_entries_credit_account_id_check",
    "financial_ledger_entries_credit_account_type_check",
    "financial_ledger_entries_distinct_accounts_check",
    "financial_ledger_entries_version_check",
    "financial_ledger_entries_amount_finite_check",
    "financial_ledger_entries_currency_code_check",
    "financial_ledger_entries_currency_minor_unit_check",
    "financial_ledger_entries_rounding_mode_check",
    "financial_ledger_entries_currency_precision_check",
    "financial_ledger_entries_source_reference_check",
    "financial_ledger_entries_provenance_reference_check",
    "financial_ledger_entries_metadata_object_check"
  ]
};

interface ExpectedIndex {
  readonly name: string;
  readonly relation: string;
  readonly keys: readonly string[];
}

const EXPECTED_INDEXES: readonly ExpectedIndex[] = [
  {
    name: "identity_accounts_identity_idx",
    relation: "core001.identity_accounts",
    keys: ["identity_id"]
  },
  {
    name: "organizations_tenant_parent_idx",
    relation: "core001.organizations",
    keys: ["tenant_id", "parent_organization_id"]
  },
  {
    name: "memberships_tenant_identity_idx",
    relation: "core001.memberships",
    keys: ["tenant_id", "identity_id"]
  },
  {
    name: "memberships_tenant_organization_idx",
    relation: "core001.memberships",
    keys: ["tenant_id", "organization_id"]
  },
  {
    name: "leads_tenant_status_created_idx",
    relation: "core003.leads",
    keys: ["tenant_id", "status", "created_at DESC"]
  },
  {
    name: "leads_tenant_customer_created_idx",
    relation: "core003.leads",
    keys: ["tenant_id", "customer_id", "created_at DESC"]
  },
  {
    name: "lead_ownership_tenant_owner_assigned_idx",
    relation: "core003.lead_ownership",
    keys: ["tenant_id", "owner_id", "assigned_at DESC"]
  },
  {
    name: "ownership_transfers_tenant_time_idx",
    relation: "core003.ownership_transfers",
    keys: ["tenant_id", "transferred_at DESC", "transfer_id"]
  },
  {
    name: "projects_tenant_developer_idx",
    relation: "core004.projects",
    keys: ["tenant_id", "developer_id"]
  },
  {
    name: "inventory_tenant_project_type_idx",
    relation: "core004.inventory",
    keys: ["tenant_id", "project_id", "inventory_type"]
  },
  {
    name: "inventory_tenant_lifecycle_availability_idx",
    relation: "core004.inventory",
    keys: ["tenant_id", "lifecycle", "availability"]
  },
  {
    name: "deals_tenant_status_updated_idx",
    relation: "core006.deals",
    keys: ["tenant_id", "status", "updated_at DESC"]
  },
  {
    name: "deals_tenant_customer_idx",
    relation: "core006.deals",
    keys: ["tenant_id", "customer_id"]
  },
  {
    name: "deals_tenant_broker_idx",
    relation: "core006.deals",
    keys: ["tenant_id", "broker_id"]
  },
  {
    name: "deal_parties_tenant_party_idx",
    relation: "core006.deal_parties",
    keys: ["tenant_id", "party_id"]
  },
  {
    name: "governance_decisions_tenant_subject_time_idx",
    relation: "core007.governance_decisions",
    keys: ["tenant_id", "subject_id", "decided_at DESC"]
  },
  {
    name: "governance_decisions_tenant_time_idx",
    relation: "core007.governance_decisions",
    keys: ["tenant_id", "decided_at DESC"]
  },
  {
    name: "approval_requests_tenant_state_expiry_idx",
    relation: "core007.approval_requests",
    keys: ["tenant_id", "state", "expires_at"]
  },
  {
    name: "commission_contracts_tenant_state_effective_idx",
    relation: "core008.commission_contracts",
    keys: ["tenant_id", "state", "effective_from DESC"]
  },
  {
    name: "financial_ledger_entries_tenant_commission_time_idx",
    relation: "core008.financial_ledger_entries",
    keys: ["tenant_id", "commission_id", "entry_timestamp DESC"]
  },
  {
    name: "financial_ledger_entries_tenant_time_idx",
    relation: "core008.financial_ledger_entries",
    keys: ["tenant_id", "entry_timestamp DESC", "entry_id"]
  }
];

interface ExpectedFunction {
  readonly schema: string;
  readonly name: string;
  readonly securityDefiner: boolean;
  readonly applicationCanExecute: boolean;
  readonly searchPath: string | null;
}

const EXPECTED_FUNCTIONS: readonly ExpectedFunction[] = [
  {
    schema: "core003",
    name: "reject_ownership_transfer_mutation",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: null
  },
  {
    schema: "core007",
    name: "reject_governance_decision_mutation",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: null
  },
  {
    schema: "core007",
    name: "guard_approval_request_mutation",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: null
  },
  {
    schema: "core008",
    name: "reject_commission_contract_mutation",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: null
  },
  {
    schema: "core008",
    name: "reject_financial_ledger_mutation",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: null
  },
  {
    schema: "reos_infra",
    name: "enforce_security_audit_tenant_context",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: "search_path=pg_catalog"
  },
  {
    schema: "reos_infra",
    name: "reject_security_audit_mutation",
    securityDefiner: false,
    applicationCanExecute: false,
    searchPath: null
  },
  {
    schema: "reos_infra",
    name: "append_security_audit_event",
    securityDefiner: true,
    applicationCanExecute: true,
    searchPath: "search_path=pg_catalog"
  }
];

interface ExpectedTrigger {
  readonly schema: string;
  readonly relation: string;
  readonly name: string;
  readonly definition: string;
}

const EXPECTED_TRIGGERS: readonly ExpectedTrigger[] = [
  {
    schema: "core003",
    relation: "ownership_transfers",
    name: "ownership_transfers_append_only",
    definition:
      "CREATE TRIGGER ownership_transfers_append_only BEFORE UPDATE OR DELETE ON core003.ownership_transfers FOR EACH ROW EXECUTE FUNCTION core003.reject_ownership_transfer_mutation()"
  },
  {
    schema: "core007",
    relation: "governance_decisions",
    name: "governance_decisions_immutable",
    definition:
      "CREATE TRIGGER governance_decisions_immutable BEFORE UPDATE OR DELETE ON core007.governance_decisions FOR EACH ROW EXECUTE FUNCTION core007.reject_governance_decision_mutation()"
  },
  {
    schema: "core007",
    relation: "approval_requests",
    name: "approval_requests_state_guard",
    definition:
      "CREATE TRIGGER approval_requests_state_guard BEFORE UPDATE OR DELETE ON core007.approval_requests FOR EACH ROW EXECUTE FUNCTION core007.guard_approval_request_mutation()"
  },
  {
    schema: "core008",
    relation: "commission_contracts",
    name: "commission_contracts_immutable",
    definition:
      "CREATE TRIGGER commission_contracts_immutable BEFORE UPDATE OR DELETE ON core008.commission_contracts FOR EACH ROW EXECUTE FUNCTION core008.reject_commission_contract_mutation()"
  },
  {
    schema: "core008",
    relation: "financial_ledger_entries",
    name: "financial_ledger_entries_append_only",
    definition:
      "CREATE TRIGGER financial_ledger_entries_append_only BEFORE UPDATE OR DELETE ON core008.financial_ledger_entries FOR EACH ROW EXECUTE FUNCTION core008.reject_financial_ledger_mutation()"
  },
  {
    schema: "reos_infra",
    relation: "security_audit_events",
    name: "security_audit_events_tenant_context_guard",
    definition:
      "CREATE TRIGGER security_audit_events_tenant_context_guard BEFORE INSERT ON reos_infra.security_audit_events FOR EACH ROW EXECUTE FUNCTION reos_infra.enforce_security_audit_tenant_context()"
  },
  {
    schema: "reos_infra",
    relation: "security_audit_events",
    name: "security_audit_events_truncate_guard",
    definition:
      "CREATE TRIGGER security_audit_events_truncate_guard BEFORE TRUNCATE ON reos_infra.security_audit_events FOR EACH STATEMENT EXECUTE FUNCTION reos_infra.reject_security_audit_mutation()"
  }
];

const TENANT_SCOPED_UNIQUE_RELATIONS = [
  "core001.organizations",
  "core003.leads",
  "core003.lead_ownership",
  "core003.ownership_transfers",
  "core004.projects",
  "core004.inventory",
  "core006.deals",
  "core006.deal_parties",
  "core007.governance_decisions",
  "core007.approval_requests",
  "core008.commission_contracts",
  "core008.financial_ledger_entries"
] as const;

function normalizeSql(value: string): string {
  return value
    .replaceAll('"', "")
    .replace(/\s+/g, " ")
    .replace(/\s*([(),.])\s*/g, "$1")
    .trim()
    .toLowerCase();
}

function normalizeTriggerDefinition(value: string): string {
  return normalizeSql(value).replace(
    "before update or delete",
    "before delete or update"
  );
}

function stripMarkdownCell(value: string): string {
  const cell = value.trim();

  if (
    cell.length >= 2 &&
    cell.startsWith("`") &&
    cell.endsWith("`")
  ) {
    return cell.slice(1, -1);
  }

  return cell;
}

function parsePhysicalSchemaManifest(
  content: string
): PhysicalSchemaManifest {
  const headings = Array.from(
    content.matchAll(/^#### `([^`]+)`\s*$/gm)
  );

  const result: Record = DIL1;
        await current.adminPool.query<MigrationLedgerRow>(
          `
            SELECT
              migration_id,
              migration_name,
              checksum
            FROM reos_infra.schema_migrations
            ORDER BY migration_id
          `
        );

      expect(ledger.rows).toEqual(
        current.migrationHistory.map((migration) => ({
          migration_id: migration.id,
          migration_name: migration.name,
          checksum: migration.checksum
        }))
      );

      await expect(
        current.applicationPool.query(
          `
            SELECT migration_id
            FROM reos_infra.schema_migrations
          `
        )
      ).rejects.toMatchObject({
        code: "42501"
      });
    });

    it("creates exactly the approved canonical relations without a duplicate CORE-005 SQL schema", async () => {
      const current = requireDatabase();

      const result =
        await current.adminPool.query<RelationRow>(
          `
            SELECT
              required.relation_name,
              to_regclass(required.relation_name) IS NOT NULL AS exists
            FROM unnest($1::text[]) AS required(relation_name)
            ORDER BY required.relation_name
          `,
          [[...REQUIRED_RELATIONS]]
        );

      expect(result.rows).toHaveLength(REQUIRED_RELATIONS.length);

      for (const row of result.rows) {
        expect(
          row.exists,
          `Missing required relation ${row.relation_name}; owner ${expectedOwner(row.relation_name)}`
        ).toBe(true);
      }

      const schemas = await current.adminPool.query<{
        readonly schema_name: string;
      }>(
        `
          SELECT nspname AS schema_name
          FROM pg_catalog.pg_namespace
          WHERE nspname ~ '^core[0-9]{3}$'
             OR nspname = 'reos_infra'
          ORDER BY nspname
        `
      );

      expect(
        schemas.rows.map((row) => row.schema_name)
      ).toEqual([...REQUIRED_SCHEMAS].sort());

      const duplicateRelations =
        await current.adminPool.query<{
          readonly relation_name: string;
          readonly schemas: string[];
        }>(
          `
            SELECT
              relation.relname AS relation_name,
              array_agg(namespace.nspname ORDER BY namespace.nspname)
                AS schemas
            FROM pg_catalog.pg_class AS relation
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relkind IN ('r', 'p', 'v', 'm')
              AND relation.relname = ANY($1::text[])
            GROUP BY relation.relname
            HAVING count(*) > 1
            ORDER BY relation.relname
          `,
          [[
            ...REQUIRED_RELATIONS.map(
              (relation) => relation.split(".")[1] ?? ""
            )
          ]]
        );

      expect(
        duplicateRelations.rows,
        "Canonical relation names must not be duplicated in alternate schemas."
      ).toEqual([]);
    });

    it("matches the physical CORE columns, PostgreSQL types, nullability and declared defaults", async () => {
      const current = requireDatabase();

      const relations = Object.keys(physicalManifest);
      const schemas = [
        ...new Set(relations.map((relation) => relation.split(".")[0] ?? ""))
      ];
      const relationNames = relations.map(
        (relation) => relation.split(".")[1] ?? ""
      );

      const result =
        await current.adminPool.query<ColumnCatalogRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              attribute.attname AS column_name,
              pg_catalog.format_type(
                attribute.atttypid,
                attribute.atttypmod
              ) AS formatted_type,
              NOT attribute.attnotnull AS nullable,
              pg_catalog.pg_get_expr(
                default_value.adbin,
                default_value.adrelid
              ) AS default_expression
            FROM pg_catalog.pg_attribute AS attribute
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = attribute.attrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            LEFT JOIN pg_catalog.pg_attrdef AS default_value
              ON default_value.adrelid = attribute.attrelid
             AND default_value.adnum = attribute.attnum
            WHERE namespace.nspname = ANY($1::text[])
              AND relation.relname = ANY($2::text[])
              AND relation.relkind IN ('r', 'p')
              AND attribute.attnum > 0
              AND attribute.attisdropped = false
            ORDER BY
              namespace.nspname,
              relation.relname,
              attribute.attnum
          `,
          [schemas, relationNames]
        );

      const expectedColumnCount = Object.values(physicalManifest)
        .reduce((total, columns) => total + columns.length, 0);

      expect(result.rows).toHaveLength(expectedColumnCount);

      const actualByRelation = new Map<
        string,
        Map<string, ColumnCatalogRow>
      >();

      for (const row of result.rows) {
        const relation =
          `${row.schema_name}.${row.relation_name}`;

        let columns = actualByRelation.get(relation);

        if (columns === undefined) {
          columns = new Map();
          actualByRelation.set(relation, columns);
        }

        columns.set(row.column_name, row);
      }

      for (const [relation, expectedColumns] of Object.entries(
        physicalManifest
      )) {
        const owner = expectedOwner(relation);
        const actualColumns = actualByRelation.get(relation);

        expect(
          actualColumns,
          `${owner} ${relation}: relation column catalog must exist.`
        ).toBeDefined();

        expect(
          [...(actualColumns?.keys() ?? [])].sort(),
          `${owner} ${relation}: actual columns must exactly match the traceability mapping.`
        ).toEqual(
          expectedColumns.map((column) => column.name).sort()
        );

        for (const expected of expectedColumns) {
          const actual = actualColumns?.get(expected.name);

          expect(
            actual,
            `${owner} ${relation}.${expected.name}: column must exist.`
          ).toBeDefined();

          if (actual === undefined) {
            continue;
          }

          const expectedType = postgresTypeName(
            expected.postgresType
          );

          expect(
            actual.formatted_type,
            `${owner} ${relation}.${expected.name}: expected type ${expectedType}, actual ${actual.formatted_type}.`
          ).toBe(expectedType);

          expect(
            actual.nullable,
            `${owner} ${relation}.${expected.name}: expected nullable=${expected.nullable}, actual nullable=${actual.nullable}.`
          ).toBe(expected.nullable);

          expect(
            defaultMatchesManifest(expected, actual.default_expression),
            `${owner} ${relation}.${expected.name}: default declaration mismatch; expected ${expected.defaultDescription}, actual ${actual.default_expression ?? "NULL"}.`
          ).toBe(true);
        }
      }
    });

    it("verifies exact primary keys, unique constraints, foreign-key targets and validated checks", async () => {
      const current = requireDatabase();

      const relations = Object.keys(EXPECTED_CHECK_CONSTRAINTS);

      const result =
        await current.adminPool.query<ConstraintCatalogRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              constraint_row.conname AS constraint_name,
              constraint_row.contype::text AS constraint_type,
              constraint_row.convalidated AS validated,
              pg_catalog.pg_get_constraintdef(
                constraint_row.oid,
                true
              ) AS definition,
              ARRAY(
                SELECT attribute.attname::text
                FROM unnest(constraint_row.conkey)
                  WITH ORDINALITY AS key_column(attnum, ordinality)
                JOIN pg_catalog.pg_attribute AS attribute
                  ON attribute.attrelid = constraint_row.conrelid
                 AND attribute.attnum = key_column.attnum
                ORDER BY key_column.ordinality
              ) AS columns,
              CASE
                WHEN constraint_row.contype = 'f'
                THEN referenced_namespace.nspname
                  || '.'
                  || referenced_relation.relname
                ELSE NULL
              END AS referenced_relation,
              CASE
                WHEN constraint_row.contype = 'f'
                THEN ARRAY(
                  SELECT referenced_attribute.attname::text
                  FROM unnest(constraint_row.confkey)
                    WITH ORDINALITY AS referenced_key(attnum, ordinality)
                  JOIN pg_catalog.pg_attribute AS referenced_attribute
                    ON referenced_attribute.attrelid =
                      constraint_row.confrelid
                   AND referenced_attribute.attnum =
                      referenced_key.attnum
                  ORDER BY referenced_key.ordinality
                )
                ELSE NULL
              END AS referenced_columns
            FROM unnest($1::text[]) AS expected(qualified_name)
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = to_regclass(expected.qualified_name)
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            JOIN pg_catalog.pg_constraint AS constraint_row
              ON constraint_row.conrelid = relation.oid
             AND constraint_row.contype IN ('p', 'u', 'f', 'c')
            LEFT JOIN pg_catalog.pg_class AS referenced_relation
              ON referenced_relation.oid = constraint_row.confrelid
            LEFT JOIN pg_catalog.pg_namespace AS referenced_namespace
              ON referenced_namespace.oid =
                referenced_relation.relnamespace
            ORDER BY
              namespace.nspname,
              relation.relname,
              constraint_row.conname
          `,
          [relations]
        );

      const expectedChecks = Object.values(
        EXPECTED_CHECK_CONSTRAINTS
      ).flat();

      const expectedNames = [
        ...EXPECTED_KEY_CONSTRAINTS.map((constraint) => constraint.name),
        ...expectedChecks
      ].sort();

      expect(
        result.rows.map((row) => row.constraint_name).sort(),
        "Missing or unexpected canonical constraints were found."
      ).toEqual(expectedNames);

      const actualByName = new Map(
        result.rows.map((row) => [row.constraint_name, row])
      );

      for (const row of result.rows) {
        expect(
          row.validated,
          `${row.schema_name}.${row.relation_name}.${row.constraint_name}: constraint must be validated; actual definition ${row.definition}.`
        ).toBe(true);
      }

      for (const expected of EXPECTED_KEY_CONSTRAINTS) {
        const actual = actualByName.get(expected.name);

        expect(
          actual,
          `${expected.relation}.${expected.name}: required key constraint is missing.`
        ).toBeDefined();

        if (actual === undefined) {
          continue;
        }

        expect(
          actual.constraint_type,
          `${expected.relation}.${expected.name}: constraint type mismatch.`
        ).toBe(expected.kind);

        expect(
          actual.columns,
          `${expected.relation}.${expected.name}: expected columns ${expected.columns.join(", ")}, actual ${actual.columns.join(", ")}.`
        ).toEqual([...expected.columns]);

        if (expected.kind === "f") {
          expect(
            actual.referenced_relation,
            `${expected.relation}.${expected.name}: foreign-key target mismatch.`
          ).toBe(expected.referencedRelation);

          expect(
            actual.referenced_columns,
            `${expected.relation}.${expected.name}: referenced columns mismatch.`
          ).toEqual([...(expected.referencedColumns ?? [])]);
        }
      }

      const tenantScopedConstraints = EXPECTED_KEY_CONSTRAINTS.filter(
        (constraint) =>
          TENANT_SCOPED_UNIQUE_RELATIONS.includes(
            constraint.relation as (typeof TENANT_SCOPED_UNIQUE_RELATIONS)[number]
          ) &&
          (constraint.kind === "p" || constraint.kind === "u")
      );

      for (const relation of TENANT_SCOPED_UNIQUE_RELATIONS) {
        const tenantScopedKey = tenantScopedConstraints.some(
          (constraint) =>
            constraint.relation === relation &&
            constraint.columns[0] === "tenant_id"
        );

        expect(
          tenantScopedKey,
          `${expectedOwner(relation)} ${relation}: tenant-scoped unique key must begin with tenant_id.`
        ).toBe(true);
      }

      const semanticCheckMarkers: Readonly<
        Record<string, readonly string[]>
      > = {
        tenants_active_owner_check: [
          "owner_identity_id",
          "primary_admin_identity_id"
        ],
        inventory_hierarchy_check: [
          "inventory_type",
          "property_id",
          "unit_id"
        ],
        ownership_transfers_new_revision_check: [
          "new_revision",
          "previous_revision"
        ],
        approval_requests_time_order_check: [
          "expires_at",
          "requested_at"
        ],
        financial_ledger_entries_amount_finite_check: [
          "amount",
          "nan",
          "infinity"
        ],
        financial_ledger_entries_currency_precision_check: [
          "round",
          "amount",
          "currency_minor_unit"
        ]
      };

      for (const [constraintName, markers] of Object.entries(
        semanticCheckMarkers
      )) {
        const actual = actualByName.get(constraintName);

        expect(
          actual,
          `Required semantic check ${constraintName} is missing.`
        ).toBeDefined();

        if (actual === undefined) {
          continue;
        }

        const definition = normalizeSql(actual.definition);

        for (const marker of markers) {
          expect(
            definition,
            `${actual.schema_name}.${actual.relation_name}.${constraintName}: expected expression marker ${marker}; actual ${actual.definition}.`
          ).toContain(marker);
        }
      }
    });

    it("verifies required index definitions, key order, validity and absence of unexpected predicates", async () => {
      const current = requireDatabase();

      const expectedNames = EXPECTED_INDEXES.map(
        (index) => index.name
      );

      const result =
        await current.adminPool.query<IndexCatalogRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              index_relation.relname AS index_name,
              pg_catalog.pg_get_indexdef(index_row.indexrelid)
                AS index_definition,
              index_row.indisunique AS is_unique,
              index_row.indisvalid AS is_valid,
              index_row.indisready AS is_ready,
              pg_catalog.pg_get_expr(
                index_row.indpred,
                index_row.indrelid
              ) AS predicate
            FROM pg_catalog.pg_index AS index_row
            JOIN pg_catalog.pg_class AS index_relation
              ON index_relation.oid = index_row.indexrelid
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = index_row.indrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE index_relation.relname = ANY($1::text[])
              AND namespace.nspname = ANY($2::text[])
            ORDER BY index_relation.relname
          `,
          [
            expectedNames,
            [...REQUIRED_SCHEMAS]
          ]
        );

      expect(
        result.rows.map((row) => row.index_name).sort()
      ).toEqual([...expectedNames].sort());

      const actualByName = new Map(
        result.rows.map((row) => [row.index_name, row])
      );

      for (const expected of EXPECTED_INDEXES) {
        const actual = actualByName.get(expected.name);

        expect(
          actual,
          `${expected.relation}.${expected.name}: required index is missing.`
        ).toBeDefined();

        if (actual === undefined) {
          continue;
        }

        const owner = expectedOwner(expected.relation);
        const expectedDefinition = expectedIndexDefinition(expected);

        expect(
          actual.relation_name,
          `${owner} ${expected.relation}.${expected.name}: index relation mismatch.`
        ).toBe(expected.relation.split(".")[1]);

        expect(
          normalizeSql(actual.index_definition),
          `${owner} ${expected.relation}.${expected.name}: expected ${expectedDefinition}; actual ${actual.index_definition}.`
        ).toBe(normalizeSql(expectedDefinition));

        expect(
          actual.is_unique,
          `${expected.name}: this declared access-path index must not be unexpectedly unique.`
        ).toBe(false);

        expect(
          actual.is_valid,
          `${expected.name}: index must be valid.`
        ).toBe(true);

        expect(
          actual.is_ready,
          `${expected.name}: index must be ready.`
        ).toBe(true);

        expect(
          actual.predicate,
          `${expected.name}: an unexpected partial-index predicate was found.`
        ).toBeNull();
      }
    });

    it("keeps every managed relation and schema owned by the migration owner, not the application role", async () => {
      const current = requireDatabase();

      const relations =
        await current.adminPool.query<RelationOwnerRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              pg_catalog.pg_get_userbyid(relation.relowner)
                AS relation_owner,
              pg_catalog.pg_get_userbyid(namespace.nspowner)
                AS schema_owner
            FROM unnest($1::text[]) AS expected(qualified_name)
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = to_regclass(expected.qualified_name)
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            ORDER BY namespace.nspname, relation.relname
          `,
          [[...REQUIRED_RELATIONS]]
        );

      expect(relations.rows).toHaveLength(REQUIRED_RELATIONS.length);

      const migrationOwner =
        relations.rows.find(
          (row) =>
            `${row.schema_name}.${row.relation_name}` ===
            "core001.identities"
        )?.relation_owner;

      expect(
        migrationOwner,
        "The migration owner must be discoverable from a canonical managed relation."
      ).toBeDefined();

      for (const row of relations.rows) {
        const relation = `${row.schema_name}.${row.relation_name}`;
        const owner = expectedOwner(relation);

        expect(
          row.relation_owner,
          `${owner} ${relation}: expected the single migration owner, actual ${row.relation_owner}.`
        ).toBe(migrationOwner);

        expect(
          row.relation_owner,
          `${owner} ${relation}: the application role must not own the table.`
        ).not.toBe(current.applicationRole);

        expect(
          row.schema_owner,
          `${owner} schema ${row.schema_name}: schema owner must match the migration owner.`
        ).toBe(migrationOwner);
      }

      const schemaOwners =
        await current.adminPool.query<{
          readonly schema_name: string;
          readonly schema_owner: string;
        }>(
          `
            SELECT
              nspname AS schema_name,
              pg_catalog.pg_get_userbyid(nspowner) AS schema_owner
            FROM pg_catalog.pg_namespace
            WHERE nspname = ANY($1::text[])
            ORDER BY nspname
          `,
          [[...REQUIRED_SCHEMAS]]
        );

      expect(schemaOwners.rows).toHaveLength(REQUIRED_SCHEMAS.length);

      for (const row of schemaOwners.rows) {
        expect(
          row.schema_owner,
          `Schema ${row.schema_name} must be owned by the migration role.`
        ).toBe(migrationOwner);
      }
    });

    it("verifies function ownership, SECURITY DEFINER boundaries and exact execution grants", async () => {
      const current = requireDatabase();

      const functionNames = EXPECTED_FUNCTIONS.map(
        (fn) => fn.name
      );

      const functionSchemas = [
        ...new Set(EXPECTED_FUNCTIONS.map((fn) => fn.schema))
      ];

      const migrationOwner =
        await current.adminPool.query<{
          readonly owner: string;
        }>(
          `
            SELECT pg_catalog.pg_get_userbyid(relation.relowner) AS owner
            FROM pg_catalog.pg_class AS relation
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE namespace.nspname = 'core001'
              AND relation.relname = 'identities'
          `
        );

      const expectedMigrationOwner = migrationOwner.rows[0]?.owner;

      expect(expectedMigrationOwner).toBeDefined();

      const result =
        await current.adminPool.query<FunctionCatalogRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              procedure.proname AS function_name,
              pg_catalog.pg_get_userbyid(procedure.proowner)
                AS function_owner,
              procedure.prosecdef AS security_definer,
              procedure.proconfig AS configuration,
              pg_catalog.has_function_privilege(
                $1,
                procedure.oid,
                'EXECUTE'
              ) AS application_can_execute,
              EXISTS (
                SELECT 1
                FROM pg_catalog.aclexplode(
                  COALESCE(
                    procedure.proacl,
                    pg_catalog.acldefault(
                      'f',
                      procedure.proowner
                    )
                  )
                ) AS acl
                WHERE acl.grantee = 0
                  AND acl.privilege_type = 'EXECUTE'
              ) AS public_can_execute,
              pg_catalog.pg_get_function_identity_arguments(
                procedure.oid
              ) AS identity_arguments
            FROM pg_catalog.pg_proc AS procedure
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = procedure.pronamespace
            WHERE procedure.proname = ANY($2::text[])
              AND namespace.nspname = ANY($3::text[])
            ORDER BY namespace.nspname, procedure.proname
          `,
          [
            current.applicationRole,
            functionNames,
            functionSchemas
          ]
        );

      expect(result.rows).toHaveLength(EXPECTED_FUNCTIONS.length);

      const actualByName = new Map(
        result.rows.map((row) => [
          `${row.schema_name}.${row.function_name}`,
          row
        ])
      );

      for (const expected of EXPECTED_FUNCTIONS) {
        const qualifiedName =
          `${expected.schema}.${expected.name}`;

        const actual = actualByName.get(qualifiedName);

        expect(
          actual,
          `${qualifiedName}: required function is missing.`
        ).toBeDefined();

        if (actual === undefined) {
          continue;
        }

        expect(
          actual.function_owner,
          `${qualifiedName}: function owner must be the migration role.`
        ).toBe(expectedMigrationOwner);

        expect(
          actual.security_definer,
          `${qualifiedName}: SECURITY DEFINER status mismatch.`
        ).toBe(expected.securityDefiner);

        expect(
          actual.application_can_execute,
          `${qualifiedName}: application execution grant mismatch.`
        ).toBe(expected.applicationCanExecute);

        expect(
          actual.public_can_execute,
          `${qualifiedName}: PUBLIC must not have EXECUTE.`
        ).toBe(false);

        if (expected.searchPath !== null) {
          expect(
            actual.configuration,
            `${qualifiedName}: function search_path must be pinned.`
          ).toContain(expected.searchPath);
        }
      }

      const appendFunction = actualByName.get(
        "reos_infra.append_security_audit_event"
      );

      expect(appendFunction).toBeDefined();

      if (appendFunction !== undefined) {
        expect(
          normalizeSql(appendFunction.identity_arguments)
        ).toBe(
          normalizeSql(
            [
              "p_event_id uuid",
              "p_event_type text",
              "p_request_id uuid",
              "p_occurred_at timestamp with time zone",
              "p_reason_code text",
              "p_operation text",
              "p_actor_identity_reference uuid",
              "p_tenant_reference uuid"
            ].join(", ")
          )
        );
      }
    });

    it("verifies immutable and audit trigger definitions and enabled state", async () => {
      const current = requireDatabase();

      const expectedTriggerNames = EXPECTED_TRIGGERS.map(
        (trigger) => trigger.name
      );

      const result =
        await current.adminPool.query<TriggerCatalogRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              trigger_row.tgname AS trigger_name,
              pg_catalog.pg_get_triggerdef(
                trigger_row.oid,
                true
              ) AS trigger_definition,
              trigger_row.tgenabled AS enabled,
              trigger_row.tgisinternal AS internal
            FROM pg_catalog.pg_trigger AS trigger_row
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = trigger_row.tgrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE trigger_row.tgname = ANY($1::text[])
              AND namespace.nspname = ANY($2::text[])
            ORDER BY namespace.nspname, trigger_row.tgname
          `,
          [
            expectedTriggerNames,
            [...REQUIRED_SCHEMAS]
          ]
        );

      expect(
        result.rows.map((row) => row.trigger_name).sort()
      ).toEqual([...expectedTriggerNames].sort());

      const actualByName = new Map(
        result.rows.map((row) => [row.trigger_name, row])
      );

      for (const expected of EXPECTED_TRIGGERS) {
        const actual = actualByName.get(expected.name);
        const qualifiedRelation =
          `${expected.schema}.${expected.relation}`;

        expect(
          actual,
          `${qualifiedRelation}.${expected.name}: trigger is missing.`
        ).toBeDefined();

        if (actual === undefined) {
          continue;
        }

        expect(
          `${actual.schema_name}.${actual.relation_name}`
        ).toBe(qualifiedRelation);

        expect(
          normalizeTriggerDefinition(actual.trigger_definition),
          `${qualifiedRelation}.${expected.name}: trigger definition mismatch; actual ${actual.trigger_definition}.`
        ).toBe(normalizeTriggerDefinition(expected.definition));

        expect(
          actual.enabled,
          `${qualifiedRelation}.${expected.name}: trigger must be enabled in normal operation.`
        ).toBe("O");

        expect(
          actual.internal,
          `${qualifiedRelation}.${expected.name}: expected a user-defined trigger.`
        ).toBe(false);
      }
    });

    it("enforces actual application-role FORCE RLS and the fail-closed tenant policy", async () => {
      const current = requireDatabase();

      const roleResult =
        await current.adminPool.query<ApplicationRoleRow>(
          `
            SELECT
              oid::text AS oid,
              rolcanlogin,
              rolinherit,
              rolsuper,
              rolcreatedb,
              rolcreaterole,
              rolreplication,
              rolbypassrls
            FROM pg_catalog.pg_roles
            WHERE rolname = $1
          `,
          [current.applicationRole]
        );

      expect(roleResult.rows).toHaveLength(1);

      const role = roleResult.rows[0];

      if (role === undefined) {
        throw new Error(
          "The generated PostgreSQL application role was not returned."
        );
      }

      expect(role.rolcanlogin).toBe(true);
      expect(role.rolinherit).toBe(true);
      expect(role.rolsuper).toBe(false);
      expect(role.rolcreatedb).toBe(false);
      expect(role.rolcreaterole).toBe(false);
      expect(role.rolreplication).toBe(false);
      expect(role.rolbypassrls).toBe(false);

      const tenantTables =
        await current.adminPool.query<TenantTableRow>(
          `
            SELECT
              relation.oid::text AS relation_oid,
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              relation.relrowsecurity AS rls_enabled,
              relation.relforcerowsecurity AS rls_forced,
              relation.relowner = $1::oid
                AS application_role_is_owner
            FROM pg_catalog.pg_class AS relation
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relkind IN ('r', 'p')
              AND namespace.nspname = ANY($2::text[])
              AND EXISTS (
                SELECT 1
                FROM pg_catalog.pg_attribute AS attribute
                WHERE attribute.attrelid = relation.oid
                  AND attribute.attname = 'tenant_id'
                  AND attribute.attnum > 0
                  AND attribute.attisdropped = false
              )
            ORDER BY namespace.nspname, relation.relname
          `,
          [
            role.oid,
            [...REQUIRED_SCHEMAS]
          ]
        );

      expect(
        tenantTables.rows.length,
        "The canonical schema must contain tenant-bearing tables."
      ).toBeGreaterThan(0);

      const tenantPolicies =
        await current.adminPool.query<TenantPolicyRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              policy.polname AS policy_name,
              policy.polpermissive AS permissive,
              policy.polcmd AS command,
              (
                $1::oid = ANY(policy.polroles)
                OR 0::oid = ANY(policy.polroles)
              ) AS applies_to_application_role,
              pg_catalog.pg_get_expr(
                policy.polqual,
                policy.polrelid
              ) AS using_expression,
              pg_catalog.pg_get_expr(
                policy.polwithcheck,
                policy.polrelid
              ) AS check_expression
            FROM pg_catalog.pg_policy AS policy
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = policy.polrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.oid = ANY($2::oid[])
            ORDER BY
              namespace.nspname,
              relation.relname,
              policy.polname
          `,
          [
            role.oid,
            tenantTables.rows.map((row) => row.relation_oid)
          ]
        );

      for (const relation of tenantTables.rows) {
        const qualifiedName =
          `${relation.schema_name}.${relation.relation_name}`;
        const owner = expectedOwner(qualifiedName);

        expect(
          relation.rls_enabled,
          `${owner} ${qualifiedName}: ENABLE ROW LEVEL SECURITY is required.`
        ).toBe(true);

        expect(
          relation.rls_forced,
          `${owner} ${qualifiedName}: FORCE ROW LEVEL SECURITY is required.`
        ).toBe(true);

        expect(
          relation.application_role_is_owner,
          `${owner} ${qualifiedName}: application role must not own the table.`
        ).toBe(false);

        const policies = tenantPolicies.rows.filter(
          (policy) =>
            policy.schema_name === relation.schema_name &&
            policy.relation_name === relation.relation_name &&
            policy.applies_to_application_role
        );

        const restrictivePolicies = policies.filter(
          (policy) =>
            !policy.permissive &&
            policy.command === "*"
        );

        expect(
          restrictivePolicies,
          `${owner} ${qualifiedName}: exactly one applicable restrictive FOR ALL tenant policy is required.`
        ).toHaveLength(1);

        const tenantPolicy = restrictivePolicies[0];

        if (tenantPolicy === undefined) {
          continue;
        }

        expect(
          tenantPolicy.using_expression,
          `${qualifiedName}: USING expression must exist.`
        ).not.toBeNull();

        expect(
          tenantPolicy.check_expression,
          `${qualifiedName}: WITH CHECK expression must exist.`
        ).not.toBeNull();

        if (
          tenantPolicy.using_expression === null ||
          tenantPolicy.check_expression === null
        ) {
          continue;
        }

        const usingExpression = normalizeSql(
          tenantPolicy.using_expression
        );

        const checkExpression = normalizeSql(
          tenantPolicy.check_expression
        );

        expect(
          usingExpression,
          `${qualifiedName}: USING and WITH CHECK must use the same fail-closed expression.`
        ).toBe(checkExpression);

        const compactUsingExpression = usingExpression.replace(/\s+/g, "");

        expect(compactUsingExpression).toContain("tenant_id=casewhen");
        expect(compactUsingExpression).toContain("pg_input_is_valid(");
        expect(compactUsingExpression).toContain(
          "current_setting('app.tenant_id'"
        );
        expect(compactUsingExpression).toContain("elsenull::uuid");
      }

      /*
       * Preserve the existing PostgresRuntime owner as the final authority
       * for effective role inheritance, assumable-role safety and the exact
       * canonical tenant-policy expression.
       */
      await expect(
        current.runtime.verifyRuntimeRoleSafety()
      ).resolves.toBeUndefined();

      const auditPrivileges =
        await current.adminPool.query<{
          readonly can_select: boolean;
          readonly can_insert: boolean;
          readonly can_update: boolean;
          readonly can_delete: boolean;
          readonly can_truncate: boolean;
        }>(
          `
            SELECT
              has_table_privilege(
                $1,
                'reos_infra.security_audit_events',
                'SELECT'
              ) AS can_select,
              has_table_privilege(
                $1,
                'reos_infra.security_audit_events',
                'INSERT'
              ) AS can_insert,
              has_table_privilege(
                $1,
                'reos_infra.security_audit_events',
                'UPDATE'
              ) AS can_update,
              has_table_privilege(
                $1,
                'reos_infra.security_audit_events',
                'DELETE'
              ) AS can_delete,
              has_table_privilege(
                $1,
                'reos_infra.security_audit_events',
                'TRUNCATE'
              ) AS can_truncate
          `,
          [current.applicationRole]
        );

      expect(auditPrivileges.rows).toEqual([
        {
          can_select: false,
          can_insert: false,
          can_update: false,
          can_delete: false,
          can_truncate: false
        }
      ]);
    });

    it("preserves unbounded PostgreSQL NUMERIC for financial ledger amounts", async () => {
      const current = requireDatabase();

      const result =
        await current.adminPool.query<FinancialTypeRow>(
          `
            SELECT
              pg_catalog.format_type(
                attribute.atttypid,
                attribute.atttypmod
              ) AS formatted_type,
              attribute.atttypmod AS typmod
            FROM pg_catalog.pg_attribute AS attribute
            WHERE attribute.attrelid =
              'core008.financial_ledger_entries'::regclass
              AND attribute.attname = 'amount'
              AND attribute.attnum > 0
              AND attribute.attisdropped = false
          `
        );

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.formatted_type).toBe("numeric");
      expect(result.rows[0]?.typmod).toBe(-1);
    });

    it("isolates tenant reads and rejects cross-tenant writes through the actual application login", async () => {
      const current = requireDatabase();

      const tenantA = randomUUID();
      const tenantB = randomUUID();

      const leadA = randomUUID();
      const leadB = randomUUID();

      const customerA = randomUUID();
      const customerB = randomUUID();

      const now = new Date().toISOString();

      for (const [tenantId, slug] of [
        [tenantA, `b4-rls-a-${tenantA.slice(0, 8)}`],
        [tenantB, `b4-rls-b-${tenantB.slice(0, 8)}`]
      ]) {
        await current.adminPool.query(
          `
            INSERT INTO core001.tenants (
              tenant_id,
              tenant_kind,
              operating_mode,
              display_name,
              slug,
              status,
              isolation_profile,
              residency_mode,
              quota_profile,
              revision,
              created_at,
              updated_at
            )
            VALUES (
              $1,
              'BROKERAGE',
              'BROKER_SAAS',
              $2,
              $3,
              'PROVISIONING',
              'SHARED_LOGICAL',
              'GLOBAL_ALLOWED',
              'default',
              1,
              $4,
              $4
            )
          `,
          [
            tenantId,
            slug,
            slug,
            now
          ]
        );
      }

      const leadInsert = `
        INSERT INTO core003.leads (
          lead_id,
          tenant_id,
          customer_id,
          status,
          priority,
          source_type,
          metadata,
          revision,
          created_at,
          updated_at
        )
        VALUES (
          $1,
          $2,
          $3,
          'NEW',
          'NORMAL',
          'OTHER',
          '{}'::jsonb,
          1,
          $4,
          $4
        )
      `;

      await current.adminPool.query(leadInsert, [
        leadA,
        tenantA,
        customerA,
        now
      ]);

      await current.adminPool.query(leadInsert, [
        leadB,
        tenantB,
        customerB,
        now
      ]);

      const visibleToA =
        await current.runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            transaction.query<LeadRow>(
              `
                SELECT tenant_id, lead_id
                FROM core003.leads
                WHERE tenant_id = ANY($1::uuid[])
                ORDER BY lead_id
              `,
              [[tenantA, tenantB]]
            )
        );

      expect(visibleToA.rows).toEqual([
        {
          tenant_id: tenantA,
          lead_id: leadA
        }
      ]);

      const visibleToB =
        await current.runtime.withTenantTransaction(
          { tenantId: tenantB },
          (transaction) =>
            transaction.query<LeadRow>(
              `
                SELECT tenant_id, lead_id
                FROM core003.leads
                WHERE tenant_id = ANY($1::uuid[])
                ORDER BY lead_id
              `,
              [[tenantA, tenantB]]
            )
        );

      expect(visibleToB.rows).toEqual([
        {
          tenant_id: tenantB,
          lead_id: leadB
        }
      ]);

      await expect(
        current.runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            transaction.query(
              leadInsert,
              [
                randomUUID(),
                tenantB,
                randomUUID(),
                now
              ]
            )
        )
      ).rejects.toMatchObject({
        code: "42501"
      });
    });
  }
);
