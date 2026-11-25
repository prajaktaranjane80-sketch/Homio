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
