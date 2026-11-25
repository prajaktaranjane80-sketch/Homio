/*
 * B4 Phase 3 — minimized security audit database boundary.
 *
 * The application role receives EXECUTE on one narrowly-scoped append
 * function. It does not receive direct table INSERT, SELECT, UPDATE,
 * DELETE or TRUNCATE access.
 *
 * Tenant-scoped writes must match the transaction-local app.tenant_id
 * established by PostgresRuntime. Global events are accepted only when
 * both actor and tenant references are NULL and no tenant context exists.
 *
 * The append function is owned by the migration role that executes this
 * migration. SECURITY DEFINER is restricted by a fixed pg_catalog search_path
 * and fully-qualified table/function references.
 */

CREATE FUNCTION reos_infra.enforce_security_audit_tenant_context()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog
AS $function$
DECLARE
  tenant_context text;
BEGIN
  tenant_context :=
    NULLIF(
      pg_catalog.current_setting('app.tenant_id', true),
      ''
    );

  IF
    NEW.tenant_reference IS NULL
    AND NEW.actor_identity_reference IS NULL
  THEN
    IF tenant_context IS NOT NULL THEN
      RAISE EXCEPTION
        'Global security audit events cannot carry tenant context'
        USING ERRCODE = '42501';
    END IF;

    RETURN NEW;
  END IF;

  IF
    NEW.tenant_reference IS NULL
    OR NEW.actor_identity_reference IS NULL
    OR tenant_context IS NULL
  THEN
    RAISE EXCEPTION
      'Security audit actor and tenant references require a tenant context'
      USING ERRCODE = '42501';
  END IF;

  IF NOT pg_catalog.pg_input_is_valid(tenant_context, 'uuid') THEN
    RAISE EXCEPTION
      'Security audit tenant context must be a valid UUID'
      USING ERRCODE = '42501';
  END IF;

  IF tenant_context::uuid IS DISTINCT FROM NEW.tenant_reference THEN
    RAISE EXCEPTION
      'Security audit tenant reference does not match transaction context'
      USING ERRCODE = '42501';
  END IF;

  RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS security_audit_events_tenant_context_guard
  ON reos_infra.security_audit_events;

CREATE TRIGGER security_audit_events_tenant_context_guard
  BEFORE INSERT
  ON reos_infra.security_audit_events
  FOR EACH ROW
  EXECUTE FUNCTION
    reos_infra.enforce_security_audit_tenant_context();


CREATE FUNCTION reos_infra.append_security_audit_event(
  p_event_id uuid,
  p_event_type text,
  p_request_id uuid,
  p_occurred_at timestamptz,
  p_reason_code text,
  p_operation text,
  p_actor_identity_reference uuid,
  p_tenant_reference uuid
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE
  tenant_context text;
BEGIN
  tenant_context :=
    NULLIF(
      pg_catalog.current_setting('app.tenant_id', true),
      ''
    );

  /*
   * A global event must have both references NULL and must run without
   * a tenant context. A partially-scoped event is never accepted.
   */
  IF
    p_tenant_reference IS NULL
    OR p_actor_identity_reference IS NULL
  THEN
    IF
      p_tenant_reference IS NOT NULL
      OR p_actor_identity_reference IS NOT NULL
    THEN
      RAISE EXCEPTION
        'Security audit actor and tenant references must be supplied together'
        USING ERRCODE = '42501';
    END IF;

    IF tenant_context IS NOT NULL THEN
      RAISE EXCEPTION
        'Global security audit events cannot carry tenant context'
        USING ERRCODE = '42501';
    END IF;
  ELSE
    IF tenant_context IS NULL THEN
      RAISE EXCEPTION
        'Tenant-scoped security audit writes require transaction context'
        USING ERRCODE = '42501';
    END IF;

    IF NOT pg_catalog.pg_input_is_valid(tenant_context, 'uuid') THEN
      RAISE EXCEPTION
        'Security audit tenant context must be a valid UUID'
        USING ERRCODE = '42501';
    END IF;

    IF tenant_context::uuid IS DISTINCT FROM p_tenant_reference THEN
      RAISE EXCEPTION
        'Security audit tenant reference does not match transaction context'
        USING ERRCODE = '42501';
    END IF;
  END IF;

  INSERT INTO reos_infra.security_audit_events (
    event_id,
    event_type,
    request_id,
    occurred_at,
    reason_code,
    operation,
    actor_identity_reference,
    tenant_reference
  )
  VALUES (
    p_event_id,
    p_event_type,
    p_request_id,
    p_occurred_at,
    p_reason_code,
    p_operation,
    p_actor_identity_reference,
    p_tenant_reference
  );
END;
$function$;


DROP TRIGGER IF EXISTS security_audit_events_truncate_guard
  ON reos_infra.security_audit_events;

CREATE TRIGGER security_audit_events_truncate_guard
  BEFORE TRUNCATE
  ON reos_infra.security_audit_events
  FOR EACH STATEMENT
  EXECUTE FUNCTION
    reos_infra.reject_security_audit_mutation();


/*
 * Remove all direct table capabilities from the application role.
 * The append function is the sole application write path.
 */
REVOKE ALL ON TABLE
  reos_infra.security_audit_events
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE TRUNCATE ON TABLE
  reos_infra.security_audit_events
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;


/*
 * Trigger functions are internal database mechanisms, not callable
 * application APIs.
 */
REVOKE ALL ON FUNCTION
  reos_infra.enforce_security_audit_tenant_context()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  reos_infra.reject_security_audit_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;


/*
 * The SECURITY DEFINER append function is owned by the migration role.
 * Its fixed search_path and fully-qualified INSERT protect its execution
 * context. Only the application role receives EXECUTE.
 */
REVOKE ALL ON FUNCTION
  reos_infra.append_security_audit_event(
    uuid,
    text,
    uuid,
    timestamptz,
    text,
    text,
    uuid,
    uuid
  )
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT EXECUTE ON FUNCTION
  reos_infra.append_security_audit_event(
    uuid,
    text,
    uuid,
    timestamptz,
    text,
    text,
    uuid,
    uuid
  )
TO __HOMIO_APPLICATION_ROLE__;
