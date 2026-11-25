
BEGIN;

CREATE SCHEMA core006;

REVOKE ALL ON SCHEMA core006 FROM PUBLIC;
GRANT USAGE ON SCHEMA core006 TO __HOMIO_APPLICATION_ROLE__;

ALTER DEFAULT PRIVILEGES IN SCHEMA core006
  REVOKE ALL ON TABLES
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

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
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  history jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_of_truth text NOT NULL DEFAULT 'deal',
  offers jsonb NOT NULL DEFAULT '[]'::jsonb,
  negotiation jsonb,
  milestones jsonb NOT NULL DEFAULT '[]'::jsonb,
  ownership_binding jsonb,
  evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
  audit_log jsonb NOT NULL DEFAULT '[]'::jsonb,
  participants jsonb NOT NULL DEFAULT '[]'::jsonb,
  contract_schema_version text NOT NULL,

  CONSTRAINT core006_deals_pkey
    PRIMARY KEY (tenant_id, deal_id),

  CONSTRAINT core006_deals_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core006_deals_identifiers_check
    CHECK (
      char_length(deal_id) > 0
      AND char_length(customer_id) > 0
      AND char_length(broker_id) > 0
      AND (
        builder_id IS NULL
        OR char_length(builder_id) > 0
      )
      AND (
        project_id IS NULL
        OR char_length(project_id) > 0
      )
      AND (
        unit_id IS NULL
        OR char_length(unit_id) > 0
      )
    ),

  CONSTRAINT core006_deals_status_check
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

  CONSTRAINT core006_deals_version_check
    CHECK (version >= 1),

  CONSTRAINT core006_deals_time_order_check
    CHECK (updated_at >= created_at),

  CONSTRAINT core006_deals_source_of_truth_check
    CHECK (char_length(source_of_truth) > 0),

  CONSTRAINT core006_deals_contract_version_check
    CHECK (char_length(contract_schema_version) > 0),

  CONSTRAINT core006_deals_history_array_check
    CHECK (jsonb_typeof(history) = 'array'),

  CONSTRAINT core006_deals_offers_array_check
    CHECK (jsonb_typeof(offers) = 'array'),

  CONSTRAINT core006_deals_negotiation_object_check
    CHECK (
      negotiation IS NULL
      OR jsonb_typeof(negotiation) = 'object'
    ),

  CONSTRAINT core006_deals_milestones_array_check
    CHECK (jsonb_typeof(milestones) = 'array'),

  CONSTRAINT core006_deals_ownership_binding_object_check
    CHECK (
      ownership_binding IS NULL
      OR jsonb_typeof(ownership_binding) = 'object'
    ),

  CONSTRAINT core006_deals_evidence_array_check
    CHECK (jsonb_typeof(evidence) = 'array'),

  CONSTRAINT core006_deals_audit_log_array_check
    CHECK (jsonb_typeof(audit_log) = 'array'),

  CONSTRAINT core006_deals_participants_array_check
    CHECK (jsonb_typeof(participants) = 'array')
);

CREATE INDEX core006_deals_tenant_status_idx
  ON core006.deals (
    tenant_id,
    status,
    updated_at DESC
  );

CREATE INDEX core006_deals_tenant_customer_idx
  ON core006.deals (
    tenant_id,
    customer_id
  );

CREATE INDEX core006_deals_tenant_project_idx
  ON core006.deals (
    tenant_id,
    project_id
  )
  WHERE project_id IS NOT NULL;

CREATE TABLE core006.deal_parties (
  deal_id text NOT NULL,
  tenant_id uuid NOT NULL,
  role text NOT NULL,
  party_id text NOT NULL,
  relationship_version integer NOT NULL DEFAULT 1,
  lifecycle text NOT NULL DEFAULT 'ACTIVE',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT core006_deal_parties_pkey
    PRIMARY KEY (
      tenant_id,
      deal_id,
      role,
      party_id
    ),

  CONSTRAINT core006_deal_parties_deal_fk
    FOREIGN KEY (tenant_id, deal_id)
    REFERENCES core006.deals (
      tenant_id,
      deal_id
    )
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core006_deal_parties_role_check
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

  CONSTRAINT core006_deal_parties_lifecycle_check
    CHECK (
      lifecycle IN (
        'ACTIVE',
        'SUSPENDED',
        'REMOVED'
      )
    ),

  CONSTRAINT core006_deal_parties_version_check
    CHECK (relationship_version >= 1),

  CONSTRAINT core006_deal_parties_identifiers_check
    CHECK (
      char_length(deal_id) > 0
      AND char_length(party_id) > 0
    ),

  CONSTRAINT core006_deal_parties_metadata_object_check
    CHECK (
      jsonb_typeof(metadata) = 'object'
    )
);

CREATE INDEX core006_deal_parties_tenant_party_idx
  ON core006.deal_parties (
    tenant_id,
    party_id
  );

ALTER TABLE core006.deals
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core006.deals
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core006_deals_application_access
  ON core006.deals
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core006_deals_tenant_guard
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

ALTER TABLE core006.deal_parties
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core006.deal_parties
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core006_deal_parties_application_access
  ON core006.deal_parties
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core006_deal_parties_tenant_guard
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

REVOKE ALL ON ALL TABLES IN SCHEMA core006
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core006.deals,
  core006.deal_parties
  TO __HOMIO_APPLICATION_ROLE__;

COMMIT;
