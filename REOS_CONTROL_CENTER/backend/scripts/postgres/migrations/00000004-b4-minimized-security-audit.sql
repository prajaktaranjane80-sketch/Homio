CREATE TABLE reos_infra.security_audit_events (
  event_id uuid NOT NULL,
  event_type text NOT NULL,
  request_id uuid NOT NULL,
  occurred_at timestamp with time zone NOT NULL,
  reason_code text NOT NULL,
  operation text,
  actor_identity_reference uuid,
  tenant_reference uuid,

  CONSTRAINT security_audit_events_pkey
    PRIMARY KEY (event_id),

  CONSTRAINT security_audit_events_type_check
    CHECK (
      event_type IN (
        'API_ACCESS_ALLOWED',
        'API_ACCESS_DENIED',
        'API_RATE_LIMITED',
        'API_MUTATION_REAUTHORIZED'
      )
    ),

  CONSTRAINT security_audit_events_reason_check
    CHECK (
      reason_code ~ '^[A-Z][A-Z0-9_]{0,63}$'
    ),

  CONSTRAINT security_audit_events_operation_check
    CHECK (
      operation IS NULL
      OR operation ~ '^[a-z][a-z0-9_.:-]{0,63}$'
    )
);

CREATE INDEX security_audit_events_request_time_idx
  ON reos_infra.security_audit_events (
    request_id,
    occurred_at DESC
  );

CREATE INDEX security_audit_events_time_idx
  ON reos_infra.security_audit_events (
    occurred_at DESC,
    event_id DESC
  );

CREATE INDEX security_audit_events_tenant_time_idx
  ON reos_infra.security_audit_events (
    tenant_reference,
    occurred_at DESC
  )
  WHERE tenant_reference IS NOT NULL;


CREATE FUNCTION reos_infra.reject_security_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'API security audit events are append-only'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER security_audit_events_append_only
  BEFORE UPDATE OR DELETE
  ON reos_infra.security_audit_events
  FOR EACH ROW
  EXECUTE FUNCTION
    reos_infra.reject_security_audit_mutation();


REVOKE ALL ON TABLE reos_infra.security_audit_events
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT INSERT
  ON TABLE reos_infra.security_audit_events
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  reos_infra.reject_security_audit_mutation()
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;
