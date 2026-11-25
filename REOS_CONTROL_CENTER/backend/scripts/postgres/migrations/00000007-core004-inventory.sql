CREATE TABLE core004.projects (
  project_id text NOT NULL,
  tenant_id uuid NOT NULL,
  developer_id text NOT NULL,
  project_code text NOT NULL,
  name text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT projects_pkey
    PRIMARY KEY (tenant_id, project_id),

  CONSTRAINT projects_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT projects_project_id_check
    CHECK (
      project_id = btrim(project_id)
      AND length(project_id) > 0
    ),

  CONSTRAINT projects_developer_id_check
    CHECK (
      developer_id = btrim(developer_id)
      AND length(developer_id) > 0
    ),

  CONSTRAINT projects_project_code_check
    CHECK (
      project_code = btrim(project_code)
      AND length(project_code) > 0
    ),

  CONSTRAINT projects_name_check
    CHECK (
      name = btrim(name)
      AND length(name) > 0
    ),

  CONSTRAINT projects_metadata_object_check
    CHECK (jsonb_typeof(metadata) = 'object'),

  CONSTRAINT projects_tenant_project_code_key
    UNIQUE (tenant_id, project_code)
);

CREATE INDEX projects_tenant_developer_idx
  ON core004.projects (
    tenant_id,
    developer_id
  );

ALTER TABLE core004.projects
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core004.projects
  FORCE ROW LEVEL SECURITY;

CREATE POLICY projects_application_access
  ON core004.projects
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY projects_tenant_guard
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

  created_at timestamp with time zone NOT NULL,
  updated_at timestamp with time zone NOT NULL,

  version integer NOT NULL DEFAULT 1,

  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT inventory_pkey
    PRIMARY KEY (tenant_id, inventory_id),

  CONSTRAINT inventory_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT inventory_project_fk
    FOREIGN KEY (tenant_id, project_id)
    REFERENCES core004.projects (
      tenant_id,
      project_id
    ),

  CONSTRAINT inventory_id_check
    CHECK (
      inventory_id = btrim(inventory_id)
      AND length(inventory_id) > 0
    ),

  CONSTRAINT inventory_developer_id_check
    CHECK (
      developer_id = btrim(developer_id)
      AND length(developer_id) > 0
    ),

  CONSTRAINT inventory_project_id_check
    CHECK (
      project_id = btrim(project_id)
      AND length(project_id) > 0
    ),

  CONSTRAINT inventory_property_id_check
    CHECK (
      property_id IS NULL
      OR (
        property_id = btrim(property_id)
        AND length(property_id) > 0
      )
    ),

  CONSTRAINT inventory_unit_id_check
    CHECK (
      unit_id IS NULL
      OR (
        unit_id = btrim(unit_id)
        AND length(unit_id) > 0
      )
    ),

  CONSTRAINT inventory_type_check
    CHECK (
      inventory_type IN (
        'DEVELOPMENT',
        'PROPERTY',
        'UNIT'
      )
    ),

  CONSTRAINT inventory_hierarchy_check
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
        AND unit_id IS NULL
      )
      OR
      (
        inventory_type = 'UNIT'
        AND property_id IS NOT NULL
        AND unit_id IS NOT NULL
      )
    ),

  CONSTRAINT inventory_name_check
    CHECK (
      name = btrim(name)
      AND length(name) > 0
    ),

  CONSTRAINT inventory_lifecycle_check
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

  CONSTRAINT inventory_availability_check
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

  CONSTRAINT inventory_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT inventory_version_check
    CHECK (version > 0),

  CONSTRAINT inventory_metadata_object_check
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX inventory_tenant_project_type_idx
  ON core004.inventory (
    tenant_id,
    project_id,
    inventory_type
  );

CREATE INDEX inventory_tenant_lifecycle_availability_idx
  ON core004.inventory (
    tenant_id,
    lifecycle,
    availability
  );

ALTER TABLE core004.inventory
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core004.inventory
  FORCE ROW LEVEL SECURITY;

CREATE POLICY inventory_application_access
  ON core004.inventory
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY inventory_tenant_guard
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

REVOKE ALL ON TABLE
  core004.projects,
  core004.inventory
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core004.projects
TO __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core004.inventory
TO __HOMIO_APPLICATION_ROLE__;
