\set ON_ERROR_STOP on

\getenv migration_role HOMIO_MIGRATION_ROLE
\getenv application_role HOMIO_APPLICATION_ROLE

BEGIN;

CREATE SCHEMA core002
  AUTHORIZATION :"migration_role";

REVOKE ALL ON SCHEMA core002 FROM PUBLIC;

GRANT USAGE ON SCHEMA core002
  TO :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core002
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

COMMIT;
