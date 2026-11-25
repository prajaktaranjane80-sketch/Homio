CREATE TABLE core001.identities (
  identity_id uuid NOT NULL,
  identity_type text NOT NULL,
  display_name text NOT NULL,
  handle text NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE',
  privacy_class text NOT NULL DEFAULT 'INTERNAL',
  revision integer NOT NULL DEFAULT 1,
  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),
  updated_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT identities_pkey
    PRIMARY KEY (identity_id),

  CONSTRAINT identities_identity_type_check
    CHECK (
      identity_type IN ('HUMAN', 'SERVICE', 'AI', 'SYSTEM')
    ),

  CONSTRAINT identities_display_name_check
    CHECK (
      display_name = btrim(display_name)
      AND length(display_name) BETWEEN 1 AND 120
    ),

  CONSTRAINT identities_handle_check
    CHECK (
      handle = lower(handle)
      AND handle ~ '^[a-z0-9][a-z0-9._-]{2,63}$'
    ),

  CONSTRAINT identities_status_check
    CHECK (
      status IN ('ACTIVE', 'SUSPENDED', 'DEACTIVATED')
    ),

  CONSTRAINT identities_privacy_class_check
    CHECK (
      privacy_class IN ('INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')
    ),

  CONSTRAINT identities_revision_check
    CHECK (revision > 0),

  CONSTRAINT identities_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT identities_handle_key
    UNIQUE (handle)
);

CREATE TABLE core001.identity_accounts (
  account_id uuid NOT NULL,
  identity_id uuid NOT NULL,
  status text NOT NULL DEFAULT 'ENABLED',
  authentication_epoch bigint NOT NULL DEFAULT 1,
  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),
  updated_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT identity_accounts_pkey
    PRIMARY KEY (account_id),

  CONSTRAINT identity_accounts_identity_fk
    FOREIGN KEY (identity_id)
    REFERENCES core001.identities (identity_id),

  CONSTRAINT identity_accounts_status_check
    CHECK (
      status IN ('ENABLED', 'LOCKED', 'DISABLED')
    ),

  CONSTRAINT identity_accounts_authentication_epoch_check
    CHECK (authentication_epoch > 0),

  CONSTRAINT identity_accounts_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX identity_accounts_identity_idx
  ON core001.identity_accounts (identity_id);

CREATE TABLE core001.tenants (
  tenant_id uuid NOT NULL,
  tenant_kind text NOT NULL,
  operating_mode text NOT NULL,
  display_name text NOT NULL,
  slug text NOT NULL,
  status text NOT NULL DEFAULT 'PROVISIONING',
  isolation_profile text NOT NULL DEFAULT 'SHARED_LOGICAL',
  residency_mode text NOT NULL DEFAULT 'GLOBAL_ALLOWED',
  residency_region text,
  jurisdiction text,
  quota_profile text NOT NULL DEFAULT 'default',
  owner_identity_id uuid,
  primary_admin_identity_id uuid,

  configuration_ref jsonb NOT NULL DEFAULT
    jsonb_build_object(
      'reference_id', gen_random_uuid(),
      'configuration_key', 'default',
      'version', 1
    ),

  security_profile_ref jsonb NOT NULL DEFAULT
    jsonb_build_object(
      'reference_id', gen_random_uuid(),
      'profile_key', 'default',
      'version', 1,
      'fail_closed', true,
      'require_valid_tenant_context', true
    ),

  region_jurisdiction_ref jsonb,

  revision integer NOT NULL DEFAULT 1,

  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  updated_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT tenants_pkey
    PRIMARY KEY (tenant_id),

  CONSTRAINT tenants_owner_identity_fk
    FOREIGN KEY (owner_identity_id)
    REFERENCES core001.identities (identity_id),

  CONSTRAINT tenants_primary_admin_identity_fk
    FOREIGN KEY (primary_admin_identity_id)
    REFERENCES core001.identities (identity_id),

  CONSTRAINT tenants_kind_check
    CHECK (
      tenant_kind IN (
        'BROKERAGE',
        'BUILDER',
        'ENTERPRISE',
        'PARTNER',
        'PLATFORM'
      )
    ),

  CONSTRAINT tenants_operating_mode_check
    CHECK (
      operating_mode IN (
        'OWNED_INTERNATIONAL_BROKERAGE',
        'BROKER_SAAS',
        'BUILDER_SAAS',
        'ENTERPRISE_WHITE_LABEL',
        'PLATFORM_API_PARTNER'
      )
    ),

  CONSTRAINT tenants_status_check
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

  CONSTRAINT tenants_isolation_profile_check
    CHECK (
      isolation_profile IN (
        'SHARED_LOGICAL',
        'TENANT_DEDICATED'
      )
    ),

  CONSTRAINT tenants_residency_mode_check
    CHECK (
      residency_mode IN (
        'GLOBAL_ALLOWED',
        'REGION_BOUND',
        'COUNTRY_BOUND',
        'CUSTOM_POLICY'
      )
    ),

  CONSTRAINT tenants_slug_check
    CHECK (
      slug = lower(slug)
      AND slug ~ '^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$'
    ),

  CONSTRAINT tenants_slug_key
    UNIQUE (slug),

  CONSTRAINT tenants_display_name_check
    CHECK (
      display_name = btrim(display_name)
      AND length(display_name) > 0
    ),

  CONSTRAINT tenants_quota_profile_check
    CHECK (
      quota_profile = btrim(quota_profile)
      AND length(quota_profile) BETWEEN 1 AND 128
    ),

  CONSTRAINT tenants_configuration_ref_object_check
    CHECK (jsonb_typeof(configuration_ref) = 'object'),

  CONSTRAINT tenants_security_profile_ref_object_check
    CHECK (
      jsonb_typeof(security_profile_ref) = 'object'
      AND jsonb_typeof(
        security_profile_ref->'fail_closed'
      ) = 'boolean'
      AND jsonb_typeof(
        security_profile_ref->'require_valid_tenant_context'
      ) = 'boolean'
    ),

  CONSTRAINT tenants_region_jurisdiction_ref_check
    CHECK (
      region_jurisdiction_ref IS NULL
      OR jsonb_typeof(region_jurisdiction_ref) = 'object'
    ),

  CONSTRAINT tenants_residency_scope_check
    CHECK (
      residency_mode = 'GLOBAL_ALLOWED'
      OR residency_region IS NOT NULL
      OR jurisdiction IS NOT NULL
      OR region_jurisdiction_ref IS NOT NULL
    ),

  CONSTRAINT tenants_active_owner_check
    CHECK (
      status <> 'ACTIVE'
      OR (
        owner_identity_id IS NOT NULL
        AND primary_admin_identity_id IS NOT NULL
        AND security_profile_ref->>'fail_closed' = 'true'
        AND security_profile_ref->>'require_valid_tenant_context' = 'true'
      )
    ),

  CONSTRAINT tenants_revision_check
    CHECK (revision > 0),

  CONSTRAINT tenants_time_order_check
    CHECK (updated_at >= created_at)
);

ALTER TABLE core001.tenants
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core001.tenants
  FORCE ROW LEVEL SECURITY;

CREATE POLICY tenants_application_access
  ON core001.tenants
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY tenants_tenant_guard
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

CREATE TABLE core001.organizations (
  organization_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  display_name text NOT NULL,
  slug text NOT NULL,
  status text NOT NULL DEFAULT 'ACTIVE',
  parent_organization_id uuid,
  revision integer NOT NULL DEFAULT 1,
  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),
  updated_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT organizations_pkey
    PRIMARY KEY (organization_id),

  CONSTRAINT organizations_tenant_identity_key
    UNIQUE (tenant_id, organization_id),

  CONSTRAINT organizations_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT organizations_parent_fk
    FOREIGN KEY (tenant_id, parent_organization_id)
    REFERENCES core001.organizations (
      tenant_id,
      organization_id
    ),

  CONSTRAINT organizations_display_name_check
    CHECK (
      display_name = btrim(display_name)
      AND length(display_name) BETWEEN 1 AND 200
    ),

  CONSTRAINT organizations_slug_check
    CHECK (
      slug = lower(slug)
      AND slug ~ '^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$'
    ),

  CONSTRAINT organizations_status_check
    CHECK (
      status IN (
        'ACTIVE',
        'RESTRICTED',
        'SUSPENDED',
        'DEACTIVATED'
      )
    ),

  CONSTRAINT organizations_revision_check
    CHECK (revision > 0),

  CONSTRAINT organizations_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT organizations_not_own_parent_check
    CHECK (
      parent_organization_id IS NULL
      OR parent_organization_id <> organization_id
    ),

  CONSTRAINT organizations_tenant_slug_key
    UNIQUE (tenant_id, slug)
);

CREATE INDEX organizations_tenant_parent_idx
  ON core001.organizations (
    tenant_id,
    parent_organization_id
  );

ALTER TABLE core001.organizations
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core001.organizations
  FORCE ROW LEVEL SECURITY;

CREATE POLICY organizations_application_access
  ON core001.organizations
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY organizations_tenant_guard
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

  valid_from timestamp with time zone,
  valid_until timestamp with time zone,
  invited_at timestamp with time zone,
  joined_at timestamp with time zone,

  revision integer NOT NULL DEFAULT 1,

  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  updated_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT memberships_pkey
    PRIMARY KEY (membership_id),

  CONSTRAINT memberships_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT memberships_organization_fk
    FOREIGN KEY (tenant_id, organization_id)
    REFERENCES core001.organizations (
      tenant_id,
      organization_id
    ),

  CONSTRAINT memberships_identity_fk
    FOREIGN KEY (identity_id)
    REFERENCES core001.identities (identity_id),

  CONSTRAINT memberships_status_check
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

  CONSTRAINT memberships_required_assurance_check
    CHECK (
      required_assurance IN (
        'BASIC',
        'STANDARD',
        'STRONG',
        'HIGH'
      )
    ),

  CONSTRAINT memberships_attribute_constraints_array_check
    CHECK (
      jsonb_typeof(attribute_constraints) = 'array'
    ),

  CONSTRAINT memberships_validity_check
    CHECK (
      valid_from IS NULL
      OR valid_until IS NULL
      OR valid_until > valid_from
    ),

  CONSTRAINT memberships_revision_check
    CHECK (revision > 0),

  CONSTRAINT memberships_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX memberships_tenant_identity_idx
  ON core001.memberships (
    tenant_id,
    identity_id
  );

CREATE INDEX memberships_tenant_organization_idx
  ON core001.memberships (
    tenant_id,
    organization_id
  );

ALTER TABLE core001.memberships
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core001.memberships
  FORCE ROW LEVEL SECURITY;

CREATE POLICY memberships_application_access
  ON core001.memberships
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY memberships_tenant_guard
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

REVOKE ALL ON TABLE
  core001.identities,
  core001.identity_accounts,
  core001.tenants,
  core001.organizations,
  core001.memberships
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core001.identities,
  core001.identity_accounts,
  core001.tenants,
  core001.organizations,
  core001.memberships
TO __HOMIO_APPLICATION_ROLE__;
