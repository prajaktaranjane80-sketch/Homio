\set ON_ERROR_STOP on

\getenv migration_role HOMIO_MIGRATION_ROLE
\getenv application_role HOMIO_APPLICATION_ROLE

BEGIN;

CREATE SCHEMA core001
  AUTHORIZATION :"migration_role";

CREATE SCHEMA core002
  AUTHORIZATION :"migration_role";

CREATE SCHEMA core003
  AUTHORIZATION :"migration_role";

CREATE SCHEMA core004
  AUTHORIZATION :"migration_role";

CREATE SCHEMA core006
  AUTHORIZATION :"migration_role";

CREATE SCHEMA core007
  AUTHORIZATION :"migration_role";

CREATE SCHEMA core008
  AUTHORIZATION :"migration_role";

REVOKE ALL ON SCHEMA
  core001,
  core002,
  core003,
  core004,
  core006,
  core007,
  core008
FROM PUBLIC;

GRANT USAGE ON SCHEMA
  core001,
  core002,
  core003,
  core004,
  core006,
  core007,
  core008
TO :"application_role";

REVOKE CREATE ON SCHEMA
  core001,
  core002,
  core003,
  core004,
  core006,
  core007,
  core008
FROM :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core001
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core002
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core003
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core004
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core006
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core007
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core008
  REVOKE ALL ON TABLES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core001
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core002
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core003
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core004
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core006
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core007
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core008
  REVOKE ALL ON SEQUENCES
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core001
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core002
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core003
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core004
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core006
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core007
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

ALTER DEFAULT PRIVILEGES
  FOR ROLE :"migration_role"
  IN SCHEMA core008
  REVOKE EXECUTE ON FUNCTIONS
  FROM PUBLIC, :"application_role";

COMMIT;
