
import { spawn, execFileSync } from "node:child_process";
import { randomBytes, randomUUID } from "node:crypto";
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
  query(
    text: string,
    values?: unknown[]
  ): Promise<TestQueryResult>;
  release(error?: Error | boolean): void;
}

interface TestPgPool {
  connect(): Promise<TestPgClient>;
  query(
    text: string,
    values?: unknown[]
  ): Promise<TestQueryResult>;
  end(): Promise<void>;
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

function createPool(
  connectionString: string,
  max = 3
): TestPgPool {
  return new pgModule.Pool({
    connectionString,
    max,
    connectionTimeoutMillis: 5_000,
    idleTimeoutMillis: 5_000
  });
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

async function createSchemaBackup(input: {
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
      "--schema=reos_infra",
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
    throw new Error("PostgreSQL produced an empty B4 backup.");
  }

  return result.stdout;
}

b4RecoverySuite(
  "B4 actual PostgreSQL infrastructure backup and recovery",
  () => {
    it(
      "restores actual B4 migrations, durable sessions, audit records and security boundaries",
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
        const migrationRole = `homio_b4_m_${suffix}`;
        const applicationRole = `homio_b4_a_${suffix}`;

        const migrationPassword = randomBytes(32).toString("hex");
        const applicationPassword = randomBytes(32).toString("hex");

        const quotedDatabase = quoteIdentifier(databaseName);
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

        let adminPool: TestPgPool | undefined;
        let targetAdminPool: TestPgPool | undefined;
        let migrationPool: TestPgPool | undefined;
        let applicationPool: TestPgPool | undefined;
        let runtime: PostgresRuntime | undefined;
        let databaseCreated = false;

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

          const b4Migrations = completeManifest.filter(
            (migration) =>
              migration.id === "00000003" ||
              migration.id === "00000004"
          );

          expect(
            b4Migrations.map((migration) => migration.id)
          ).toEqual(["00000003", "00000004"]);

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

          expect(migrationReport.appliedCount).toBe(2);
          expect(migrationReport.latestMigrationId).toBe("00000004");

          applicationPool = createPool(applicationUrl, 1);

          runtime = new PostgresRuntime(
            applicationPool as unknown as PostgresDriverPool
          );

          await runtime.verifyRuntimeRoleSafety();

          const context: TrustedRequestContext = {
            identityId: randomUUID(),
            accountId: randomUUID(),
            authenticationEpoch: 1,
            tenantId: randomUUID(),
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

          const sessionStore = new PostgresSessionStore(runtime);

          const sessionId = await sessionStore.establishSession({
            principal,
            context
          });

          await expect(
            sessionStore.isSessionActive({
              principal,
              context
            })
          ).resolves.toBe(true);

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

          const auditStore = new PostgresSecurityAuditStore(
            applicationPool
          );

          await auditStore.record(auditEvent);

          const beforeBackup = await targetAdminPool.query(`
            SELECT
              (SELECT count(*)::integer
                 FROM reos_infra.api_sessions) AS session_count,
              (SELECT count(*)::integer
                 FROM reos_infra.security_audit_events
                WHERE request_id = '${requestId}') AS audit_count,
              (SELECT count(*)::integer
                 FROM reos_infra.schema_migrations) AS migration_count
          `);

          expect(beforeBackup.rows[0]).toMatchObject({
            session_count: 1,
            audit_count: 1,
            migration_count: 2
          });

          const backupSql = await createSchemaBackup({
            containerId: postgresContainerId,
            databaseName,
            adminPassword
          });

          expect(backupSql).toContain("api_sessions");
          expect(backupSql).toContain("security_audit_events");
          expect(backupSql).toContain("schema_migrations");
          expect(backupSql).toContain("CREATE POLICY");
          expect(backupSql).toContain("CREATE TRIGGER");

          await runtime.close();
          runtime = undefined;
          applicationPool = undefined;

          await migrationPool.end();
          migrationPool = undefined;

          await targetAdminPool.query(
            "DROP SCHEMA reos_infra CASCADE"
          );

          await runPsqlInContainer({
            containerId: postgresContainerId,
            databaseName,
            adminPassword,
            sql: backupSql
          });

          migrationPool = createPool(migrationUrl, 1);

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
          ).toBe("00000004");

          const restoredLedger = await targetAdminPool.query(`
            SELECT migration_id, checksum
            FROM reos_infra.schema_migrations
            ORDER BY migration_id
          `);

          expect(
            restoredLedger.rows.map((row) => row.migration_id)
          ).toEqual(["00000003", "00000004"]);

          expect(
            restoredLedger.rows.map((row) => row.checksum)
          ).toEqual(
            b4Migrations.map((migration) => migration.checksum)
          );

          await migrationPool.end();
          migrationPool = undefined;

          applicationPool = createPool(applicationUrl, 1);

          runtime = new PostgresRuntime(
            applicationPool as unknown as PostgresDriverPool
          );

          await runtime.verifyRuntimeRoleSafety();

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
              principal,
              context: {
                ...context,
                tenantId: randomUUID()
              }
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

          const owners = await targetAdminPool.query(`
            SELECT
              namespace.nspname AS schema_name,
              pg_get_userbyid(namespace.nspowner) AS schema_owner,
              relation.relname AS relation_name,
              pg_get_userbyid(relation.relowner) AS table_owner
            FROM pg_namespace AS namespace
            JOIN pg_class AS relation
              ON relation.relnamespace = namespace.oid
            WHERE namespace.nspname = 'reos_infra'
              AND relation.relkind = 'r'
            ORDER BY relation.relname
          `);

          expect(
            owners.rows.map((row) => row.relation_name)
          ).toEqual([
            "api_sessions",
            "schema_migrations",
            "security_audit_events"
          ]);

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
            "security_audit_events_append_only"
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
              ) AS audit_delete
          `, [applicationRole]);

          expect(privileges.rows[0]).toEqual({
            schema_usage: true,
            schema_create: false,
            session_select: true,
            session_insert: true,
            session_update: true,
            session_delete: false,
            audit_insert: true,
            audit_select: false,
            audit_update: false,
            audit_delete: false
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

          expect(true).toBe(true);
        } finally {
          if (runtime !== undefined) {
            await runtime.close().catch(() => undefined);
          } else if (applicationPool !== undefined) {
            await applicationPool.end().catch(() => undefined);
          }

          await migrationPool?.end().catch(() => undefined);
          await targetAdminPool?.end().catch(() => undefined);

          if (adminPool !== undefined) {
            if (databaseCreated) {
              await adminPool.query(
                `DROP DATABASE IF EXISTS ${quotedDatabase} WITH (FORCE)`
              ).catch(() => undefined);
            }

            await adminPool.query(
              `DROP ROLE IF EXISTS ${quotedApplicationRole}`
            ).catch(() => undefined);

            await adminPool.query(
              `DROP ROLE IF EXISTS ${quotedMigrationRole}`
            ).catch(() => undefined);

            await adminPool.end().catch(() => undefined);
          }
        }
      },
      TEST_TIMEOUT_MS
    );
  }
);
