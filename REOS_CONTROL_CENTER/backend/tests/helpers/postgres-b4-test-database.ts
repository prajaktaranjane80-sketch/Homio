import { randomBytes } from "node:crypto";
import { fileURLToPath } from "node:url";

import { Pool } from "pg";

import {
  PostgresRuntime,
  type PostgresDriverPool
} from "../../src/persistence/postgres.js";

import {
  loadPostgresMigrationManifest
} from "../../src/persistence/postgres-migration-manifest.js";

import {
  PostgresMigrationRunner
} from "../../src/persistence/postgres-migrations.js";

const ADMIN_URL_ENV = "HOMIO_TEST_POSTGRES_ADMIN_URL";
const MINIMUM_POSTGRES_VERSION = 180004;

interface ServerVersionRow {
  readonly server_version_num: number;
}

interface ActivityRow {
  readonly pid: number;
  readonly application_name: string | null;
  readonly state: string | null;
}

interface MigrationLedgerRow {
  readonly migration_id: string;
  readonly migration_name: string;
  readonly checksum: string;
}

export interface B4PostgresTestDatabase {
  readonly databaseName: string;
  readonly applicationRole: string;
  readonly adminPool: Pool;
  readonly applicationPool: Pool;
  readonly runtime: PostgresRuntime;
  close(): Promise<void>;
}

function quoteIdentifier(value: string): string {
  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) {
    throw new TypeError("A safe PostgreSQL identifier is required.");
  }

  return `"${value}"`;
}

function quoteLiteral(value: string): string {
  return `'${value.replaceAll("'", "''")}'`;
}

function connectionUrl(
  source: string,
  username: string,
  password: string,
  databaseName: string
): string {
  const url = new URL(source);

  url.username = username;
  url.password = password;
  url.pathname = `/${databaseName}`;

  return url.toString();
}

function toError(value: unknown): Error {
  return value instanceof Error
    ? value
    : new Error("PostgreSQL test database operation failed.", {
        cause: value
      });
}

async function waitForDatabaseConnectionsToClose(
  pool: Pool,
  databaseName: string
): Promise<void> {
  const deadline = Date.now() + 10_000;

  let remaining: readonly ActivityRow[] = [];

  do {
    const result = await pool.query<ActivityRow>(
      `
        SELECT
          pid::integer AS pid,
          application_name,
          state
        FROM pg_stat_activity
        WHERE datname = $1
          AND pid <> pg_backend_pid()
        ORDER BY pid
      `,
      [databaseName]
    );

    remaining = result.rows;

    if (remaining.length === 0) {
      return;
    }

    await new Promise<void>((resolveWait) => {
      setTimeout(resolveWait, 25);
    });
  } while (Date.now() < deadline);

  throw new Error(
    "PostgreSQL test database still has active client sessions: " +
    JSON.stringify(remaining)
  );
}

export async function createB4PostgresTestDatabase():
Promise<B4PostgresTestDatabase> {
  const sourceUrl = process.env[ADMIN_URL_ENV];

  if (
    typeof sourceUrl !== "string" ||
    sourceUrl.trim().length === 0
  ) {
    throw new Error(
      `${ADMIN_URL_ENV} is required for B4 PostgreSQL integration tests.`
    );
  }

  const parsedUrl = new URL(sourceUrl);

  if (
    !["postgres:", "postgresql:"].includes(parsedUrl.protocol) ||
    parsedUrl.username.length === 0 ||
    parsedUrl.password.length === 0
  ) {
    throw new Error(
      `${ADMIN_URL_ENV} must contain a PostgreSQL administrator connection URL.`
    );
  }

  const rootUrl = new URL(sourceUrl);
  rootUrl.pathname = "/postgres";

  let rootPool: Pool | undefined;
  let adminPool: Pool | undefined;
  let migrationPool: Pool | undefined;
  let applicationPool: Pool | undefined;
  let runtime: PostgresRuntime | undefined;

  let databaseName = "";
  let migrationRole = "";
  let applicationRole = "";

  let databaseCreated = false;
  let migrationRoleCreated = false;
  let applicationRoleCreated = false;

  let closePromise: Promise<void> | undefined;

  const closeResources = async (): Promise<void> => {
    const errors: Error[] = [];

    const capture = async (
      operation: () => Promise<unknown>
    ): Promise<void> => {
      try {
        await operation();
      } catch (error) {
        errors.push(toError(error));
      }
    };

    const cleanupRuntime = runtime;

    if (cleanupRuntime !== undefined) {
      await capture(() => cleanupRuntime.close());
    } else {
      const cleanupApplicationPool = applicationPool;

      if (cleanupApplicationPool !== undefined) {
        await capture(() => cleanupApplicationPool.end());
      }
    }

    const cleanupMigrationPool = migrationPool;

    if (cleanupMigrationPool !== undefined) {
      await capture(() => cleanupMigrationPool.end());
    }

    const cleanupAdminPool = adminPool;

    if (cleanupAdminPool !== undefined) {
      await capture(() => cleanupAdminPool.end());
    }

    const cleanupRootPool = rootPool;

    if (cleanupRootPool !== undefined && databaseCreated) {
      try {
        await waitForDatabaseConnectionsToClose(
          cleanupRootPool,
          databaseName
        );

        await cleanupRootPool.query(
          `DROP DATABASE IF EXISTS ${quoteIdentifier(databaseName)}`
        );

        databaseCreated = false;
      } catch (error) {
        errors.push(toError(error));
      }
    }

    /*
     * Never drop roles while their temporary database still exists.
     * A failed connection drain must remain visible and leave the
     * disposable resources available for investigation.
     */
    if (
      cleanupRootPool !== undefined &&
      !databaseCreated
    ) {
      if (applicationRoleCreated) {
        await capture(async () => {
          await cleanupRootPool.query(
            `DROP ROLE IF EXISTS ${quoteIdentifier(applicationRole)}`
          );

          applicationRoleCreated = false;
        });
      }

      if (migrationRoleCreated) {
        await capture(async () => {
          await cleanupRootPool.query(
            `DROP ROLE IF EXISTS ${quoteIdentifier(migrationRole)}`
          );

          migrationRoleCreated = false;
        });
      }
    }

    if (cleanupRootPool !== undefined) {
      await capture(() => cleanupRootPool.end());
    }

    if (errors.length > 0) {
      throw new AggregateError(
        errors,
        "B4 PostgreSQL test database cleanup did not complete cleanly."
      );
    }
  };

  const close = (): Promise<void> => {
    if (closePromise === undefined) {
      closePromise = closeResources();
    }

    return closePromise;
  };

  try {
    rootPool = new Pool({
      connectionString: rootUrl.toString(),
      max: 3,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000
    });

    const versionResult = await rootPool.query<ServerVersionRow>(
      `
        SELECT
          current_setting('server_version_num')::integer
            AS server_version_num
      `
    );

    const serverVersion =
      versionResult.rows[0]?.server_version_num;

    if (
      typeof serverVersion !== "number" ||
      !Number.isSafeInteger(serverVersion) ||
      serverVersion < MINIMUM_POSTGRES_VERSION
    ) {
      throw new Error(
        "B4 integration requires PostgreSQL 18.4 or newer."
      );
    }

    const suffix = randomBytes(8).toString("hex");

    databaseName = `homio_b4_${suffix}`;
    migrationRole = `homio_b4_m_${suffix}`;
    applicationRole = `homio_b4_a_${suffix}`;

    const migrationPassword = randomBytes(32).toString("hex");
    const applicationPassword = randomBytes(32).toString("hex");

    await rootPool.query(`
      CREATE ROLE ${quoteIdentifier(migrationRole)}
        LOGIN
        INHERIT
        NOSUPERUSER
        NOCREATEDB
        NOCREATEROLE
        NOREPLICATION
        NOBYPASSRLS
        PASSWORD ${quoteLiteral(migrationPassword)}
    `);

    migrationRoleCreated = true;

    await rootPool.query(`
      CREATE ROLE ${quoteIdentifier(applicationRole)}
        LOGIN
        INHERIT
        NOSUPERUSER
        NOCREATEDB
        NOCREATEROLE
        NOREPLICATION
        NOBYPASSRLS
        PASSWORD ${quoteLiteral(applicationPassword)}
    `);

    applicationRoleCreated = true;

    await rootPool.query(`
      CREATE DATABASE ${quoteIdentifier(databaseName)}
        OWNER ${quoteIdentifier(migrationRole)}
        TEMPLATE template0
    `);

    databaseCreated = true;

    await rootPool.query(`
      REVOKE CONNECT ON DATABASE ${quoteIdentifier(databaseName)}
        FROM PUBLIC
    `);

    await rootPool.query(`
      GRANT CONNECT ON DATABASE ${quoteIdentifier(databaseName)}
        TO ${quoteIdentifier(migrationRole)},
           ${quoteIdentifier(applicationRole)}
    `);

    const targetAdminUrl = connectionUrl(
      rootUrl.toString(),
      decodeURIComponent(rootUrl.username),
      decodeURIComponent(rootUrl.password),
      databaseName
    );

    const migrationUrl = connectionUrl(
      rootUrl.toString(),
      migrationRole,
      migrationPassword,
      databaseName
    );

    const applicationUrl = connectionUrl(
      rootUrl.toString(),
      applicationRole,
      applicationPassword,
      databaseName
    );

    adminPool = new Pool({
      connectionString: targetAdminUrl,
      max: 2,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000
    });

    migrationPool = new Pool({
      connectionString: migrationUrl,
      max: 1,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000
    });

    applicationPool = new Pool({
      connectionString: applicationUrl,
      max: 3,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000
    });

    /*
     * The migration login owns the infrastructure schema and ledger.
     * The API login cannot create objects in this schema or read the ledger.
     */
    await migrationPool.query(`
      CREATE SCHEMA reos_infra
        AUTHORIZATION ${quoteIdentifier(migrationRole)}
    `);

    await migrationPool.query(`
      CREATE TABLE reos_infra.schema_migrations (
        migration_id text NOT NULL,
        migration_name text NOT NULL,
        checksum text NOT NULL,
        applied_at timestamp with time zone NOT NULL
          DEFAULT clock_timestamp(),

        CONSTRAINT schema_migrations_pkey
          PRIMARY KEY (migration_id),

        CONSTRAINT schema_migrations_migration_name_key
          UNIQUE (migration_name),

        CONSTRAINT schema_migrations_migration_id_check
          CHECK (migration_id ~ '^[0-9]{8}$'),

        CONSTRAINT schema_migrations_migration_name_check
          CHECK (
            migration_name ~ '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'
          ),

        CONSTRAINT schema_migrations_checksum_check
          CHECK (checksum ~ '^[a-f0-9]{64}$')
      )
    `);

    await migrationPool.query(`
      ALTER DEFAULT PRIVILEGES
        FOR ROLE ${quoteIdentifier(migrationRole)}
        IN SCHEMA reos_infra
        REVOKE ALL ON TABLES
        FROM PUBLIC, ${quoteIdentifier(applicationRole)}
    `);

    await migrationPool.query(
      "REVOKE ALL ON SCHEMA reos_infra FROM PUBLIC"
    );

    await migrationPool.query(`
      REVOKE ALL ON SCHEMA reos_infra
        FROM ${quoteIdentifier(applicationRole)}
    `);

    await migrationPool.query(`
      REVOKE ALL ON TABLE reos_infra.schema_migrations
        FROM PUBLIC, ${quoteIdentifier(applicationRole)}
    `);

    const migrationsDirectory = fileURLToPath(
      new URL(
        "../../scripts/postgres/migrations/",
        import.meta.url
      )
    );

    const completeManifest = await loadPostgresMigrationManifest(
      migrationsDirectory,
      {
        migrationRole,
        applicationRole,
        schemaName: "core002"
      }
    );

    const b4Migrations = completeManifest.filter(
      (migration) =>
        migration.id === "00000003" ||
        migration.id === "00000004"
    );

    const expectedMigrationIds = [
      "00000003",
      "00000004"
    ];

    if (
      JSON.stringify(b4Migrations.map(({ id }) => id)) !==
      JSON.stringify(expectedMigrationIds)
    ) {
      throw new Error(
        "The canonical B4 session and audit migrations are incomplete or out of order."
      );
    }

    const migrationRunner = new PostgresMigrationRunner(
      migrationPool as unknown as PostgresDriverPool,
      {
        migrationRole,
        applicationRole
      }
    );

    const firstReport = await migrationRunner.migrate(b4Migrations);
    const repeatReport = await migrationRunner.migrate(b4Migrations);

    if (
      firstReport.appliedCount !== 2 ||
      firstReport.latestMigrationId !== "00000004" ||
      repeatReport.appliedCount !== 0 ||
      repeatReport.latestMigrationId !== "00000004"
    ) {
      throw new Error(
        "The B4 migration run was not deterministic and idempotent."
      );
    }

    const ledger = await adminPool.query<MigrationLedgerRow>(
      `
        SELECT
          migration_id,
          migration_name,
          checksum
        FROM reos_infra.schema_migrations
        ORDER BY migration_id ASC
      `
    );

    if (
      ledger.rows.length !== 2 ||
      JSON.stringify(
        ledger.rows.map((row) => row.migration_id)
      ) !== JSON.stringify(expectedMigrationIds) ||
      JSON.stringify(
        ledger.rows.map((row) => row.checksum)
      ) !== JSON.stringify(
        b4Migrations.map((migration) => migration.checksum)
      )
    ) {
      throw new Error(
        "The persisted B4 migration ledger does not match the canonical manifest."
      );
    }

    runtime = new PostgresRuntime(
      applicationPool as unknown as PostgresDriverPool
    );

    /*
     * The actual API database login is checked after the B4 session table
     * exists. This proves its effective role, table ownership, forced RLS
     * and restrictive tenant policy against a real PostgreSQL connection.
     */
    await runtime.verifyRuntimeRoleSafety();

    return Object.freeze({
      databaseName,
      applicationRole,
      adminPool,
      applicationPool,
      runtime,
      close
    });
  } catch (error) {
    try {
      await close();
    } catch (cleanupError) {
      throw new AggregateError(
        [
          toError(error),
          toError(cleanupError)
        ],
        "B4 PostgreSQL test database setup failed and cleanup also failed."
      );
    }

    throw error;
  }
}
