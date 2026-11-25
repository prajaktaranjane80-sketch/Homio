CREATE TABLE core006.deals (
  deal_id text NOT NULL,
  tenant_id uuid NOT NULL,

  customer_id text NOT NULL,
  broker_id text NOT NULL,

  builder_id text,
  project_id text,
  unit_id text,

  status text NOT NULL,
  version integer NOT NULL,

  created_at timestamp with time zone NOT NULL,
  updated_at timestamp with time zone NOT NULL,

  history jsonb NOT NULL DEFAULT '[]'::jsonb,

  source_of_truth text NOT NULL DEFAULT 'deal',

  offers jsonb NOT NULL DEFAULT '[]'::jsonb,
  negotiation jsonb,
  milestones jsonb NOT NULL DEFAULT '[]'::jsonb,
  ownership_binding jsonb,
  evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
  audit_log jsonb NOT NULL DEFAULT '[]'::jsonb,

  contract_schema_version text NOT NULL DEFAULT '1.0',

  CONSTRAINT deals_pkey
    PRIMARY KEY (tenant_id, deal_id),

  CONSTRAINT deals_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT deals_deal_id_check
    CHECK (
      deal_id = btrim(deal_id)
      AND length(deal_id) > 0
    ),

  CONSTRAINT deals_customer_id_check
    CHECK (
      customer_id = btrim(customer_id)
      AND length(customer_id) > 0
    ),

  CONSTRAINT deals_broker_id_check
    CHECK (
      broker_id = btrim(broker_id)
      AND length(broker_id) > 0
    ),

  CONSTRAINT deals_builder_id_check
    CHECK (
      builder_id IS NULL
      OR (
        builder_id = btrim(builder_id)
        AND length(builder_id) > 0
      )
    ),

  CONSTRAINT deals_project_id_check
    CHECK (
      project_id IS NULL
      OR (
        project_id = btrim(project_id)
        AND length(project_id) > 0
      )
    ),

  CONSTRAINT deals_unit_id_check
    CHECK (
      unit_id IS NULL
      OR (
        unit_id = btrim(unit_id)
        AND length(unit_id) > 0
      )
    ),

  CONSTRAINT deals_status_check
    CHECK (
      status IN (
        'QUALIFIED',
        'MATCHED',
        'VISIT_PENDING',
        'VISITED',
        'OFFERED',
        'NEGOTIATING',
        'BOOKING_PENDING',
        'BOOKED',
        'AGREEMENT_PENDING',
        'AGREED',
        'REGISTRATION_PENDING',
        'REGISTERED',
        'COMPLETION_PENDING',
        'COMPLETED',
        'CANCELLED',
        'EXPIRED',
        'REJECTED',
        'DISPUTED',
        'FRAUD_BLOCKED'
      )
    ),

  CONSTRAINT deals_version_check
    CHECK (version > 0),

  CONSTRAINT deals_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT deals_history_array_check
    CHECK (jsonb_typeof(history) = 'array'),

  CONSTRAINT deals_source_of_truth_check
    CHECK (source_of_truth = 'deal'),

  CONSTRAINT deals_offers_array_check
    CHECK (jsonb_typeof(offers) = 'array'),

  CONSTRAINT deals_negotiation_object_check
    CHECK (
      negotiation IS NULL
      OR jsonb_typeof(negotiation) = 'object'
    ),

  CONSTRAINT deals_milestones_array_check
    CHECK (jsonb_typeof(milestones) = 'array'),

  CONSTRAINT deals_ownership_binding_object_check
    CHECK (
      ownership_binding IS NULL
      OR jsonb_typeof(ownership_binding) = 'object'
    ),

  CONSTRAINT deals_evidence_array_check
    CHECK (jsonb_typeof(evidence) = 'array'),

  CONSTRAINT deals_audit_log_array_check
    CHECK (jsonb_typeof(audit_log) = 'array'),

  CONSTRAINT deals_contract_schema_version_check
    CHECK (
      contract_schema_version = btrim(contract_schema_version)
      AND length(contract_schema_version) > 0
    )
);

CREATE INDEX deals_tenant_status_updated_idx
  ON core006.deals (
    tenant_id,
    status,
    updated_at DESC
  );

CREATE INDEX deals_tenant_customer_idx
  ON core006.deals (
    tenant_id,
    customer_id
  );

CREATE INDEX deals_tenant_broker_idx
  ON core006.deals (
    tenant_id,
    broker_id
  );

ALTER TABLE core006.deals
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core006.deals
  FORCE ROW LEVEL SECURITY;

CREATE POLICY deals_application_access
  ON core006.deals
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY deals_tenant_guard
  ON core006.deals
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

CREATE TABLE core006.deal_parties (
  deal_id text NOT NULL,
  tenant_id uuid NOT NULL,

  role text NOT NULL,
  party_id text NOT NULL,

  relationship_version integer NOT NULL DEFAULT 1,
  lifecycle text NOT NULL DEFAULT 'ACTIVE',

  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT deal_parties_pkey
    PRIMARY KEY (
      tenant_id,
      deal_id,
      role,
      party_id
    ),

  CONSTRAINT deal_parties_deal_fk
    FOREIGN KEY (tenant_id, deal_id)
    REFERENCES core006.deals (
      tenant_id,
      deal_id
    ),

  CONSTRAINT deal_parties_role_check
    CHECK (
      role IN (
        'BUYER',
        'CUSTOMER',
        'SELLER',
        'BUILDER',
        'BROKER',
        'REPRESENTATIVE'
      )
    ),

  CONSTRAINT deal_parties_party_id_check
    CHECK (
      party_id = btrim(party_id)
      AND length(party_id) > 0
    ),

  CONSTRAINT deal_parties_relationship_version_check
    CHECK (relationship_version > 0),

  CONSTRAINT deal_parties_lifecycle_check
    CHECK (
      lifecycle IN (
        'ACTIVE',
        'SUSPENDED',
        'REMOVED'
      )
    ),

  CONSTRAINT deal_parties_metadata_object_check
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX deal_parties_tenant_party_idx
  ON core006.deal_parties (
    tenant_id,
    party_id
  );

ALTER TABLE core006.deal_parties
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core006.deal_parties
  FORCE ROW LEVEL SECURITY;

CREATE POLICY deal_parties_application_access
  ON core006.deal_parties
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY deal_parties_tenant_guard
  ON core006.deal_parties
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
  core006.deals,
  core006.deal_parties
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core006.deals,
  core006.deal_parties
TO __HOMIO_APPLICATION_ROLE__;
