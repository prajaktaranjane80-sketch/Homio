DROP TRIGGER IF EXISTS security_audit_events_truncate_guard
  ON reos_infra.security_audit_events;

CREATE TRIGGER security_audit_events_truncate_guard
  BEFORE TRUNCATE
  ON reos_infra.security_audit_events
  FOR EACH STATEMENT
  EXECUTE FUNCTION
    reos_infra.reject_security_audit_mutation();

REVOKE ALL ON TABLE
  reos_infra.security_audit_events
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE TRUNCATE ON TABLE
  reos_infra.security_audit_events
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT INSERT ON TABLE
  reos_infra.security_audit_events
TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  reos_infra.reject_security_audit_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;
