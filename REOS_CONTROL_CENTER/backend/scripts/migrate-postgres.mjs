import { createRequire } from "node:module";
import { resolve } from "node:path";

import {
  loadPostgresMigrationManifest
} from "../dist/persistence/postgres-migration-manifest.js";

import {
  PostgresMigrationRunner
} from "../dist/persistence/postgres-migrations.js";

const require = createRequire(import.meta.url);
const { Pool } = require("pg");

const ROLE_PATTERN = /^[a-z_][a-z0-9_$]{0,62}$/;

function fail(message) {
  throw new Error(message);
}

function readDatabaseUrl(name) {
  const value = process.env[name];

  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value !== value.trim()
  ) {
    fail(`${name} is required.`);
  }

  let url;

  try {
    url = new URL(value);
  } catch {
    fail(`${name} must be a valid PostgreSQL URL.`);
  }

  if (
    !["postgres:", "postgresql:"].includes(url.protocol) ||
    !url.hostname ||
    !url.username ||
    !url.password ||
    url.pathname.length < 2 ||
    url.search.length > 0 ||
    url.hash.length > 0
  ) {
    fail(`${name} has an invalid PostgreSQL connection contract.`);
  }

  return { value, url };
}

function readRole(url, environmentName) {
  const role = decodeURIComponent(url.username);
  const configured = process.env[environmentName];

  if (
    !ROLE_PATTERN.test(role) ||
    (configured !== undefined && configured !== role)
  ) {
    fail(`${environmentName} does not match the URL login role.`);
  }

  return role;
}

function sameDatabase(left, right) {
  const leftPort = left.port || "5432";
  const rightPort = right.port || "5432";

  return (
    left.hostname.toLowerCase() === right.hostname.toLowerCase() &&
    leftPort === rightPort &&
    left.pathname === right.pathname
  );
}

function buildSslConfiguration() {
  const nodeEnv = process.env.NODE_ENV ?? "development";
  const defaultMode = nodeEnv === "production"
    ? "verify-full"
    : "disable";

  const mode = process.env.HOMIO_POSTGRES_SSL_MODE ?? defaultMode;

  if (mode !== "disable" && mode !== "verify-full") {
    fail("HOMIO_POSTGRES_SSL_MODE must be disable or verify-full.");
  }

  if (nodeEnv === "production" && mode !== "verify-full") {
    fail("Production PostgreSQL migrations require verify-full TLS.");
  }

  if (mode === "disable") {
    return false;
  }

  const ca = process.env.HOMIO_POSTGRES_CA_CERT;

  if (
    ca !== undefined &&
    (
      !ca.includes("-----BEGIN CERTIFICATE-----") ||
      !ca.includes("-----END CERTIFICATE-----")
    )
  ) {
    fail("HOMIO_POSTGRES_CA_CERT must contain PEM certificate data.");
  }

  return {
    rejectUnauthorized: true,
    ...(ca === undefined ? {} : { ca })
  };
}

async function run() {
  const application = readDatabaseUrl("HOMIO_POSTGRES_URL");
  const migration = readDatabaseUrl(
    "HOMIO_POSTGRES_MIGRATION_URL"
  );

  if (!sameDatabase(application.url, migration.url)) {
    fail(
      "Application and migration URLs must target the same PostgreSQL database."
    );
  }

  const applicationRole = readRole(
    application.url,
    "HOMIO_APPLICATION_ROLE"
  );

  const migrationRole = readRole(
    migration.url,
    "HOMIO_POSTGRES_MIGRATION_ROLE"
  );

  if (applicationRole === migrationRole) {
    fail(
      "The PostgreSQL migration role must be distinct from the application role."
    );
  }

  // The current CORE-002 repository is intentionally bound to this
  // canonical schema. A different schema requires a matching repository
  // owner, not merely a deployment environment-variable override.
  const schemaName = process.env.HOMIO_POSTGRES_SCHEMA ?? "core002";

  if (schemaName !== "core002") {
    fail("HOMIO_POSTGRES_SCHEMA must be core002.");
  }

  const ssl = buildSslConfiguration();

  const pool = new Pool({
    connectionString: migration.value,
    max: 1,
    connectionTimeoutMillis: 5000,
    idleTimeoutMillis: 5000,
    statement_timeout: 30000,
    ssl,
    allowExitOnIdle: false
  });

  try {
    const schemaResult = await pool.query(
      `
        SELECT
          session_user::text AS session_user,
          current_user::text AS current_user,
          pg_get_userbyid(namespace.nspowner) AS schema_owner,
          has_schema_privilege(
            current_user,
            namespace.oid,
            'CREATE'
          ) AS can_create
        FROM pg_namespace AS namespace
        WHERE namespace.nspname = $1
      `,
      [schemaName]
    );

    const schema = schemaResult.rows[0];

    if (
      schema === undefined ||
      schema.session_user !== migrationRole ||
      schema.current_user !== migrationRole ||
      schema.schema_owner !== migrationRole ||
      schema.can_create !== true
    ) {
      fail(
        "The dedicated migration login must own the pre-provisioned CORE-002 schema and have CREATE privilege."
      );
    }

    const migrations = await loadPostgresMigrationManifest(
      resolve(import.meta.dirname, "postgres", "migrations"),
      {
        migrationRole,
        applicationRole,
        schemaName
      }
    );

    const runner = new PostgresMigrationRunner(
      pool,
      {
        migrationRole,
        applicationRole
      }
    );

    const report = await runner.migrate(migrations);

    process.stdout.write(
      [
        "HOMIO PostgreSQL migrations verified.",
        `Applied: ${report.appliedCount}`,
        `Latest migration: ${report.latestMigrationId}`,
        `Latest checksum: ${report.latestChecksum}`,
        ""
      ].join("\n")
    );
  } finally {
    await pool.end();
  }
}

run().catch(() => {
  process.stderr.write(
    "HOMIO PostgreSQL migration failed. Review the migration-role, schema, manifest and database logs; no automatic retry is performed.\n"
  );
  process.exitCode = 1;
});
