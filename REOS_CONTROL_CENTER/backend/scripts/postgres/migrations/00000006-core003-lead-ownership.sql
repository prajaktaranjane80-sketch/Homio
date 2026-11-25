
BEGIN;

CREATE SCHEMA core003;

REVOKE ALL ON SCHEMA core003 FROM PUBLIC;
GRANT USAGE ON SCHEMA core003 TO __HOMIO_APPLICATION_ROLE__;

ALTER DEFAULT PRIVILEGES IN SCHEMA core003
  REVOKE ALL ON TABLES
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core003.leads (
  lead_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  customer_id uuid NOT NULL,
  status text NOT NULL,
  priority text NOT NULL,
  source_type text NOT NULL,
  source_id text,
  campaign_id text,
  channel text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  revision integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,

  CONSTRAINT core003_leads_pkey
    PRIMARY KEY (lead_id),

  CONSTRAINT core003_leads_tenant_identity_uq
    UNIQUE (tenant_id, lead_id),

  CONSTRAINT core003_leads_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core003_leads_status_check
    CHECK (
      status IN (
        'NEW',
        'QUALIFYING',
        'QUALIFIED',
        'NURTURING',
        'CONVERTED',
        'LOST',
        'ARCHIVED'
      )
    ),

  CONSTRAINT core003_leads_priority_check
    CHECK (
      priority IN (
        'LOW',
        'NORMAL',
        'HIGH',
        'URGENT'
      )
    ),

  CONSTRAINT core003_leads_source_type_check
    CHECK (
      source_type IN (
        'DIRECT',
        'WEBSITE',
        'PORTAL',
        'REFERRAL',
        'BUILDER',
        'BROKER',
        'PARTNER',
        'CAMPAIGN',
        'IMPORT',
        'API',
        'OTHER'
      )
    ),

  CONSTRAINT core003_leads_metadata_object_check
    CHECK (
      jsonb_typeof(metadata) = 'object'
    ),

  CONSTRAINT core003_leads_revision_check
    CHECK (revision >= 0),

  CONSTRAINT core003_leads_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX core003_leads_tenant_customer_idx
  ON core003.leads (
    tenant_id,
    customer_id
  );

CREATE INDEX core003_leads_tenant_status_idx
  ON core003.leads (
    tenant_id,
    status
  );

CREATE INDEX core003_leads_tenant_created_idx
  ON core003.leads (
    tenant_id,
    created_at DESC
  );

CREATE TABLE core003.lead_ownership (
  lead_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  owner_id uuid NOT NULL,
  owner_role text NOT NULL,
  assigned_at timestamptz NOT NULL,
  revision integer NOT NULL DEFAULT 0,
  assignment_reference text,

  CONSTRAINT core003_lead_ownership_pkey
    PRIMARY KEY (tenant_id, lead_id),

  CONSTRAINT core003_lead_ownership_lead_fk
    FOREIGN KEY (tenant_id, lead_id)
    REFERENCES core003.leads (tenant_id, lead_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core003_lead_ownership_role_check
    CHECK (
      owner_role IN (
        'BROKERAGE',
        'BROKER',
        'AGENT',
        'PARTNER',
        'BUILDER',
        'PLATFORM'
      )
    ),

  CONSTRAINT core003_lead_ownership_revision_check
    CHECK (revision >= 0),

  CONSTRAINT core003_lead_ownership_reference_check
    CHECK (
      assignment_reference IS NULL
      OR char_length(assignment_reference) > 0
    )
);

CREATE INDEX core003_lead_ownership_owner_idx
  ON core003.lead_ownership (
    tenant_id,
    owner_id
  );

CREATE TABLE core003.ownership_transfers (
  transfer_id uuid NOT NULL,
  lead_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  previous_owner_id uuid NOT NULL,
  new_owner_id uuid NOT NULL,
  previous_revision integer NOT NULL,
  new_revision integer NOT NULL,
  reason text NOT NULL,
  transferred_at timestamptz NOT NULL,
  transfer_reference text,

  CONSTRAINT core003_ownership_transfers_pkey
    PRIMARY KEY (transfer_id),

  CONSTRAINT core003_ownership_transfers_history_uq
    UNIQUE (
      tenant_id,
      lead_id,
      new_revision
    ),

  CONSTRAINT core003_ownership_transfers_lead_fk
    FOREIGN KEY (tenant_id, lead_id)
    REFERENCES core003.leads (tenant_id, lead_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core003_ownership_transfers_reason_check
    CHECK (
      reason IN (
        'MANUAL',
        'BUSINESS_RULE',
        'REASSIGNMENT',
        'TENANT_INTERNAL',
        'PARTNER_CHANGE'
      )
    ),

  CONSTRAINT core003_ownership_transfers_previous_revision_check
    CHECK (previous_revision >= 0),

  CONSTRAINT core003_ownership_transfers_revision_step_check
    CHECK (new_revision = previous_revision + 1),

  CONSTRAINT core003_ownership_transfers_owner_change_check
    CHECK (previous_owner_id <> new_owner_id),

  CONSTRAINT core003_ownership_transfers_reference_check
    CHECK (
      transfer_reference IS NULL
      OR char_length(transfer_reference) > 0
    )
);

ALTER TABLE core003.leads
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core003.leads
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core003_leads_application_access
  ON core003.leads
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core003_leads_tenant_guard
  ON core003.leads
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

ALTER TABLE core003.lead_ownership
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core003.lead_ownership
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core003_lead_ownership_application_access
  ON core003.lead_ownership
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core003_lead_ownership_tenant_guard
  ON core003.lead_ownership
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

ALTER TABLE core003.ownership_transfers
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core003.ownership_transfers
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core003_ownership_transfers_application_access
  ON core003.ownership_transfers
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core003_ownership_transfers_tenant_guard
  ON core003.ownership_transfers
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

REVOKE ALL ON ALL TABLES IN SCHEMA core003
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core003.leads,
  core003.lead_ownership
  TO __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core003.ownership_transfers
  TO __HOMIO_APPLICATION_ROLE__;

COMMIT;
