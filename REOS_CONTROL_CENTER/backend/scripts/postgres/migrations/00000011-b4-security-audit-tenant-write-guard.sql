
BEGIN;

ALTER TABLE reos_infra.security_audit_events
  ADD CONSTRAINT security_audit_events_tenant_reference_fk
  FOREIGN KEY (tenant_reference)
  REFERENCES core001.tenants (tenant_id)
  ON UPDATE RESTRICT
  ON DELETE RESTRICT
  NOT VALID;

ALTER TABLE reos_infra.security_audit_events
  VALIDATE CONSTRAINT security_audit_events_tenant_reference_fk;

COMMIT;
