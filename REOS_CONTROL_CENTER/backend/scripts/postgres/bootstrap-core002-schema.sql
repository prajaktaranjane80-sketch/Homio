\set ON_ERROR_STOP on

\getenv migration_role HOMIO_POSTGRES_MIGRATION_ROLE
\getenv application_role HOMIO_APPLICATION_ROLE
\getenv schema_name HOMIO_POSTGRES_SCHEMA

BEGIN;

CREATE SCHEMA :"schema_name"
  AUTHORIZATION :"migration_role";

REVOKE ALL ON SCHEMA :"schema_name" FROM PUBLIC;

GRANT USAGE ON SCHEMA :"schema_name"
  TO :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA :"schema_name"
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

COMMIT;
