
import { spawn, execFileSync } from "node:child_process";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import {
  describe,
  expect,
  it
} from "vitest";

import {
  PostgresRuntime,
  type PostgresDriverPool
} from "../../src/persistence/postgres.js";
import {
  PostgresMigrationRunner
} from "../../src/persistence/postgres-migrations.js";
import {
  loadPostgresMigrationManifest
} from "../../src/persistence/postgres-migration-manifest.js";
import {
  PostgresSecurityAuditStore
} from "../../src/persistence/postgres-security-audit.js";
import {
  PostgresSessionStore
} from "../../src/persistence/postgres-session-store.js";
import type {
  SecurityAuditEvent,
  TrustedRequestContext,
  VerifiedExternalPrincipal
} from "../../src/security/contracts.js";

interface TestQueryResult {
  readonly rows: readonly Record<string, unknown>[];
  readonly rowCount: number | null;
}

interface TestPgClient {
  readonly connectionParameters?: {
    readonly database?: string;
  };
  query(
    text: string,
    values?: unknown[]
  ): Promise<TestQueryResult>;
  release(error?: Error | boolean): void;
}

interface TestPgPool {
  on(
    event: "error",
    listener: (error: Error, client: TestPgClient) => void
  ): this;
  connect(): Promise<TestPgClient>;
  query(
    text: string,
    values?: unknown[]
  ): Promise<TestQueryResult>;
  end(): Promise<void>;
}

interface ObservedPoolError {
  readonly databaseName: string;
  readonly error: Error;
}

interface PgModule {
  Pool: new (options: {
    connectionString: string;
    max: number;
    connectionTimeoutMillis?: number;
    idleTimeoutMillis?: number;
  }) => TestPgPool;
}

interface DockerResult {
  readonly stdout: string;
  readonly stderr: string;
}

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;

const require = createRequire(import.meta.url);
const pgModule = require("pg") as PgModule;

const postgresContainerId = findPostgresContainerId();

const integrationEnabled =
  typeof adminUrl === "string" &&
  (
    postgresContainerId !== undefined ||
    process.env.CI === "true"
  );

const b4RecoverySuite = integrationEnabled
  ? describe
  : describe.skip;

const TEST_TIMEOUT_MS = 90_000;
const DATABASE_DRAIN_TIMEOUT_MS = 10_000;
const DATABASE_DRAIN_POLL_INTERVAL_MS = 25;
const unexpectedPoolErrors: ObservedPoolError[] = [];

function findPostgresContainerId(): string | undefined {
  try {
    const output = execFileSync(
      "docker",
      [
        "ps",
        "--filter",
        "publish=5432",
        "--format",
        "{{.ID}}"
      ],
      {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
        timeout: 5_000
      }
    ).trim();

    const containerIds = output
      .split(/\r?\n/)
      .map((value) => value.trim())
      .filter(Boolean);

    return containerIds.length === 1
      ? containerIds[0]
      : undefined;
  } catch {
    return undefined;
  }
}

function quoteIdentifier(value: string): string {
  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(value)) {
    throw new TypeError("A safe PostgreSQL identifier is required.");
  }

  return `"${value}"`;
}

function redact(
  value: string,
  secrets: readonly string[]
): string {
  let result = value;

  for (const secret of secrets) {
    if (secret.length > 0) {
      result = result.replaceAll(secret, "[REDACTED]");
    }
  }

  return result;
}

function runDocker(
  args: readonly string[],
  environment: NodeJS.ProcessEnv,
  input?: string,
  secrets: readonly string[] = [],
  timeoutMs = 60_000
): Promise<DockerResult> {
  return new Promise((resolve, reject) => {
    const child = spawn("docker", [...args], {
      env: environment,
      stdio: ["pipe", "pipe", "pipe"]
    });

    const stdoutChunks: Buffer[] = [];
    const stderrChunks: Buffer[] = [];

    let settled = false;

    const finish = (
      error?: Error,
      result?: DockerResult
    ): void => {
      if (settled) {
        return;
      }

      settled = true;
      clearTimeout(timeout);

      if (error !== undefined) {
        reject(error);
        return;
      }

      if (result === undefined) {
        reject(new Error("Docker returned no result."));
        return;
      }

      resolve(result);
    };

    const timeout = setTimeout(() => {
      child.kill("SIGKILL");
      finish(
        new Error("The PostgreSQL Docker operation timed out.")
      );
    }, timeoutMs);

    child.stdout.on("data", (chunk: Buffer | string) => {
      stdoutChunks.push(Buffer.from(chunk));
    });

    child.stderr.on("data", (chunk: Buffer | string) => {
      stderrChunks.push(Buffer.from(chunk));
    });

    child.stdin.on("error", () => undefined);

    child.once("error", (error) => {
      finish(error);
    });

    child.once("close", (code, signal) => {
      const stdout = Buffer.concat(stdoutChunks).toString("utf8");
      const stderr = Buffer.concat(stderrChunks).toString("utf8");

      if (code !== 0) {
        const detail = redact(
          `${stderr}\n${stdout}`.trim(),
          secrets
        );

        finish(
          new Error(
            `Docker PostgreSQL command failed ` +
            `(exit=${String(code)}, signal=${String(signal)}): ` +
            detail.slice(0, 4_000)
          )
        );

        return;
      }

      finish(undefined, { stdout, stderr });
    });

    if (input === undefined) {
      child.stdin.end();
    } else {
      child.stdin.end(input);
    }
  });
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

function registerPoolErrorListener(
  pool: TestPgPool,
  fallbackDatabaseName: string,
  observedErrors: ObservedPoolError[]
): void {
  pool.on("error", (error, client) => {
    observedErrors.push({
      databaseName:
        client.connectionParameters?.database ?? fallbackDatabaseName,
      error
    });
  });
}

function assertNoUnexpectedPoolErrors(
  observedErrors: ObservedPoolError[]
): void {
  if (observedErrors.length === 0) {
    return;
  }

  const failures = observedErrors.splice(0);
  const details = failures
    .map(
      ({ databaseName, error }) =>
        `database=${databaseName}; ${error.name}: ${error.message}`
    )
    .join("\n");

  throw new Error(
    `Unexpected idle PostgreSQL pool error(s) were observed:\n${details}`
  );
}

async function waitForDatabaseConnectionsToDrain(
  adminPool: TestPgPool,
  databaseName: string,
  timeoutMs = DATABASE_DRAIN_TIMEOUT_MS
): Promise<void> {
  const deadline = Date.now() + timeoutMs;

  while (true) {
    const result = await adminPool.query(
      `
        SELECT count(*)::integer AS connection_count
        FROM pg_catalog.pg_stat_activity
        WHERE datname = $1
          AND pid <> pg_backend_pid()
      `,
      [databaseName]
    );

    const connectionCount = Number(
      result.rows[0]?.connection_count
    );

    if (
      !Number.isSafeInteger(connectionCount) ||
      connectionCount < 0
    ) {
      throw new Error(
        `PostgreSQL returned an invalid connection count for ${databaseName}.`
      );
    }

    if (connectionCount === 0) {
      return;
    }

    if (Date.now() >= deadline) {
      throw new Error(
        `PostgreSQL database ${databaseName} still has ${connectionCount} active connection(s) after ${timeoutMs}ms; refusing forced database termination.`
      );
    }

    await new Promise<void>((resolve) => {
      setTimeout(resolve, DATABASE_DRAIN_POLL_INTERVAL_MS);
    });
  }
}

function createPool(
  connectionString: string,
  max = 3
): TestPgPool {
  const databaseName = decodeURIComponent(
    new URL(connectionString).pathname.replace(/^\/+/, "")
  );

  if (databaseName.length === 0) {
    throw new TypeError(
      "A database name is required for a PostgreSQL test pool."
    );
  }

  const pool = new pgModule.Pool({
    connectionString,
    max,
    connectionTimeoutMillis: 5_000,
    idleTimeoutMillis: 5_000
  });

  registerPoolErrorListener(
    pool,
    databaseName,
    unexpectedPoolErrors
  );

  return pool;
}

async function runPsqlInContainer(input: {
  readonly containerId: string;
  readonly databaseName: string;
  readonly adminPassword: string;
  readonly sql: string;
  readonly additionalEnvironment?: Readonly<Record<string, string>>;
  readonly secrets?: readonly string[];
}): Promise<string> {
  const additionalEnvironment =
    input.additionalEnvironment ?? {};

  const environment: NodeJS.ProcessEnv = {
    ...process.env,
    PGPASSWORD: input.adminPassword,
    ...additionalEnvironment
  };

  const exposedEnvironmentNames = Object.keys(
    additionalEnvironment
  );

  const args = [
    "exec",
    "--env",
    "PGPASSWORD",
    ...exposedEnvironmentNames.flatMap((name) => [
      "--env",
      name
    ]),
    "-i",
    input.containerId,
    "psql",
    "--no-psqlrc",
    "--set",
    "ON_ERROR_STOP=1",
    "--host=127.0.0.1",
    "--username=postgres",
    `--dbname=${input.databaseName}`,
    "--no-align",
    "--tuples-only",
    "--quiet",
    "--file=-"
  ];

  const result = await runDocker(
    args,
    environment,
    input.sql,
    [
      input.adminPassword,
      ...Object.values(additionalEnvironment),
      ...(input.secrets ?? [])
    ]
  );

  return result.stdout;
}

async function createDatabaseBackup(input: {
  readonly containerId: string;
  readonly databaseName: string;
  readonly adminPassword: string;
}): Promise<string> {
  const result = await runDocker(
    [
      "exec",
      "--env",
      "PGPASSWORD",
      input.containerId,
      "pg_dump",
      "--no-password",
      "--host=127.0.0.1",
      "--username=postgres",
      `--dbname=${input.databaseName}`,
      "--format=plain"
    ],
    {
      ...process.env,
      PGPASSWORD: input.adminPassword
    },
    undefined,
    [input.adminPassword]
  );

  if (result.stdout.trim().length === 0) {
    throw new Error("PostgreSQL produced an empty full-database B4 backup.");
  }

  return result.stdout;
}

async function createSchemaOnlyBackup(input: {
  readonly containerId: string;
  readonly databaseName: string;
  readonly adminPassword: string;
}): Promise<string> {
  const result = await runDocker(
    [
      "exec",
      "--env",
      "PGPASSWORD",
      input.containerId,
      "pg_dump",
      "--no-password",
      "--host=127.0.0.1",
      "--username=postgres",
      `--dbname=${input.databaseName}`,
      "--schema-only",
      "--format=plain"
    ],
    {
      ...process.env,
      PGPASSWORD: input.adminPassword
    },
    undefined,
    [input.adminPassword]
  );

  if (result.stdout.trim().length === 0) {
    throw new Error("PostgreSQL produced an empty B4 schema-only backup.");
  }

  return result.stdout;
}

function sha256(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

describe("B4 recovery test PostgreSQL cleanup controls", () => {
  it("registers idle pool errors for an explicit failing assertion", () => {
    let errorListener:
      | ((error: Error, client: TestPgClient) => void)
      | undefined;
    const observedErrors: ObservedPoolError[] = [];
    const fakePool = {
      on(
        event: "error",
        listener: (error: Error, client: TestPgClient) => void
      ) {
        expect(event).toBe("error");
        errorListener = listener;
        return this;
      }
    } as unknown as TestPgPool;

    registerPoolErrorListener(
      fakePool,
      "homio_b4_restore_test",
      observedErrors
    );

    expect(errorListener).toBeDefined();

    const idleClientError = Object.assign(
      new Error("terminating connection due to administrator command"),
      { code: "57P01" }
    );

    errorListener?.(idleClientError, {
      connectionParameters: {
        database: "homio_b4_restore_test"
      }
    });

    expect(observedErrors).toHaveLength(1);
    expect(observedErrors[0]?.databaseName).toBe(
      "homio_b4_restore_test"
    );
    expect(observedErrors[0]?.error).toBe(idleClientError);
    expect(() =>
      assertNoUnexpectedPoolErrors(observedErrors)
    ).toThrow("Unexpected idle PostgreSQL pool error(s)");
    expect(observedErrors).toHaveLength(0);
  });

  it("waits for the isolated database backend sessions to close", async () => {
    let queryCount = 0;
    const fakePool = {
      async query() {
        queryCount += 1;

        return {
          rows: [
            {
              connection_count: queryCount === 1 ? 1 : 0
            }
          ],
          rowCount: 1
        };
      }
    } as unknown as TestPgPool;

    await waitForDatabaseConnectionsToDrain(
      fakePool,
      "homio_b4_restore_test"
    );

    expect(queryCount).toBe(2);
  });

  it("refuses database teardown while a backend session remains", async () => {
    const fakePool = {
      async query() {
        return {
          rows: [{ connection_count: 1 }],
          rowCount: 1
        };
      }
    } as unknown as TestPgPool;

    await expect(
      waitForDatabaseConnectionsToDrain(
        fakePool,
        "homio_b4_restore_test",
        0
      )
    ).rejects.toThrow(
      "refusing forced database termination"
    );
  });
});

b4RecoverySuite(
  "B4 actual PostgreSQL infrastructure backup and recovery",
  () => {
    it(
      "restores actual B4 migrations, active and revoked sessions, audit records and security boundaries",
      async () => {
        if (
          adminUrl === undefined ||
          postgresContainerId === undefined
        ) {
          throw new Error(
            "The PostgreSQL 18.4 CI service container is required."
          );
        }

        const baseUrl = new URL(adminUrl);

        if (
          !["postgres:", "postgresql:"].includes(baseUrl.protocol) ||
          baseUrl.password.length === 0
        ) {
          throw new Error(
            "The PostgreSQL integration administrator URL is invalid."
          );
        }

        const adminPassword = decodeURIComponent(
          baseUrl.password
        );

        const suffix = randomBytes(8).toString("hex");
        const databaseName = `homio_b4_recovery_${suffix}`;
        const restoreDatabaseName = `homio_b4_restore_${suffix}`;
        const migrationRole = `homio_b4_m_${suffix}`;
        const applicationRole = `homio_b4_a_${suffix}`;

        const migrationPassword = randomBytes(32).toString("hex");
        const applicationPassword = randomBytes(32).toString("hex");

        const quotedDatabase = quoteIdentifier(databaseName);
        const quotedRestoreDatabase = quoteIdentifier(restoreDatabaseName);
        const quotedMigrationRole = quoteIdentifier(migrationRole);
        const quotedApplicationRole = quoteIdentifier(applicationRole);

        const targetAdminUrl = connectionUrl(
          adminUrl,
          decodeURIComponent(baseUrl.username),
          adminPassword,
          databaseName
        );

        const migrationUrl = connectionUrl(
          adminUrl,
          migrationRole,
          migrationPassword,
          databaseName
        );

        const applicationUrl = connectionUrl(
          adminUrl,
          applicationRole,
          applicationPassword,
          databaseName
        );

        const restoreTargetAdminUrl = connectionUrl(
          adminUrl,
          decodeURIComponent(baseUrl.username),
          adminPassword,
          restoreDatabaseName
        );

        const restoreMigrationUrl = connectionUrl(
          adminUrl,
          migrationRole,
          migrationPassword,
          restoreDatabaseName
        );

        const restoreApplicationUrl = connectionUrl(
          adminUrl,
          applicationRole,
          applicationPassword,
          restoreDatabaseName
        );

        let adminPool: TestPgPool | undefined;
        let targetAdminPool: TestPgPool | undefined;
        let migrationPool: TestPgPool | undefined;
        let applicationPool: TestPgPool | undefined;
        let runtime: PostgresRuntime | undefined;
        let databaseCreated = false;
        let restoreDatabaseCreated = false;
        const cleanupErrors: unknown[] = [];

        try {
          adminPool = createPool(adminUrl, 2);

          await adminPool.query(
            `CREATE DATABASE ${quotedDatabase}`
          );

          databaseCreated = true;

          const bootstrapPath = fileURLToPath(
            new URL(
              "../../scripts/postgres/bootstrap-migration-ledger.sql",
              import.meta.url
            )
          );

          const bootstrapSql = await readFile(
            bootstrapPath,
            "utf8"
          );

          await runPsqlInContainer({
            containerId: postgresContainerId,
            databaseName,
            adminPassword,
            sql: bootstrapSql,
            additionalEnvironment: {
              HOMIO_MIGRATION_ROLE: migrationRole,
              HOMIO_APPLICATION_ROLE: applicationRole,
              HOMIO_MIGRATION_PASSWORD: migrationPassword,
              HOMIO_APPLICATION_PASSWORD: applicationPassword
            },
            secrets: [
              migrationPassword,
              applicationPassword
            ]
          });

          const coreBootstrapPath = fileURLToPath(
            new URL(
              "../../scripts/postgres/bootstrap-core002-schema.sql",
              import.meta.url
            )
          );

          const coreBootstrapSql = await readFile(
            coreBootstrapPath,
            "utf8"
          );

          await runPsqlInContainer({
            containerId: postgresContainerId,
            databaseName,
            adminPassword,
            sql: coreBootstrapSql,
            additionalEnvironment: {
              HOMIO_MIGRATION_ROLE: migrationRole,
              HOMIO_APPLICATION_ROLE: applicationRole
            },
            secrets: [
              migrationPassword,
              applicationPassword
            ]
          });

          await adminPool.query(
            `REVOKE CONNECT ON DATABASE ${quotedDatabase} FROM PUBLIC`
          );

          await adminPool.query(
            `GRANT CONNECT ON DATABASE ${quotedDatabase} TO ${quotedMigrationRole}, ${quotedApplicationRole}`
          );

          targetAdminPool = createPool(targetAdminUrl, 3);
          migrationPool = createPool(migrationUrl, 1);

          const migrationsDirectory = fileURLToPath(
            new URL(
              "../../scripts/postgres/migrations/",
              import.meta.url
            )
          );

          const completeManifest =
            await loadPostgresMigrationManifest(
              migrationsDirectory,
              {
                migrationRole,
                applicationRole,
                schemaName: "core002"
              }
            );

          /*
           * Recovery must exercise the entire canonical database, not only
           * the reos_infra slice. The same complete, ordered manifest is
           * used before backup and replayed unchanged after restore.
           */
          const b4Migrations = completeManifest;
          const expectedMigrationIds = Array.from(
            { length: 11 },
            (_, index) => String(index + 1).padStart(8, "0")
          );

          expect(
            b4Migrations.map((migration) => migration.id)
          ).toEqual(expectedMigrationIds);

          const migrationRunner = new PostgresMigrationRunner(
            migrationPool as unknown as PostgresDriverPool,
            {
              migrationRole,
              applicationRole
            }
          );

          const migrationReport = await migrationRunner.migrate(
            b4Migrations
          );

          expect(migrationReport.appliedCount).toBe(b4Migrations.length);
          expect(migrationReport.latestMigrationId).toBe("00000011");

          applicationPool = createPool(applicationUrl, 1);

          runtime = new PostgresRuntime(
            applicationPool as unknown as PostgresDriverPool
          );

          await runtime.verifyRuntimeRoleSafety();

          const tenantA = randomUUID();
          const tenantB = randomUUID();
          const leadA = randomUUID();
          const leadB = randomUUID();
          const customerA = randomUUID();
          const customerB = randomUUID();
          const persistedAt = new Date().toISOString();

          for (const [tenantId, slug] of [
            [tenantA, `b4-recovery-a-${tenantA.slice(0, 8)}`],
            [tenantB, `b4-recovery-b-${tenantB.slice(0, 8)}`]
          ]) {
            await targetAdminPool.query(
              `
                INSERT INTO core001.tenants (
                  tenant_id,
                  tenant_kind,
                  operating_mode,
                  display_name,
                  slug,
                  status,
                  isolation_profile,
                  residency_mode,
                  quota_profile,
                  revision,
                  created_at,
                  updated_at
                )
                VALUES (
                  $1,
                  'BROKERAGE',
                  'BROKER_SAAS',
                  $2,
                  $3,
                  'PROVISIONING',
                  'SHARED_LOGICAL',
                  'GLOBAL_ALLOWED',
                  'default',
                  1,
                  $4,
                  $4
                )
              `,
              [tenantId, slug, slug, persistedAt]
            );
          }

          const leadInsert = `
            INSERT INTO core003.leads (
              lead_id,
              tenant_id,
              customer_id,
              status,
              priority,
              source_type,
              metadata,
              revision,
              created_at,
              updated_at
            )
            VALUES (
              $1,
              $2,
              $3,
              'NEW',
              'NORMAL',
              'OTHER',
              '{}'::jsonb,
              1,
              $4,
              $4
            )
          `;

          await targetAdminPool.query(leadInsert, [
            leadA,
            tenantA,
            customerA,
            persistedAt
          ]);

          await targetAdminPool.query(leadInsert, [
            leadB,
            tenantB,
            customerB,
            persistedAt
          ]);

          const context: TrustedRequestContext = {
            identityId: randomUUID(),
            accountId: randomUUID(),
            authenticationEpoch: 1,
            tenantId: tenantA,
            tenantRevision: 1,
            organizationId: randomUUID(),
            membershipId: randomUUID(),
            membershipRevision: 1
          };

          const now = Math.floor(Date.now() / 1_000);

          const principal: VerifiedExternalPrincipal = {
            issuer: "https://b4-recovery.example.test/",
            subject: `b4-recovery-${suffix}`,
            audiences: ["homio-api"],
            clientId: "homio-b4-recovery-ci",
            tokenId: randomUUID(),
            issuedAtEpochSeconds: now - 5,
            expiresAtEpochSeconds: now + 3_600
          };

          const individuallyRevokedPrincipal: VerifiedExternalPrincipal = {
            ...principal,
            subject: `b4-recovery-single-revocation-${suffix}`,
            tokenId: randomUUID()
          };

          const accountWideContext: TrustedRequestContext = {
            ...context,
            accountId: randomUUID()
          };

          const accountWidePrincipal: VerifiedExternalPrincipal = {
            ...principal,
            subject: `b4-recovery-account-revocation-${suffix}`,
            tokenId: randomUUID()
          };

          const sessionStore = new PostgresSessionStore(runtime);

          const sessionId = await sessionStore.establishSession({
            principal,
            context
          });

          await sessionStore.establishSession({
            principal: individuallyRevokedPrincipal,
            context
          });

          await sessionStore.establishSession({
            principal: accountWidePrincipal,
            context: accountWideContext
          });

          await expect(
            sessionStore.isSessionActive({
              principal,
              context
            })
          ).resolves.toBe(true);

          await expect(
            sessionStore.revokeSession({
              principal: individuallyRevokedPrincipal,
              context,
              reasonCode: "B4_SINGLE_SESSION_REVOKED"
            })
          ).resolves.toBe(true);

          await expect(
            sessionStore.isSessionActive({
              principal: individuallyRevokedPrincipal,
              context
            })
          ).resolves.toBe(false);

          await expect(
            sessionStore.isSessionActive({
              principal,
              context
            })
          ).resolves.toBe(true);

          await expect(
            sessionStore.revokeAccountSessions({
              context: accountWideContext,
              reasonCode: "B4_ACCOUNT_REVOKED"
            })
          ).resolves.toBe(1);

          await expect(
            sessionStore.isSessionActive({
              principal: accountWidePrincipal,
              context: accountWideContext
            })
          ).resolves.toBe(false);

          const requestId = randomUUID();

          const auditEvent: SecurityAuditEvent = {
            eventType: "API_ACCESS_DENIED",
            requestId,
            occurredAt: new Date().toISOString(),
            reasonCode: "B4_BACKUP_RECOVERY",
            operation: "inventory.read",
            actorIdentityId: context.identityId,
            tenantId: context.tenantId
          };

          /*
           * The audit store must use the existing transaction runtime.
           * Passing applicationPool directly would bypass the trusted
           * tenant transaction context and database append function.
           */
          const auditStore = new PostgresSecurityAuditStore(runtime);

          await auditStore.record(auditEvent);
                    const beforeBackup = await targetAdminPool.query(
            `
              SELECT
                (SELECT count(*)::integer
                   FROM reos_infra.api_sessions) AS session_count,
                (SELECT count(*)::integer
                   FROM reos_infra.security_audit_events
                  WHERE request_id = $2) AS audit_count,
                (SELECT count(*)::integer
                   FROM reos_infra.schema_migrations) AS migration_count,
                (SELECT count(*)::integer
                   FROM core001.tenants
                  WHERE tenant_id = ANY($1::uuid[])) AS tenant_count,
                (SELECT count(*)::integer
                   FROM core003.leads
                  WHERE tenant_id = ANY($1::uuid[])) AS lead_count
            `,
            [[tenantA, tenantB], requestId]
          );

          expect(beforeBackup.rows[0]).toMatchObject({
            session_count: 3,
            audit_count: 1,
            migration_count: 11,
            tenant_count: 2,
            lead_count: 2
          });

          const backupSql = await createDatabaseBackup({
            containerId: postgresContainerId,
            databaseName,
            adminPassword
          });
          const schemaBackupSql = await createSchemaOnlyBackup({
            containerId: postgresContainerId,
            databaseName,
            adminPassword
          });

          const backupSha256 = sha256(backupSql);
          const schemaFingerprint = (dump: string): string =>
            sha256(
              dump
                .split(/\r?\n/)
                .filter(
                  (line) => !/^\\(?:restrict|unrestrict)\s+/.test(line)
                )
                .join("\n")
            );
          const schemaSha256 = schemaFingerprint(schemaBackupSql);

          for (const schemaName of [
            "core001",
            "core002",
            "core003",
            "core004",
            "core006",
            "core007",
            "core008",
            "reos_infra"
          ]) {
            expect(backupSql).toContain(`CREATE SCHEMA ${schemaName};`);
          }

          expect(backupSql).toContain("CREATE TABLE core001.tenants");
          expect(backupSql).toContain("CREATE TABLE core003.leads");
          expect(backupSql).toContain("CREATE TABLE core008.financial_ledger_entries");
          expect(backupSql).toContain("CREATE TABLE reos_infra.api_sessions");
          expect(backupSql).toContain("CREATE TABLE reos_infra.security_audit_events");
          expect(backupSql).toContain("CREATE TABLE reos_infra.schema_migrations");
          expect(backupSql).toContain("append_security_audit_event");
          expect(backupSql).toContain("CREATE POLICY");
          expect(backupSql).toContain("CREATE TRIGGER");

          await runtime.close();
          runtime = undefined;
          applicationPool = undefined;

          await migrationPool.end();
          migrationPool = undefined;

          await targetAdminPool.end();
          targetAdminPool = undefined;

          await adminPool.query(
            `CREATE DATABASE ${quotedRestoreDatabase} TEMPLATE template0`
          );
          restoreDatabaseCreated = true;

          await adminPool.query(
            `REVOKE CONNECT ON DATABASE ${quotedRestoreDatabase} FROM PUBLIC`
          );

          await adminPool.query(
            `GRANT CONNECT ON DATABASE ${quotedRestoreDatabase} TO ${quotedMigrationRole}, ${quotedApplicationRole}`
          );

          targetAdminPool = createPool(restoreTargetAdminUrl, 3);
          migrationPool = createPool(restoreMigrationUrl, 1);

          await runPsqlInContainer({
            containerId: postgresContainerId,
            databaseName: restoreDatabaseName,
            adminPassword,
            sql: backupSql
          });



          const restoredDatabasePrivileges = await targetAdminPool.query(
            `
              SELECT
                has_database_privilege(
                  $1,
                  current_database(),
                  'CONNECT'
                ) AS migration_connect,
                has_database_privilege(
                  $2,
                  current_database(),
                  'CONNECT'
                ) AS application_connect,
                EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_database AS database
                  CROSS JOIN LATERAL pg_catalog.aclexplode(
                    COALESCE(
                      database.datacl,
                      pg_catalog.acldefault('d', database.datdba)
                    )
                  ) AS privilege
                  WHERE database.datname = current_database()
                    AND privilege.grantee = 0
                    AND privilege.privilege_type = 'CONNECT'
                ) AS public_connect
            `,
            [migrationRole, applicationRole]
          );

          expect(restoredDatabasePrivileges.rows[0]).toEqual({
            migration_connect: true,
            application_connect: true,
            public_connect: false
          });

          const restoredMigrationRunner =
            new PostgresMigrationRunner(
              migrationPool as unknown as PostgresDriverPool,
              {
                migrationRole,
                applicationRole
              }
            );

          const restoredMigrationReport =
            await restoredMigrationRunner.migrate(b4Migrations);

          expect(restoredMigrationReport.appliedCount).toBe(0);
          expect(
            restoredMigrationReport.latestMigrationId
          ).toBe("00000011");

          const restoredLedger = await targetAdminPool.query(`
            SELECT migration_id, checksum
            FROM reos_infra.schema_migrations
            ORDER BY migration_id
          `);

          expect(
            restoredLedger.rows.map((row) => row.migration_id)
          ).toEqual(expectedMigrationIds);

          expect(
            restoredLedger.rows.map((row) => row.checksum)
          ).toEqual(
            b4Migrations.map((migration) => migration.checksum)
          );

          const restoredSchemaSql = await createSchemaOnlyBackup({
            containerId: postgresContainerId,
            databaseName: restoreDatabaseName,
            adminPassword
          });

          expect(schemaFingerprint(restoredSchemaSql)).toBe(schemaSha256);

          const restoredSchemas = await targetAdminPool.query(
            `
              SELECT nspname AS schema_name
              FROM pg_catalog.pg_namespace
              WHERE nspname = ANY($1::text[])
              ORDER BY nspname
            `,
            [[
              "core001",
              "core002",
              "core003",
              "core004",
              "core006",
              "core007",
              "core008",
              "reos_infra"
            ]]
          );

          expect(
            restoredSchemas.rows.map((row) => row.schema_name)
          ).toEqual([
            "core001",
            "core002",
            "core003",
            "core004",
            "core006",
            "core007",
            "core008",
            "reos_infra"
          ]);

          const restoredData = await targetAdminPool.query(
            `
              SELECT
                (SELECT count(*)::integer
                   FROM reos_infra.api_sessions) AS session_count,
                (SELECT count(*)::integer
                   FROM reos_infra.security_audit_events
                  WHERE request_id = $2) AS audit_count,
                (SELECT count(*)::integer
                   FROM reos_infra.schema_migrations) AS migration_count,
                (SELECT count(*)::integer
                   FROM core001.tenants
                  WHERE tenant_id = ANY($1::uuid[])) AS tenant_count,
                (SELECT count(*)::integer
                   FROM core003.leads
                  WHERE tenant_id = ANY($1::uuid[])) AS lead_count
            `,
            [[tenantA, tenantB], requestId]
          );

          expect(restoredData.rows[0]).toMatchObject({
            session_count: 3,
            audit_count: 1,
            migration_count: 11,
            tenant_count: 2,
            lead_count: 2
          });

          await migrationPool.end();
          migrationPool = undefined;

          applicationPool = createPool(restoreApplicationUrl, 1);

          runtime = new PostgresRuntime(
            applicationPool as unknown as PostgresDriverPool
          );

          await runtime.verifyRuntimeRoleSafety();

          const managedSchemas = [
            "core001",
            "core002",
            "core003",
            "core004",
            "core006",
            "core007",
            "core008",
            "reos_infra"
          ];

          const restoredTenantTables = await targetAdminPool.query(
            `
              SELECT
                namespace.nspname AS schema_name,
                relation.relname AS relation_name,
                relation.relrowsecurity AS rls_enabled,
                relation.relforcerowsecurity AS rls_forced,
                pg_catalog.pg_get_userbyid(relation.relowner)
                  AS relation_owner
              FROM pg_catalog.pg_class AS relation
              JOIN pg_catalog.pg_namespace AS namespace
                ON namespace.oid = relation.relnamespace
              WHERE relation.relkind IN ('r', 'p')
                AND namespace.nspname = ANY($1::text[])
                AND EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_attribute AS attribute
                  WHERE attribute.attrelid = relation.oid
                    AND attribute.attname = 'tenant_id'
                    AND attribute.attnum > 0
                    AND attribute.attisdropped = false
                )
              ORDER BY namespace.nspname, relation.relname
            `,
            [managedSchemas]
          );

          expect(restoredTenantTables.rows.length).toBeGreaterThan(0);

          for (const row of restoredTenantTables.rows) {
            expect(row.rls_enabled).toBe(true);
            expect(row.rls_forced).toBe(true);
            expect(row.relation_owner).toBe(migrationRole);
          }

          const restoredTenantVisibility =
            await runtime.withTenantTransaction(
              { tenantId: tenantA },
              (transaction) =>
                transaction.query(
                  `
                    SELECT tenant_id, lead_id
                    FROM core003.leads
                    WHERE tenant_id = ANY($1::uuid[])
                    ORDER BY lead_id
                  `,
                  [[tenantA, tenantB]]
                )
            );

          expect(restoredTenantVisibility.rows).toEqual([
            {
              tenant_id: tenantA,
              lead_id: leadA
            }
          ]);

          await expect(
            runtime.withTenantTransaction(
              { tenantId: tenantA },
              (transaction) =>
                transaction.query(
                  leadInsert,
                  [
                    randomUUID(),
                    tenantB,
                    randomUUID(),
                    persistedAt
                  ]
                )
            )
          ).rejects.toMatchObject({
            code: "42501"
          });

          const restoredSessionStore = new PostgresSessionStore(
            runtime
          );

          await expect(
            restoredSessionStore.isSessionActive({
              principal,
              context
            })
          ).resolves.toBe(true);

          await expect(
            restoredSessionStore.isSessionActive({
              principal: individuallyRevokedPrincipal,
              context
            })
          ).resolves.toBe(false);

          await expect(
            restoredSessionStore.isSessionActive({
              principal: accountWidePrincipal,
              context: accountWideContext
            })
          ).resolves.toBe(false);

          await expect(
            restoredSessionStore.isSessionActive({
              principal,
              context: {
                ...context,
                tenantId: randomUUID()
              }
            })
          ).resolves.toBe(false);

          await expect(
            restoredSessionStore.revokeAccountSessions({
              context,
              reasonCode: "B4_POST_RESTORE_ACCOUNT_REVOKED"
            })
          ).resolves.toBe(1);

          await expect(
            restoredSessionStore.isSessionActive({
              principal,
              context
            })
          ).resolves.toBe(false);

          const restoredAudit = await targetAdminPool.query(`
            SELECT
              event_type,
              request_id,
              reason_code,
              operation,
              actor_identity_reference,
              tenant_reference
            FROM reos_infra.security_audit_events
            WHERE request_id = '${requestId}'
          `);

          expect(restoredAudit.rows).toHaveLength(1);
          expect(restoredAudit.rows[0]).toMatchObject({
            event_type: "API_ACCESS_DENIED",
            request_id: requestId,
            reason_code: "B4_BACKUP_RECOVERY",
            operation: "inventory.read",
            actor_identity_reference: context.identityId,
            tenant_reference: context.tenantId
          });

          const owners = await targetAdminPool.query(
            `
              SELECT
                namespace.nspname AS schema_name,
                pg_catalog.pg_get_userbyid(namespace.nspowner)
                  AS schema_owner,
                relation.relname AS relation_name,
                pg_catalog.pg_get_userbyid(relation.relowner)
                  AS table_owner
              FROM pg_catalog.pg_namespace AS namespace
              JOIN pg_catalog.pg_class AS relation
                ON relation.relnamespace = namespace.oid
              WHERE namespace.nspname = ANY($1::text[])
                AND relation.relkind IN ('r', 'p')
              ORDER BY namespace.nspname, relation.relname
            `,
            [managedSchemas]
          );

          expect(owners.rows.length).toBeGreaterThan(0);

          for (const row of owners.rows) {
            expect(row.schema_owner).toBe(migrationRole);
            expect(row.table_owner).toBe(migrationRole);
          }

          const rls = await targetAdminPool.query(`
            SELECT
              relation.relrowsecurity AS enabled,
              relation.relforcerowsecurity AS forced
            FROM pg_class AS relation
            WHERE relation.oid = 'reos_infra.api_sessions'::regclass
          `);

          expect(rls.rows[0]).toEqual({
            enabled: true,
            forced: true
          });

          const policies = await targetAdminPool.query(`
            SELECT polname, polpermissive
            FROM pg_policy
            WHERE polrelid = 'reos_infra.api_sessions'::regclass
            ORDER BY polname
          `);

          expect(policies.rows).toEqual([
            {
              polname: "api_sessions_application_access",
              polpermissive: true
            },
            {
              polname: "api_sessions_tenant_guard",
              polpermissive: false
            }
          ]);

          const triggers = await targetAdminPool.query(`
            SELECT
              relation.relname AS table_name,
              trigger.tgname AS trigger_name
            FROM pg_trigger AS trigger
            JOIN pg_class AS relation
              ON relation.oid = trigger.tgrelid
            WHERE NOT trigger.tgisinternal
              AND relation.oid IN (
                'reos_infra.api_sessions'::regclass,
                'reos_infra.security_audit_events'::regclass
              )
            ORDER BY relation.relname, trigger.tgname
          `);

          expect(
            triggers.rows.map((row) => row.trigger_name)
          ).toEqual([
            "api_sessions_immutable_identity",
            "security_audit_events_append_only",
            "security_audit_events_tenant_context_guard",
            "security_audit_events_truncate_guard"
          ]);

          const privileges = await targetAdminPool.query(`
            SELECT
              has_schema_privilege(
                $1, 'reos_infra', 'USAGE'
              ) AS schema_usage,
              has_schema_privilege(
                $1, 'reos_infra', 'CREATE'
              ) AS schema_create,
              has_table_privilege(
                $1, 'reos_infra.api_sessions', 'SELECT'
              ) AS session_select,
              has_table_privilege(
                $1, 'reos_infra.api_sessions', 'INSERT'
              ) AS session_insert,
              has_table_privilege(
                $1, 'reos_infra.api_sessions', 'UPDATE'
              ) AS session_update,
              has_table_privilege(
                $1, 'reos_infra.api_sessions', 'DELETE'
              ) AS session_delete,
              has_table_privilege(
                $1, 'reos_infra.security_audit_events', 'INSERT'
              ) AS audit_insert,
              has_table_privilege(
                $1, 'reos_infra.security_audit_events', 'SELECT'
              ) AS audit_select,
              has_table_privilege(
                $1, 'reos_infra.security_audit_events', 'UPDATE'
              ) AS audit_update,
              has_table_privilege(
                $1, 'reos_infra.security_audit_events', 'DELETE'
              ) AS audit_delete,
              has_table_privilege(
                $1, 'reos_infra.security_audit_events', 'TRUNCATE'
              ) AS audit_truncate,
              has_function_privilege(
                $1,
                'reos_infra.append_security_audit_event(uuid,text,uuid,timestamptz,text,text,uuid,uuid)'::regprocedure,
                'EXECUTE'
              ) AS audit_append_execute
          `, [applicationRole]);

          expect(privileges.rows[0]).toEqual({
            schema_usage: true,
            schema_create: false,
            session_select: true,
            session_insert: true,
            session_update: true,
            session_delete: false,
            audit_insert: false,
            audit_select: false,
            audit_update: false,
            audit_delete: false,
            audit_truncate: false,
            audit_append_execute: true
          });

          await expect(
            applicationPool.query(
              "SELECT migration_id FROM reos_infra.schema_migrations"
            )
          ).rejects.toMatchObject({
            code: "42501"
          });

          await expect(
            applicationPool.query(
              "SELECT event_id FROM reos_infra.security_audit_events"
            )
          ).rejects.toMatchObject({
            code: "42501"
          });

          await expect(
            targetAdminPool.query(`
              UPDATE reos_infra.api_sessions
              SET account_id = '${randomUUID()}'
              WHERE session_id = '${sessionId}'
            `)
          ).rejects.toMatchObject({
            code: "55000"
          });

          await expect(
            targetAdminPool.query(`
              UPDATE reos_infra.security_audit_events
              SET reason_code = 'RESTORE_MUTATION'
              WHERE request_id = '${requestId}'
            `)
          ).rejects.toMatchObject({
            code: "55000"
          });

          console.log("B4_RECOVERY_METHOD=FULL_DATABASE_PG_DUMP_TO_SEPARATE_DATABASE");
          console.log(`B4_RECOVERY_SOURCE_DATABASE=${databaseName}`);
          console.log(`B4_RECOVERY_TARGET_DATABASE=${restoreDatabaseName}`);
          console.log(`B4_RECOVERY_BACKUP_SHA256=${backupSha256}`);
          console.log(`B4_RECOVERY_BACKUP_BYTES=${Buffer.byteLength(backupSql, "utf8")}`);
          console.log(`B4_RECOVERY_SCHEMA_SHA256=${schemaSha256}`);
          console.log("B4_RECOVERY_MIGRATION_COUNT=11");
          console.log("B4_RECOVERY_REPLAY_APPLIED_COUNT=0");
          console.log("B4_RECOVERY_SCHEMA_INTEGRITY=PASS");
          console.log("B4_RECOVERY_DATA_INTEGRITY=PASS");
          console.log("B4_RECOVERY_TENANT_ISOLATION=PASS");
          console.log("B4_RECOVERY_DATABASE_ACL=PASS");
          console.log("B4_RECOVERY_ROLE_AND_GRANT_INTEGRITY=PASS");
          console.log("B4_RECOVERY_TARGET_CLASS=EPHEMERAL_GITHUB_ACTIONS_POSTGRESQL_18_4");
          console.log("B4_RECOVERY_PRODUCTION_TARGET=NOT_TESTED");
          console.log("B4_RECOVERY_VERIFICATION=PASS");
        } finally {
          if (runtime !== undefined) {
            await runtime.close().catch((error: unknown) => {
              cleanupErrors.push(error);
            });
          } else if (applicationPool !== undefined) {
            await applicationPool.end().catch((error: unknown) => {
              cleanupErrors.push(error);
            });
          }

          await migrationPool?.end().catch((error: unknown) => {
            cleanupErrors.push(error);
          });
          await targetAdminPool?.end().catch((error: unknown) => {
            cleanupErrors.push(error);
          });

          if (adminPool !== undefined) {
            if (restoreDatabaseCreated) {
              try {
                await waitForDatabaseConnectionsToDrain(
                  adminPool,
                  restoreDatabaseName
                );
                await adminPool.query(
                  `DROP DATABASE IF EXISTS ${quotedRestoreDatabase}`
                );
                restoreDatabaseCreated = false;
              } catch (error) {
                cleanupErrors.push(error);
              }
            }

            if (databaseCreated) {
              try {
                await waitForDatabaseConnectionsToDrain(
                  adminPool,
                  databaseName
                );
                await adminPool.query(
                  `DROP DATABASE IF EXISTS ${quotedDatabase}`
                );
                databaseCreated = false;
              } catch (error) {
                cleanupErrors.push(error);
              }
            }

            await adminPool.query(
              `DROP ROLE IF EXISTS ${quotedApplicationRole}`
            ).catch((error: unknown) => {
              cleanupErrors.push(error);
            });

            await adminPool.query(
              `DROP ROLE IF EXISTS ${quotedMigrationRole}`
            ).catch((error: unknown) => {
              cleanupErrors.push(error);
            });

            await adminPool.end().catch((error: unknown) => {
              cleanupErrors.push(error);
            });
          }

          try {
            assertNoUnexpectedPoolErrors(unexpectedPoolErrors);
          } catch (error) {
            cleanupErrors.push(error);
          }

          if (cleanupErrors.length > 0) {
            const details = cleanupErrors
              .map((error) =>
                error instanceof Error ? error.message : String(error)
              )
              .join("\n");

            throw new Error(
              `B4 recovery cleanup failed:\n${details}`
            );
          }
        }
      },
      TEST_TIMEOUT_MS
    );
  }
);

  
