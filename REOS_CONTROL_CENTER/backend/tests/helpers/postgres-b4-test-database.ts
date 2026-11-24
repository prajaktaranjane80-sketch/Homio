import { randomBytes } from "node:crypto";
import { readFile } from "node:fs/promises";
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

const BOOTSTRAP_VARIABLE_ENVIRONMENT = {
  migration_role: "HOMIO_MIGRATION_ROLE",
  application_role: "HOMIO_APPLICATION_ROLE",
  migration_password: "HOMIO_MIGRATION_PASSWORD",
  application_password: "HOMIO_APPLICATION_PASSWORD"
} as const;

type BootstrapVariableName =
  keyof typeof BOOTSTRAP_VARIABLE_ENVIRONMENT;

type BootstrapVariableValues = Readonly<
  Record<BootstrapVariableName, string>
>;

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

export interface B4PostgresTestMigration {
  readonly id: string;
  readonly name: string;
  readonly checksum: string;
}

export interface B4PostgresTestDatabase {
  readonly databaseName: string;
  readonly applicationRole: string;
  readonly postgresServerVersion: number;
  readonly migrationHistory: readonly B4PostgresTestMigration[];
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

/**
 * The repository bootstrap files are canonical psql scripts.
 *
 * This adapter removes only their supported psql control directives and
 * safely substitutes their declared environment variables so the exact
 * checked-in SQL can be executed through the existing node-postgres client.
 *
 * Unknown psql commands and unresolved variables fail closed.
 */
function compileCanonicalBootstrapSql(
  source: string,
  values: BootstrapVariableValues,
  requiredVariables: readonly BootstrapVariableName[]
): string {
  if (typeof source !== "string" || source.trim().length === 0) {
    throw new Error("A non-empty canonical PostgreSQL bootstrap script is required.");
  }

  const observedVariables = new Set<BootstrapVariableName>();
  const executableLines: string[] = [];

  for (const line of source.replace(/\r\n/g, "\n").split("\n")) {
    const trimmed = line.trim();

    if (/^\\set\s+ON_ERROR_STOP\s+on$/i.test(trimmed)) {
      continue;
    }

    const getenvMatch =
      /^\\getenv\s+([a-z_][a-z0-9_]*)\s+([A-Z][A-Z0-9_]*)$/i.exec(
        trimmed
      );

    if (getenvMatch !== null) {
      const variable = getenvMatch[1] as BootstrapVariableName;
      const environmentName = getenvMatch[2];

      if (
        !Object.prototype.hasOwnProperty.call(
          BOOTSTRAP_VARIABLE_ENVIRONMENT,
          variable
        ) ||
        BOOTSTRAP_VARIABLE_ENVIRONMENT[variable] !== environmentName ||
        typeof values[variable] !== "string" ||
        values[variable].length === 0
      ) {
        throw new Error(
          "The canonical bootstrap script declares an unsupported or unresolved variable."
        );
      }

      observedVariables.add(variable);
      continue;
    }

    if (trimmed.startsWith("\\")) {
      throw new Error(
        "The canonical bootstrap script contains an unsupported psql command."
      );
    }

    executableLines.push(line);
  }

  for (const requiredVariable of requiredVariables) {
    if (!observedVariables.has(requiredVariable)) {
      throw new Error(
        `The canonical bootstrap script is missing ${requiredVariable}.`
      );
    }
  }

  let sql = executableLines.join("\n");

  for (const variable of observedVariables) {
    const value = values[variable];
    const isIdentifier = variable.endsWith("_role");
    const token = isIdentifier
      ? `:"${variable}"`
      : `:'${variable}'`;

    if (!sql.includes(token)) {
      throw new Error(
        `The canonical bootstrap script did not use its declared ${variable} variable.`
      );
    }

    sql = sql.replaceAll(
      token,
      isIdentifier
        ? quoteIdentifier(value)
        : quoteLiteral(value)
    );
  }

  if (
    /:"[a-z_][a-z0-9_]*"/i.test(sql) ||
    /:'[a-z_][a-z0-9_]*'/i.test(sql)
  ) {
    throw new Error(
      "The canonical bootstrap script contains an unresolved psql variable."
    );
  }

  if (sql.trim().length === 0) {
    throw new Error("The compiled PostgreSQL bootstrap SQL is empty.");
  }

  return sql;
}

async function executeCanonicalBootstrapScript(
  pool: Pool,
  scriptUrl: URL,
  values: BootstrapVariableValues,
  requiredVariables: readonly BootstrapVariableName[]
): Promise<void> {
  const source = await readFile(scriptUrl, "utf8");

  const sql = compileCanonicalBootstrapSql(
    source,
    values,
    requiredVariables
  );

  await pool.query(sql);
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
    sourceUrl.length === 0 ||
    sourceUrl !== sourceUrl.trim()
  ) {
    throw new Error(
      `${ADMIN_URL_ENV} is required and must not contain surrounding whitespace.`
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
     * Never drop temporary roles while the database still exists.
     * A failed connection drain must remain visible and leave the database
     * available for investigation.
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

    const bootstrapVariables: BootstrapVariableValues = Object.freeze({
      migration_role: migrationRole,
      application_role: applicationRole,
      migration_password: migrationPassword,
      application_password: applicationPassword
    });

    /*
     * The temporary database is initially created by the administrator.
     * The canonical bootstrap SQL then creates the dedicated roles and
     * migration-owned schemas inside this database.
     */
    await rootPool.query(
      `CREATE DATABASE ${quoteIdentifier(databaseName)} TEMPLATE template0`
    );

    databaseCreated = true;

    const targetAdminUrl = connectionUrl(
      rootUrl.toString(),
      decodeURIComponent(rootUrl.username),
      decodeURIComponent(rootUrl.password),
      databaseName
    );

    adminPool = new Pool({
      connectionString: targetAdminUrl,
      max: 2,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000
    });

    /*
     * Execute the exact checked-in bootstrap SQL.
     * No second inline migration-ledger DDL is maintained in this helper.
     */
    await executeCanonicalBootstrapScript(
      adminPool,
      new URL(
        "../../scripts/postgres/bootstrap-migration-ledger.sql",
        import.meta.url
      ),
      bootstrapVariables,
      [
        "migration_role",
        "application_role",
        "migration_password",
        "application_password"
      ]
    );

    migrationRoleCreated = true;
    applicationRoleCreated = true;

    await executeCanonicalBootstrapScript(
      adminPool,
      new URL(
        "../../scripts/postgres/bootstrap-core002-schema.sql",
        import.meta.url
      ),
      bootstrapVariables,
      [
        "migration_role",
        "application_role"
      ]
    );

    await rootPool.query(`
      REVOKE CONNECT ON DATABASE ${quoteIdentifier(databaseName)}
        FROM PUBLIC
    `);

    await rootPool.query(`
      GRANT CONNECT ON DATABASE ${quoteIdentifier(databaseName)}
        TO ${quoteIdentifier(migrationRole)},
           ${quoteIdentifier(applicationRole)}
    `);

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

    migrationPool = new Pool({
      connectionString: migrationUrl,
      max: 1,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000,
    });

    applicationPool = new Pool({
      connectionString: applicationUrl,
      max: 3,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 2_000,
    });

    const migrationsDirectory = fileURLToPath(
      new URL(
        "../../scripts/postgres/migrations/",
        import.meta.url
      )
    );

    /*
     * The helper consumes the entire canonical manifest.
     * It never filters the manifest down to selected B4 migration IDs.
     */
    const completeManifest = await loadPostgresMigrationManifest(
      migrationsDirectory,
      {
        migrationRole,
        applicationRole,
        schemaName: "core002"
      }
    );

    if (completeManifest.length === 0) {
      throw new Error(
        "The canonical PostgreSQL migration manifest is empty."
      );
    }

    for (let index = 0; index < completeManifest.length; index += 1) {
      const migration = completeManifest[index];

      if (migration === undefined) {
        throw new Error(
          "The canonical PostgreSQL migration manifest changed during validation."
        );
      }

      const expectedId = String(index + 1).padStart(8, "0");

      if (migration.id !== expectedId) {
        throw new Error(
          `The canonical migration manifest is not a complete ordered prefix; expected ${expectedId}, received ${migration.id}.`
        );
      }
    }

    const migrationRunner = new PostgresMigrationRunner(
      migrationPool as unknown as PostgresDriverPool,
      {
        migrationRole,
        applicationRole
      }
    );

    const firstReport = await migrationRunner.migrate(completeManifest);
    const replayReport = await migrationRunner.migrate(completeManifest);

    const latestMigration =
      completeManifest[completeManifest.length - 1];

    if (latestMigration === undefined) {
      throw new Error(
        "The canonical PostgreSQL migration manifest has no final migration."
      );
    }

    if (
      firstReport.appliedCount !== completeManifest.length ||
      firstReport.latestMigrationId !== latestMigration.id ||
      firstReport.latestChecksum !== latestMigration.checksum ||
      replayReport.appliedCount !== 0 ||
      replayReport.latestMigrationId !== latestMigration.id ||
      replayReport.latestChecksum !== latestMigration.checksum
    ) {
      throw new Error(
        "The full canonical migration manifest was not deterministic and idempotent."
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

    const expectedLedger = completeManifest.map((migration) => ({
      migration_id: migration.id,
      migration_name: migration.name,
      checksum: migration.checksum
    }));

    if (
      JSON.stringify(ledger.rows) !==
      JSON.stringify(expectedLedger)
    ) {
      throw new Error(
        "The persisted migration ledger does not exactly match the full canonical manifest."
      );
    }

    const migrationHistory = Object.freeze(
      completeManifest.map((migration) =>
        Object.freeze({
          id: migration.id,
          name: migration.name,
          checksum: migration.checksum
        })
      )
    );

    runtime = new PostgresRuntime(
      applicationPool as unknown as PostgresDriverPool
    );

    /*
     * Verify the real API login on an actual pooled application connection.
     * This uses the same PostgresRuntime security owner as production.
     */
    await runtime.verifyRuntimeRoleSafety();

    return Object.freeze({
      databaseName,
      applicationRole,
      postgresServerVersion: serverVersion,
      migrationHistory,
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
