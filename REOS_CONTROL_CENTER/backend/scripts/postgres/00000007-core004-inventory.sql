
BEGIN;

CREATE SCHEMA core004;

REVOKE ALL ON SCHEMA core004 FROM PUBLIC;
GRANT USAGE ON SCHEMA core004 TO __HOMIO_APPLICATION_ROLE__;

ALTER DEFAULT PRIVILEGES IN SCHEMA core004
  REVOKE ALL ON TABLES
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core004.projects (
  project_id text NOT NULL,
  tenant_id uuid NOT NULL,
  developer_id text NOT NULL,
  project_code varchar(64) NOT NULL,
  name text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT core004_projects_pkey
    PRIMARY KEY (tenant_id, project_id),

  CONSTRAINT core004_projects_tenant_code_uq
    UNIQUE (tenant_id, project_code),

  CONSTRAINT core004_projects_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core004_projects_project_id_check
    CHECK (char_length(project_id) > 0),

  CONSTRAINT core004_projects_developer_id_check
    CHECK (char_length(developer_id) > 0),

  CONSTRAINT core004_projects_project_code_check
    CHECK (
      project_code ~ '^[A-Z0-9_-]{2,64}$'
    ),

  CONSTRAINT core004_projects_name_check
    CHECK (char_length(name) > 0),

  CONSTRAINT core004_projects_metadata_object_check
    CHECK (
      jsonb_typeof(metadata) = 'object'
    )
);

CREATE INDEX core004_projects_tenant_developer_idx
  ON core004.projects (
    tenant_id,
    developer_id
  );

CREATE TABLE core004.inventory (
  inventory_id text NOT NULL,
  tenant_id uuid NOT NULL,
  inventory_type text NOT NULL,
  developer_id text NOT NULL,
  project_id text NOT NULL,
  property_id text,
  unit_id text,
  name text NOT NULL,
  lifecycle text NOT NULL,
  availability text NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  version integer NOT NULL DEFAULT 1,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT core004_inventory_project_fk
    FOREIGN KEY (tenant_id, project_id)
    REFERENCES core004.projects (
      tenant_id,
      project_id
    )
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core004_inventory_identity_uq
    UNIQUE NULLS NOT DISTINCT (
      tenant_id,
      inventory_type,
      project_id,
      property_id,
      unit_id,
      inventory_id
    ),

  CONSTRAINT core004_inventory_type_check
    CHECK (
      inventory_type IN (
        'DEVELOPMENT',
        'PROPERTY',
        'UNIT'
      )
    ),

  CONSTRAINT core004_inventory_lifecycle_check
    CHECK (
      lifecycle IN (
        'DRAFT',
        'ACTIVE',
        'RESERVED',
        'BLOCKED',
        'SOLD',
        'UNAVAILABLE',
        'ARCHIVED'
      )
    ),

  CONSTRAINT core004_inventory_availability_check
    CHECK (
      availability IN (
        'AVAILABLE',
        'RESERVED',
        'BLOCKED',
        'ALLOCATED',
        'SOLD',
        'UNAVAILABLE'
      )
    ),

  CONSTRAINT core004_inventory_identity_text_check
    CHECK (
      char_length(inventory_id) > 0
      AND char_length(developer_id) > 0
      AND char_length(project_id) > 0
      AND char_length(name) > 0
    ),

  CONSTRAINT core004_inventory_hierarchy_check
    CHECK (
      (
        inventory_type = 'DEVELOPMENT'
        AND property_id IS NULL
        AND unit_id IS NULL
      )
      OR
      (
        inventory_type = 'PROPERTY'
        AND property_id IS NOT NULL
        AND char_length(property_id) > 0
        AND unit_id IS NULL
      )
      OR
      (
        inventory_type = 'UNIT'
        AND property_id IS NOT NULL
        AND char_length(property_id) > 0
        AND unit_id IS NOT NULL
        AND char_length(unit_id) > 0
      )
    ),

  CONSTRAINT core004_inventory_version_check
    CHECK (version >= 1),

  CONSTRAINT core004_inventory_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT core004_inventory_metadata_object_check
    CHECK (
      jsonb_typeof(metadata) = 'object'
    )
);

CREATE INDEX core004_inventory_tenant_project_idx
  ON core004.inventory (
    tenant_id,
    project_id
  );

CREATE INDEX core004_inventory_tenant_type_idx
  ON core004.inventory (
    tenant_id,
    inventory_type
  );

CREATE INDEX core004_inventory_tenant_developer_idx
  ON core004.inventory (
    tenant_id,
    developer_id
  );

ALTER TABLE core004.projects
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core004.projects
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core004_projects_application_access
  ON core004.projects
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core004_projects_tenant_guard
  ON core004.projects
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

ALTER TABLE core004.inventory
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core004.inventory
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core004_inventory_application_access
  ON core004.inventory
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core004_inventory_tenant_guard
  ON core004.inventory
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

REVOKE ALL ON ALL TABLES IN SCHEMA core004
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core004.projects,
  core004.inventory
  TO __HOMIO_APPLICATION_ROLE__;

COMMIT;
