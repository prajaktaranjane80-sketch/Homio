
BEGIN;

CREATE SCHEMA core001;

REVOKE ALL ON SCHEMA core001 FROM PUBLIC;
GRANT USAGE ON SCHEMA core001 TO __HOMIO_APPLICATION_ROLE__;

ALTER DEFAULT PRIVILEGES IN SCHEMA core001
  REVOKE ALL ON TABLES
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core001.identities (
  identity_id uuid NOT NULL,
  identity_type text NOT NULL,
  display_name text NOT NULL,
  handle varchar(64) NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE',
  privacy_class text NOT NULL DEFAULT 'INTERNAL',
  revision integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,

  CONSTRAINT core001_identities_pkey
    PRIMARY KEY (identity_id),

  CONSTRAINT core001_identities_type_check
    CHECK (
      identity_type IN ('HUMAN', 'SERVICE', 'AI', 'SYSTEM')
    ),

  CONSTRAINT core001_identities_status_check
    CHECK (
      status IN ('ACTIVE', 'SUSPENDED', 'DEACTIVATED')
    ),

  CONSTRAINT core001_identities_privacy_check
    CHECK (
      privacy_class IN ('INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')
    ),

  CONSTRAINT core001_identities_display_name_check
    CHECK (
      char_length(display_name) BETWEEN 1 AND 120
    ),

  CONSTRAINT core001_identities_handle_check
    CHECK (
      handle ~ '^[a-z0-9][a-z0-9._-]{2,63}$'
    ),

  CONSTRAINT core001_identities_revision_check
    CHECK (revision >= 1),

  CONSTRAINT core001_identities_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE UNIQUE INDEX core001_identities_handle_uq
  ON core001.identities (handle);

CREATE TABLE core001.identity_accounts (
  account_id uuid NOT NULL,
  identity_id uuid NOT NULL,
  status text NOT NULL DEFAULT 'ENABLED',
  authentication_epoch integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,

  CONSTRAINT core001_identity_accounts_pkey
    PRIMARY KEY (account_id),

  CONSTRAINT core001_identity_accounts_identity_fk
    FOREIGN KEY (identity_id)
    REFERENCES core001.identities (identity_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_identity_accounts_status_check
    CHECK (status IN ('ENABLED', 'LOCKED', 'DISABLED')),

  CONSTRAINT core001_identity_accounts_epoch_check
    CHECK (authentication_epoch >= 1),

  CONSTRAINT core001_identity_accounts_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX core001_identity_accounts_identity_idx
  ON core001.identity_accounts (identity_id);

CREATE TABLE core001.tenants (
  tenant_id uuid NOT NULL,
  tenant_kind text NOT NULL,
  operating_mode text NOT NULL,
  display_name text NOT NULL,
  slug varchar(64) NOT NULL,
  status text NOT NULL DEFAULT 'PROVISIONING',
  isolation_profile text NOT NULL DEFAULT 'SHARED_LOGICAL',
  residency_mode text NOT NULL DEFAULT 'GLOBAL_ALLOWED',
  residency_region text,
  jurisdiction text,
  quota_profile varchar(128) NOT NULL DEFAULT 'default',
  owner_identity_id uuid,
  primary_admin_identity_id uuid,
  configuration_ref jsonb NOT NULL,
  security_profile_ref jsonb NOT NULL,
  region_jurisdiction_ref jsonb,
  revision integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,

  CONSTRAINT core001_tenants_pkey
    PRIMARY KEY (tenant_id),

  CONSTRAINT core001_tenants_slug_uq
    UNIQUE (slug),

  CONSTRAINT core001_tenants_owner_identity_fk
    FOREIGN KEY (owner_identity_id)
    REFERENCES core001.identities (identity_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_tenants_primary_admin_identity_fk
    FOREIGN KEY (primary_admin_identity_id)
    REFERENCES core001.identities (identity_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_tenants_kind_check
    CHECK (
      tenant_kind IN (
        'BROKERAGE',
        'BUILDER',
        'ENTERPRISE',
        'PARTNER',
        'PLATFORM'
      )
    ),

  CONSTRAINT core001_tenants_operating_mode_check
    CHECK (
      operating_mode IN (
        'OWNED_INTERNATIONAL_BROKERAGE',
        'BROKER_SAAS',
        'BUILDER_SAAS',
        'ENTERPRISE_WHITE_LABEL',
        'PLATFORM_API_PARTNER'
      )
    ),

  CONSTRAINT core001_tenants_status_check
    CHECK (
      status IN (
        'PROVISIONING',
        'PENDING_ACTIVATION',
        'ACTIVE',
        'RESTRICTED',
        'SUSPENDED',
        'DEACTIVATING',
        'DEACTIVATED',
        'ARCHIVED'
      )
    ),

  CONSTRAINT core001_tenants_isolation_check
    CHECK (
      isolation_profile IN (
        'SHARED_LOGICAL',
        'TENANT_DEDICATED'
      )
    ),

  CONSTRAINT core001_tenants_residency_check
    CHECK (
      residency_mode IN (
        'GLOBAL_ALLOWED',
        'REGION_BOUND',
        'COUNTRY_BOUND',
        'CUSTOM_POLICY'
      )
    ),

  CONSTRAINT core001_tenants_slug_check
    CHECK (
      slug ~ '^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$'
    ),

  CONSTRAINT core001_tenants_quota_profile_check
    CHECK (
      char_length(quota_profile) BETWEEN 1 AND 128
    ),

  CONSTRAINT core001_tenants_region_check
    CHECK (
      residency_region IS NULL
      OR residency_region ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$'
    ),

  CONSTRAINT core001_tenants_jurisdiction_check
    CHECK (
      jurisdiction IS NULL
      OR jurisdiction ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$'
    ),

  CONSTRAINT core001_tenants_region_required_check
    CHECK (
      residency_mode <> 'REGION_BOUND'
      OR residency_region IS NOT NULL
    ),

  CONSTRAINT core001_tenants_country_required_check
    CHECK (
      residency_mode <> 'COUNTRY_BOUND'
      OR jurisdiction IS NOT NULL
    ),

  CONSTRAINT core001_tenants_configuration_ref_object_check
    CHECK (
      jsonb_typeof(configuration_ref) = 'object'
    ),

  CONSTRAINT core001_tenants_security_profile_ref_object_check
    CHECK (
      jsonb_typeof(security_profile_ref) = 'object'
    ),

  CONSTRAINT core001_tenants_region_ref_object_check
    CHECK (
      region_jurisdiction_ref IS NULL
      OR jsonb_typeof(region_jurisdiction_ref) = 'object'
    ),

  CONSTRAINT core001_tenants_revision_check
    CHECK (revision >= 1),

  CONSTRAINT core001_tenants_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT core001_tenants_active_owner_check
    CHECK (
      status <> 'ACTIVE'
      OR (
        owner_identity_id IS NOT NULL
        AND primary_admin_identity_id IS NOT NULL
        AND security_profile_ref @>
          '{"fail_closed": true, "require_valid_tenant_context": true}'::jsonb
      )
    )
);

CREATE INDEX core001_tenants_status_idx
  ON core001.tenants (status);

CREATE TABLE core001.organizations (
  organization_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  display_name text NOT NULL,
  slug varchar(64) NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE',
  parent_organization_id uuid,
  revision integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,

  CONSTRAINT core001_organizations_pkey
    PRIMARY KEY (organization_id),

  CONSTRAINT core001_organizations_tenant_identity_uq
    UNIQUE (tenant_id, organization_id),

  CONSTRAINT core001_organizations_tenant_slug_uq
    UNIQUE (tenant_id, slug),

  CONSTRAINT core001_organizations_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_organizations_parent_fk
    FOREIGN KEY (tenant_id, parent_organization_id)
    REFERENCES core001.organizations (
      tenant_id,
      organization_id
    )
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_organizations_display_name_check
    CHECK (
      char_length(display_name) BETWEEN 1 AND 200
    ),

  CONSTRAINT core001_organizations_slug_check
    CHECK (
      slug ~ '^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$'
    ),

  CONSTRAINT core001_organizations_status_check
    CHECK (
      status IN (
        'ACTIVE',
        'RESTRICTED',
        'SUSPENDED',
        'DEACTIVATED'
      )
    ),

  CONSTRAINT core001_organizations_not_own_parent_check
    CHECK (
      parent_organization_id IS NULL
      OR parent_organization_id <> organization_id
    ),

  CONSTRAINT core001_organizations_revision_check
    CHECK (revision >= 1),

  CONSTRAINT core001_organizations_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX core001_organizations_parent_idx
  ON core001.organizations (
    tenant_id,
    parent_organization_id
  );

CREATE FUNCTION core001.has_unique_uuid_array(value uuid[])
RETURNS boolean
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
SET search_path = pg_catalog
AS $function$
  SELECT
    cardinality(value) = count(DISTINCT item)
  FROM unnest(value) AS item;
$function$;

CREATE TABLE core001.memberships (
  membership_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  organization_id uuid NOT NULL,
  identity_id uuid NOT NULL,
  status text NOT NULL DEFAULT 'INVITED',
  role_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
  entitlement_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
  scope_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
  relationship_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
  attribute_constraints jsonb NOT NULL DEFAULT '[]'::jsonb,
  required_assurance text NOT NULL DEFAULT 'STANDARD',
  valid_from timestamptz,
  valid_until timestamptz,
  invited_at timestamptz,
  joined_at timestamptz,
  revision integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,

  CONSTRAINT core001_memberships_pkey
    PRIMARY KEY (membership_id),

  CONSTRAINT core001_memberships_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_memberships_organization_fk
    FOREIGN KEY (tenant_id, organization_id)
    REFERENCES core001.organizations (
      tenant_id,
      organization_id
    )
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_memberships_identity_fk
    FOREIGN KEY (identity_id)
    REFERENCES core001.identities (identity_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core001_memberships_status_check
    CHECK (
      status IN (
        'INVITED',
        'PENDING',
        'ACTIVE',
        'RESTRICTED',
        'SUSPENDED',
        'REVOKED',
        'EXPIRED'
      )
    ),

  CONSTRAINT core001_memberships_assurance_check
    CHECK (
      required_assurance IN (
        'BASIC',
        'STANDARD',
        'STRONG',
        'HIGH'
      )
    ),

  CONSTRAINT core001_memberships_role_ids_unique_check
    CHECK (
      core001.has_unique_uuid_array(role_ids)
    ),

  CONSTRAINT core001_memberships_entitlement_ids_unique_check
    CHECK (
      core001.has_unique_uuid_array(entitlement_ids)
    ),

  CONSTRAINT core001_memberships_scope_ids_unique_check
    CHECK (
      core001.has_unique_uuid_array(scope_ids)
    ),

  CONSTRAINT core001_memberships_relationship_ids_unique_check
    CHECK (
      core001.has_unique_uuid_array(relationship_ids)
    ),

  CONSTRAINT core001_memberships_attribute_constraints_array_check
    CHECK (
      jsonb_typeof(attribute_constraints) = 'array'
    ),

  CONSTRAINT core001_memberships_validity_window_check
    CHECK (
      valid_from IS NULL
      OR valid_until IS NULL
      OR valid_until > valid_from
    ),

  CONSTRAINT core001_memberships_revision_check
    CHECK (revision >= 1),

  CONSTRAINT core001_memberships_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX core001_memberships_tenant_organization_idx
  ON core001.memberships (
    tenant_id,
    organization_id
  );

CREATE INDEX core001_memberships_tenant_identity_idx
  ON core001.memberships (
    tenant_id,
    identity_id
  );

CREATE INDEX core001_memberships_tenant_status_idx
  ON core001.memberships (
    tenant_id,
    status
  );

ALTER TABLE core001.tenants
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core001.tenants
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core001_tenants_application_access
  ON core001.tenants
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core001_tenants_tenant_guard
  ON core001.tenants
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );

ALTER TABLE core001.organizations
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core001.organizations
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core001_organizations_application_access
  ON core001.organizations
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core001_organizations_tenant_guard
  ON core001.organizations
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );

ALTER TABLE core001.memberships
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core001.memberships
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core001_memberships_application_access
  ON core001.memberships
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core001_memberships_tenant_guard
  ON core001.memberships
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );

REVOKE ALL ON ALL TABLES IN SCHEMA core001
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core001.identities,
  core001.identity_accounts,
  core001.tenants,
  core001.organizations,
  core001.memberships
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  core001.has_unique_uuid_array(uuid[])
  FROM PUBLIC;

GRANT EXECUTE ON FUNCTION
  core001.has_unique_uuid_array(uuid[])
  TO __HOMIO_APPLICATION_ROLE__;

COMMIT;
