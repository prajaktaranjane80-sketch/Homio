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

  matched_rule_ids text[] NOT NULL DEFAULT ARRAY[]::text[],
  reasons text[] NOT NULL DEFAULT ARRAY[]::text[],
  evidence_references text[] NOT NULL DEFAULT ARRAY[]::text[],

  decided_at timestamp with time zone NOT NULL,
  schema_version integer NOT NULL,
  fingerprint text NOT NULL,

  review_state text,
  escalation_state text,

  human_review_reference text,

  decision_evidence text[] NOT NULL DEFAULT ARRAY[]::text[],

  override_reference text,
  override_authorization text,
  appeal_review_reference text,

  irreversible_action_protected boolean NOT NULL DEFAULT true,

  CONSTRAINT governance_decisions_pkey
    PRIMARY KEY (tenant_id, decision_id),

  CONSTRAINT governance_decisions_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT governance_decisions_subject_check
    CHECK (
      subject_id = btrim(subject_id)
      AND length(subject_id) > 0
    ),

  CONSTRAINT governance_decisions_correlation_check
    CHECK (
      correlation_id = btrim(correlation_id)
      AND length(correlation_id) > 0
    ),

  CONSTRAINT governance_decisions_type_check
    CHECK (
      decision_type IN (
        'CONTINUE',
        'REVIEW',
        'APPROVAL_REQUIRED',
        'ESCALATION_REQUIRED'
      )
    ),

  CONSTRAINT governance_decisions_action_class_check
    CHECK (
      action_class IN (
        'INFORMATIONAL',
        'REVIEW',
        'HIGH_RISK',
        'CRITICAL'
      )
    ),

  CONSTRAINT governance_decisions_authority_check
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

  CONSTRAINT governance_decisions_approval_authority_check
    CHECK (
      NOT approval_required
      OR required_authority IS NOT NULL
    ),

  CONSTRAINT governance_decisions_escalation_level_check
    CHECK (
      escalation_level IN (
        'NONE',
        'REVIEW',
        'HIGH',
        'CRITICAL'
      )
    ),

  CONSTRAINT governance_decisions_review_state_check
    CHECK (
      review_state IS NULL
      OR review_state IN (
        'NOT_REQUIRED',
        'PENDING',
        'UNDER_REVIEW',
        'COMPLETED'
      )
    ),

  CONSTRAINT governance_decisions_escalation_state_check
    CHECK (
      escalation_state IS NULL
      OR escalation_state IN (
        'NOT_REQUIRED',
        'OPEN',
        'ACKNOWLEDGED',
        'RESOLVED'
      )
    ),

  CONSTRAINT governance_decisions_schema_version_check
    CHECK (schema_version > 0),

  CONSTRAINT governance_decisions_fingerprint_check
    CHECK (fingerprint ~ '^[a-f0-9]{64}$')
);

CREATE INDEX governance_decisions_tenant_subject_time_idx
  ON core007.governance_decisions (
    tenant_id,
    subject_id,
    decided_at DESC
  );

CREATE INDEX governance_decisions_tenant_time_idx
  ON core007.governance_decisions (
    tenant_id,
    decided_at DESC
  );

ALTER TABLE core007.governance_decisions
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core007.governance_decisions
  FORCE ROW LEVEL SECURITY;

CREATE POLICY governance_decisions_application_access
  ON core007.governance_decisions
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY governance_decisions_tenant_guard
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

CREATE FUNCTION core007.reject_governance_decision_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'CORE-007 governance decision records are immutable'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER governance_decisions_immutable
  BEFORE UPDATE OR DELETE
  ON core007.governance_decisions
  FOR EACH ROW
  EXECUTE FUNCTION
    core007.reject_governance_decision_mutation();

REVOKE ALL ON FUNCTION
  core007.reject_governance_decision_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core007.approval_requests (
  request_id uuid NOT NULL,
  tenant_id uuid NOT NULL,

  subject_id text NOT NULL,
  correlation_id text NOT NULL,

  governance_fingerprint text NOT NULL,
  policy_id text NOT NULL,
  policy_version text NOT NULL,

  requested_at timestamp with time zone NOT NULL,
  expires_at timestamp with time zone NOT NULL,

  state text NOT NULL DEFAULT 'PENDING',

  decision_record jsonb,

  CONSTRAINT approval_requests_pkey
    PRIMARY KEY (tenant_id, request_id),

  CONSTRAINT approval_requests_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT approval_requests_subject_check
    CHECK (
      subject_id = btrim(subject_id)
      AND length(subject_id) > 0
    ),

  CONSTRAINT approval_requests_correlation_check
    CHECK (
      correlation_id = btrim(correlation_id)
      AND length(correlation_id) > 0
    ),

  CONSTRAINT approval_requests_state_check
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

  CONSTRAINT approval_requests_time_order_check
    CHECK (expires_at > requested_at),

  CONSTRAINT approval_requests_decision_record_check
    CHECK (
      decision_record IS NULL
      OR (
        jsonb_typeof(decision_record) = 'object'
        AND decision_record->>'request_id' = request_id::text
        AND decision_record ?& ARRAY[
          'state',
          'decision_at',
          'actor_reference',
          'reason',
          'fingerprint'
        ]
        AND state IN (
          'APPROVED',
          'REJECTED',
          'EXPIRED',
          'CANCELLED'
        )
      )
    )
);

CREATE INDEX approval_requests_tenant_state_expiry_idx
  ON core007.approval_requests (
    tenant_id,
    state,
    expires_at
  );

ALTER TABLE core007.approval_requests
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core007.approval_requests
  FORCE ROW LEVEL SECURITY;

CREATE POLICY approval_requests_application_access
  ON core007.approval_requests
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY approval_requests_tenant_guard
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
    OR NEW.governance_fingerprint
      IS DISTINCT FROM OLD.governance_fingerprint
    OR NEW.policy_id IS DISTINCT FROM OLD.policy_id
    OR NEW.policy_version IS DISTINCT FROM OLD.policy_version
    OR NEW.requested_at IS DISTINCT FROM OLD.requested_at
    OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
  THEN
    RAISE EXCEPTION
      'CORE-007 approval request identity is immutable'
      USING ERRCODE = '55000';
  END IF;

  IF OLD.state <> 'PENDING' THEN
    IF
      NEW.state IS DISTINCT FROM OLD.state
      OR NEW.decision_record IS DISTINCT FROM OLD.decision_record
    THEN
      RAISE EXCEPTION
        'CORE-007 terminal approval decisions cannot be rewritten'
        USING ERRCODE = '55000';
    END IF;

    RETURN NEW;
  END IF;

  IF NEW.state NOT IN (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'EXPIRED',
    'CANCELLED'
  ) THEN
    RAISE EXCEPTION
      'Invalid CORE-007 approval transition'
      USING ERRCODE = '23514';
  END IF;

  IF NEW.state = 'PENDING'
    AND NEW.decision_record IS DISTINCT FROM OLD.decision_record
  THEN
    RAISE EXCEPTION
      'A pending approval cannot contain a terminal decision record'
      USING ERRCODE = '23514';
  END IF;

  IF NEW.state <> 'PENDING'
    AND NEW.decision_record IS NULL
  THEN
    RAISE EXCEPTION
      'A terminal approval requires its ApprovalRecord'
      USING ERRCODE = '23514';
  END IF;

  RETURN NEW;
END;
$function$;

CREATE TRIGGER approval_requests_state_guard
  BEFORE UPDATE OR DELETE
  ON core007.approval_requests
  FOR EACH ROW
  EXECUTE FUNCTION
    core007.guard_approval_request_mutation();

REVOKE ALL ON FUNCTION
  core007.guard_approval_request_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON TABLE
  core007.governance_decisions,
  core007.approval_requests
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core007.governance_decisions
TO __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  core007.approval_requests
TO __HOMIO_APPLICATION_ROLE__;
