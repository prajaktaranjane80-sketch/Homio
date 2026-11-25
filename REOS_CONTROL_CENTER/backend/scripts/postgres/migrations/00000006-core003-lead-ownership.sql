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

  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  updated_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT leads_pkey
    PRIMARY KEY (tenant_id, lead_id),

  CONSTRAINT leads_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT leads_status_check
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

  CONSTRAINT leads_priority_check
    CHECK (
      priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')
    ),

  CONSTRAINT leads_source_type_check
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

  CONSTRAINT leads_source_id_check
    CHECK (
      source_id IS NULL
      OR (
        source_id = btrim(source_id)
        AND length(source_id) > 0
      )
    ),

  CONSTRAINT leads_campaign_id_check
    CHECK (
      campaign_id IS NULL
      OR (
        campaign_id = btrim(campaign_id)
        AND length(campaign_id) > 0
      )
    ),

  CONSTRAINT leads_channel_check
    CHECK (
      channel IS NULL
      OR (
        channel = btrim(channel)
        AND length(channel) > 0
      )
    ),

  CONSTRAINT leads_metadata_object_check
    CHECK (jsonb_typeof(metadata) = 'object'),

  CONSTRAINT leads_revision_check
    CHECK (revision >= 0),

  CONSTRAINT leads_time_order_check
    CHECK (updated_at >= created_at)
);

CREATE INDEX leads_tenant_status_created_idx
  ON core003.leads (
    tenant_id,
    status,
    created_at DESC
  );

CREATE INDEX leads_tenant_customer_created_idx
  ON core003.leads (
    tenant_id,
    customer_id,
    created_at DESC
  );

ALTER TABLE core003.leads
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core003.leads
  FORCE ROW LEVEL SECURITY;

CREATE POLICY leads_application_access
  ON core003.leads
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY leads_tenant_guard
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

CREATE TABLE core003.lead_ownership (
  lead_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  owner_id uuid NOT NULL,
  owner_role text NOT NULL,
  assigned_at timestamp with time zone NOT NULL,
  revision integer NOT NULL DEFAULT 0,
  assignment_reference text,

  CONSTRAINT lead_ownership_pkey
    PRIMARY KEY (tenant_id, lead_id),

  CONSTRAINT lead_ownership_lead_fk
    FOREIGN KEY (tenant_id, lead_id)
    REFERENCES core003.leads (tenant_id, lead_id),

  CONSTRAINT lead_ownership_owner_role_check
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

  CONSTRAINT lead_ownership_revision_check
    CHECK (revision >= 0),

  CONSTRAINT lead_ownership_assignment_reference_check
    CHECK (
      assignment_reference IS NULL
      OR (
        assignment_reference = btrim(assignment_reference)
        AND length(assignment_reference) > 0
      )
    )
);

CREATE INDEX lead_ownership_tenant_owner_assigned_idx
  ON core003.lead_ownership (
    tenant_id,
    owner_id,
    assigned_at DESC
  );

ALTER TABLE core003.lead_ownership
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core003.lead_ownership
  FORCE ROW LEVEL SECURITY;

CREATE POLICY lead_ownership_application_access
  ON core003.lead_ownership
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY lead_ownership_tenant_guard
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

CREATE TABLE core003.ownership_transfers (
  transfer_id uuid NOT NULL,
  lead_id uuid NOT NULL,
  tenant_id uuid NOT NULL,

  previous_owner_id uuid NOT NULL,
  new_owner_id uuid NOT NULL,

  previous_revision integer NOT NULL,
  new_revision integer NOT NULL,

  reason text NOT NULL,
  transferred_at timestamp with time zone NOT NULL,
  transfer_reference text,

  CONSTRAINT ownership_transfers_pkey
    PRIMARY KEY (transfer_id),

  CONSTRAINT ownership_transfers_lead_fk
    FOREIGN KEY (tenant_id, lead_id)
    REFERENCES core003.leads (tenant_id, lead_id),

  CONSTRAINT ownership_transfers_previous_owner_check
    CHECK (previous_owner_id <> new_owner_id),

  CONSTRAINT ownership_transfers_previous_revision_check
    CHECK (previous_revision >= 0),

  CONSTRAINT ownership_transfers_new_revision_check
    CHECK (new_revision = previous_revision + 1),

  CONSTRAINT ownership_transfers_reason_check
    CHECK (
      reason IN (
        'MANUAL',
        'BUSINESS_RULE',
        'REASSIGNMENT',
        'TENANT_INTERNAL',
        'PARTNER_CHANGE'
      )
    ),

  CONSTRAINT ownership_transfers_reference_check
    CHECK (
      transfer_reference IS NULL
      OR (
        transfer_reference = btrim(transfer_reference)
        AND length(transfer_reference) > 0
      )
    ),

  CONSTRAINT ownership_transfers_revision_key
    UNIQUE (
      tenant_id,
      lead_id,
      new_revision
    )
);

CREATE INDEX ownership_transfers_tenant_time_idx
  ON core003.ownership_transfers (
    tenant_id,
    transferred_at DESC,
    transfer_id
  );

ALTER TABLE core003.ownership_transfers
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core003.ownership_transfers
  FORCE ROW LEVEL SECURITY;

CREATE POLICY ownership_transfers_application_access
  ON core003.ownership_transfers
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY ownership_transfers_tenant_guard
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

CREATE FUNCTION core003.reject_ownership_transfer_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'CORE-003 ownership transfer history is append-only'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER ownership_transfers_append_only
  BEFORE UPDATE OR DELETE
  ON core003.ownership_transfers
  FOR EACH ROW
  EXECUTE FUNCTION
    core003.reject_ownership_transfer_mutation();

REVOKE ALL ON FUNCTION
  core003.reject_ownership_transfer_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON TABLE
  core003.leads,
  core003.lead_ownership,
  core003.ownership_transfers
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core003.leads,
  core003.lead_ownership
TO __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core003.ownership_transfers
TO __HOMIO_APPLICATION_ROLE__;
