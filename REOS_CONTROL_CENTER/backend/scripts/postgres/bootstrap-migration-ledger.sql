\set ON_ERROR_STOP on
-- One-time DBA bootstrap for the infrastructure ledger required by
-- PostgresMigrationRunner. Intentionally fails if roles/schema already exist.
\getenv migration_role HOMIO_MIGRATION_ROLE
\getenv application_role HOMIO_APPLICATION_ROLE
\getenv migration_password HOMIO_MIGRATION_PASSWORD
\getenv application_password HOMIO_APPLICATION_PASSWORD

BEGIN;

CREATE ROLE :"migration_role"
  LOGIN INHERIT NOSUPERUSER NOBYPASSRLS
  PASSWORD :'migration_password';

CREATE ROLE :"application_role"
  LOGIN INHERIT NOSUPERUSER NOBYPASSRLS
  PASSWORD :'application_password';

CREATE SCHEMA reos_infra AUTHORIZATION :"migration_role";

SET ROLE :"migration_role";

CREATE TABLE reos_infra.schema_migrations (
  migration_id text NOT NULL,
  migration_name text NOT NULL,
  checksum text NOT NULL,
  applied_at timestamp with time zone NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT schema_migrations_pkey
    PRIMARY KEY (migration_id),
  CONSTRAINT schema_migrations_migration_name_key
    UNIQUE (migration_name),
  CONSTRAINT schema_migrations_migration_id_check
    CHECK (migration_id ~ '^[0-9]{8}$'),
  CONSTRAINT schema_migrations_migration_name_check
    CHECK (migration_name ~ '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'),
  CONSTRAINT schema_migrations_checksum_check
    CHECK (checksum ~ '^[a-f0-9]{64}$')
);

RESET ROLE;

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA reos_infra
  REVOKE ALL ON TABLES FROM PUBLIC, :"application_role";

REVOKE ALL ON SCHEMA reos_infra FROM PUBLIC;
REVOKE ALL ON SCHEMA reos_infra FROM :"application_role";
REVOKE ALL ON TABLE reos_infra.schema_migrations FROM PUBLIC;
REVOKE ALL ON TABLE reos_infra.schema_migrations FROM :"application_role";

COMMIT;
