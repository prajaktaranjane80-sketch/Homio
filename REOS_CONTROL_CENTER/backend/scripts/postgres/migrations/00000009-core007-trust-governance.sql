
BEGIN;

CREATE SCHEMA core007;

REVOKE ALL ON SCHEMA core007 FROM PUBLIC;
GRANT USAGE ON SCHEMA core007 TO __HOMIO_APPLICATION_ROLE__;

ALTER DEFAULT PRIVILEGES IN SCHEMA core007
  REVOKE ALL ON TABLES
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core007.governance_decisions (
  decision_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  subject_id text NOT NULL,
  correlation_id text NOT NULL,
  policy_id text NOT NULL,
  policy_version text NOT NULL,
  policy_fingerprint text NOT NULL,
  source_evaluation_fingerprint text NOT NULL,
  decision_type text NOT NULL,
  action_class text NOT NULL,
  approval_required boolean NOT NULL,
  required_authority text,
  escalation_level text NOT NULL,
  matched_rule_ids text[] NOT NULL,
  reasons text[] NOT NULL,
  evidence_references text[] NOT NULL,
  decided_at timestamptz NOT NULL,
  schema_version integer NOT NULL,
  fingerprint text NOT NULL,
  review_state text NOT NULL,
  escalation_state text NOT NULL,
  human_review_reference text,
  decision_evidence text[] NOT NULL DEFAULT ARRAY[]::text[],
  override_reference text,
  override_authorization text,
  appeal_review_reference text,
  irreversible_action_protected boolean NOT NULL DEFAULT true,

  CONSTRAINT core007_governance_decisions_pkey
    PRIMARY KEY (decision_id),

  CONSTRAINT core007_governance_decisions_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core007_governance_decisions_identifiers_check
    CHECK (
      char_length(subject_id) > 0
      AND char_length(correlation_id) > 0
      AND char_length(policy_id) > 0
      AND char_length(policy_version) > 0
      AND char_length(policy_fingerprint) > 0
      AND char_length(source_evaluation_fingerprint) > 0
    ),

  CONSTRAINT core007_governance_decisions_type_check
    CHECK (
      decision_type IN (
        'CONTINUE',
        'REVIEW',
        'APPROVAL_REQUIRED',
        'ESCALATION_REQUIRED'
      )
    ),

  CONSTRAINT core007_governance_decisions_action_class_check
    CHECK (
      action_class IN (
        'INFORMATIONAL',
        'REVIEW',
        'HIGH_RISK',
        'CRITICAL'
      )
    ),

  CONSTRAINT core007_governance_decisions_authority_check
    CHECK (
      required_authority IS NULL
      OR required_authority IN (
        'STANDARD_REVIEW',
        'SENIOR_REVIEW',
        'COMPLIANCE',
        'SECURITY',
        'FINANCIAL',
        'EXECUTIVE'
      )
    ),

  CONSTRAINT core007_governance_decisions_escalation_level_check
    CHECK (
      escalation_level IN (
        'NONE',
        'REVIEW',
        'HIGH',
        'CRITICAL'
      )
    ),

  CONSTRAINT core007_governance_decisions_review_state_check
    CHECK (
      review_state IN (
        'NOT_REQUIRED',
        'PENDING',
        'UNDER_REVIEW',
        'COMPLETED'
      )
    ),

  CONSTRAINT core007_governance_decisions_escalation_state_check
    CHECK (
      escalation_state IN (
        'NOT_REQUIRED',
        'OPEN',
        'ACKNOWLEDGED',
        'RESOLVED'
      )
    ),

  CONSTRAINT core007_governance_decisions_approval_authority_check
    CHECK (
      NOT approval_required
      OR required_authority IS NOT NULL
    ),

  CONSTRAINT core007_governance_decisions_approval_type_check
    CHECK (
      decision_type <> 'APPROVAL_REQUIRED'
      OR approval_required
    ),

  CONSTRAINT core007_governance_decisions_escalation_type_check
    CHECK (
      decision_type <> 'ESCALATION_REQUIRED'
      OR escalation_level <> 'NONE'
    ),

  CONSTRAINT core007_governance_decisions_schema_version_check
    CHECK (schema_version >= 1),

  CONSTRAINT core007_governance_decisions_fingerprint_check
    CHECK (fingerprint ~ '^[a-f0-9]{64}$'),

  CONSTRAINT core007_governance_decisions_optional_reference_check
    CHECK (
      (human_review_reference IS NULL OR char_length(human_review_reference) > 0)
      AND (override_reference IS NULL OR char_length(override_reference) > 0)
      AND (override_authorization IS NULL OR char_length(override_authorization) > 0)
      AND (appeal_review_reference IS NULL OR char_length(appeal_review_reference) > 0)
    )
);

CREATE INDEX core007_governance_decisions_tenant_subject_idx
  ON core007.governance_decisions (
    tenant_id,
    subject_id
  );

CREATE INDEX core007_governance_decisions_tenant_time_idx
  ON core007.governance_decisions (
    tenant_id,
    decided_at DESC
  );

CREATE TABLE core007.approval_requests (
  request_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  subject_id text NOT NULL,
  correlation_id text NOT NULL,
  governance_fingerprint text NOT NULL,
  policy_id text NOT NULL,
  policy_version text NOT NULL,
  requested_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  state text NOT NULL DEFAULT 'PENDING',

  CONSTRAINT core007_approval_requests_pkey
    PRIMARY KEY (request_id),

  CONSTRAINT core007_approval_requests_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core007_approval_requests_identifiers_check
    CHECK (
      char_length(subject_id) > 0
      AND char_length(correlation_id) > 0
      AND char_length(governance_fingerprint) > 0
      AND char_length(policy_id) > 0
      AND char_length(policy_version) > 0
    ),

  CONSTRAINT core007_approval_requests_state_check
    CHECK (
      state IN (
        'NOT_REQUIRED',
        'PENDING',
        'APPROVED',
        'REJECTED',
        'EXPIRED',
        'CANCELLED'
      )
    ),

  CONSTRAINT core007_approval_requests_time_order_check
    CHECK (expires_at > requested_at)
);

CREATE INDEX core007_approval_requests_tenant_state_expiry_idx
  ON core007.approval_requests (
    tenant_id,
    state,
    expires_at
  );

CREATE INDEX core007_approval_requests_tenant_subject_idx
  ON core007.approval_requests (
    tenant_id,
    subject_id
  );

CREATE FUNCTION core007.guard_approval_request_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION
      'CORE-007 approval requests cannot be deleted'
      USING ERRCODE = '55000';
  END IF;

  IF
    NEW.request_id IS DISTINCT FROM OLD.request_id
    OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
    OR NEW.subject_id IS DISTINCT FROM OLD.subject_id
    OR NEW.correlation_id IS DISTINCT FROM OLD.correlation_id
    OR NEW.governance_fingerprint IS DISTINCT FROM OLD.governance_fingerprint
    OR NEW.policy_id IS DISTINCT FROM OLD.policy_id
    OR NEW.policy_version IS DISTINCT FROM OLD.policy_version
    OR NEW.requested_at IS DISTINCT FROM OLD.requested_at
    OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
  THEN
    RAISE EXCEPTION
      'CORE-007 approval request identity is immutable'
      USING ERRCODE = '55000';
  END IF;

  IF NEW.state = OLD.state THEN
    RETURN NEW;
  END IF;

  IF OLD.state <> 'PENDING'
    OR NEW.state NOT IN (
      'APPROVED',
      'REJECTED',
      'EXPIRED',
      'CANCELLED'
    )
  THEN
    RAISE EXCEPTION
      'Invalid CORE-007 approval request state transition: % -> %',
      OLD.state,
      NEW.state
      USING ERRCODE = '55000';
  END IF;

  RETURN NEW;
END;
$function$;

CREATE TRIGGER core007_approval_requests_mutation_guard
  BEFORE UPDATE OR DELETE
  ON core007.approval_requests
  FOR EACH ROW
  EXECUTE FUNCTION core007.guard_approval_request_mutation();

ALTER TABLE core007.governance_decisions
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core007.governance_decisions
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core007_governance_decisions_application_access
  ON core007.governance_decisions
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core007_governance_decisions_tenant_guard
  ON core007.governance_decisions
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

ALTER TABLE core007.approval_requests
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core007.approval_requests
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core007_approval_requests_application_access
  ON core007.approval_requests
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core007_approval_requests_tenant_guard
  ON core007.approval_requests
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

REVOKE ALL ON ALL TABLES IN SCHEMA core007
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core007.governance_decisions
  TO __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core007.approval_requests
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  core007.guard_approval_request_mutation()
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

COMMIT;
