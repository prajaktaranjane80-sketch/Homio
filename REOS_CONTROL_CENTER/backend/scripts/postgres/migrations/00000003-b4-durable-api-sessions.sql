CREATE TABLE reos_infra.api_sessions (
  session_id uuid NOT NULL,
  tenant_id uuid NOT NULL,
  account_id uuid NOT NULL,
  identity_id uuid NOT NULL,
  tenant_revision integer NOT NULL,
  organization_id uuid NOT NULL,
  membership_id uuid NOT NULL,
  membership_revision integer NOT NULL,
  issuer_digest text NOT NULL,
  token_id_digest text NOT NULL,
  authentication_epoch bigint NOT NULL,
  issued_at timestamp with time zone NOT NULL,
  expires_at timestamp with time zone NOT NULL,
  revoked_at timestamp with time zone,
  revocation_reason_code text,

  CONSTRAINT api_sessions_pkey
    PRIMARY KEY (session_id),

  CONSTRAINT api_sessions_token_identity_key
    UNIQUE (
      tenant_id,
      issuer_digest,
      token_id_digest
    ),

  CONSTRAINT api_sessions_tenant_revision_check
    CHECK (tenant_revision > 0),

  CONSTRAINT api_sessions_membership_revision_check
    CHECK (membership_revision > 0),

  CONSTRAINT api_sessions_authentication_epoch_check
    CHECK (authentication_epoch > 0),

  CONSTRAINT api_sessions_issuer_digest_check
    CHECK (issuer_digest ~ '^[a-f0-9]{64}$'),

  CONSTRAINT api_sessions_token_digest_check
    CHECK (token_id_digest ~ '^[a-f0-9]{64}$'),

  CONSTRAINT api_sessions_time_order_check
    CHECK (expires_at > issued_at),

  CONSTRAINT api_sessions_revocation_pair_check
    CHECK (
      (revoked_at IS NULL AND revocation_reason_code IS NULL)
      OR
      (
        revoked_at IS NOT NULL
        AND revocation_reason_code IS NOT NULL
        AND revocation_reason_code ~ '^[A-Z][A-Z0-9_]{0,63}$'
      )
    ),

  CONSTRAINT api_sessions_revocation_time_check
    CHECK (
      revoked_at IS NULL
      OR revoked_at >= issued_at
    )
);

CREATE INDEX api_sessions_active_account_idx
  ON reos_infra.api_sessions (
    tenant_id,
    account_id,
    expires_at
  )
  WHERE revoked_at IS NULL;

CREATE INDEX api_sessions_expiry_idx
  ON reos_infra.api_sessions (expires_at)
  WHERE revoked_at IS NULL;


CREATE FUNCTION reos_infra.guard_api_session_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION
      'API session records cannot be deleted'
      USING ERRCODE = '55000';
  END IF;

  IF
    NEW.session_id IS DISTINCT FROM OLD.session_id
    OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
    OR NEW.account_id IS DISTINCT FROM OLD.account_id
    OR NEW.identity_id IS DISTINCT FROM OLD.identity_id
    OR NEW.tenant_revision IS DISTINCT FROM OLD.tenant_revision
    OR NEW.organization_id IS DISTINCT FROM OLD.organization_id
    OR NEW.membership_id IS DISTINCT FROM OLD.membership_id
    OR NEW.membership_revision IS DISTINCT FROM OLD.membership_revision
    OR NEW.issuer_digest IS DISTINCT FROM OLD.issuer_digest
    OR NEW.token_id_digest IS DISTINCT FROM OLD.token_id_digest
    OR NEW.authentication_epoch IS DISTINCT FROM OLD.authentication_epoch
    OR NEW.issued_at IS DISTINCT FROM OLD.issued_at
    OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
  THEN
    RAISE EXCEPTION
      'API session identity and authentication binding are immutable'
      USING ERRCODE = '55000';
  END IF;

  IF OLD.revoked_at IS NOT NULL THEN
    IF
      NEW.revoked_at IS DISTINCT FROM OLD.revoked_at
      OR NEW.revocation_reason_code
        IS DISTINCT FROM OLD.revocation_reason_code
    THEN
      RAISE EXCEPTION
        'API session revocation cannot be reversed or rewritten'
        USING ERRCODE = '55000';
    END IF;

    RETURN NEW;
  END IF;

  IF NEW.revoked_at IS NULL THEN
    IF NEW.revocation_reason_code IS NOT NULL THEN
      RAISE EXCEPTION
        'A revocation reason requires a revocation timestamp'
        USING ERRCODE = '55000';
    END IF;

    RETURN NEW;
  END IF;

  IF NEW.revocation_reason_code IS NULL THEN
    RAISE EXCEPTION
      'API session revocation requires a reason code'
      USING ERRCODE = '23514';
  END IF;

  RETURN NEW;
END;
$function$;

CREATE TRIGGER api_sessions_immutable_identity
  BEFORE UPDATE OR DELETE
  ON reos_infra.api_sessions
  FOR EACH ROW
  EXECUTE FUNCTION
    reos_infra.guard_api_session_mutation();


ALTER TABLE reos_infra.api_sessions
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE reos_infra.api_sessions
  FORCE ROW LEVEL SECURITY;


CREATE POLICY api_sessions_application_access
  ON reos_infra.api_sessions
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);


CREATE POLICY api_sessions_tenant_guard
  ON reos_infra.api_sessions
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


REVOKE ALL ON SCHEMA reos_infra
  FROM PUBLIC;

GRANT USAGE ON SCHEMA reos_infra
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON TABLE reos_infra.api_sessions
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE
  ON TABLE reos_infra.api_sessions
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  reos_infra.guard_api_session_mutation()
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;
