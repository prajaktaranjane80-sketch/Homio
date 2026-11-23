import {
  createHash,
  randomBytes,
  randomUUID
} from "node:crypto";

import { createRequire } from "node:module";
import { resolve } from "node:path";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import type {
  PostgresDriverPool
} from "../../src/persistence/postgres.js";

import {
  PostgresRuntime
} from "../../src/persistence/postgres.js";

import {
  PostgresMigrationRunner
} from "../../src/persistence/postgres-migrations.js";

import {
  loadPostgresMigrationManifest
} from "../../src/persistence/postgres-migration-manifest.js";

import {
  PostgresCore002EventOutboxRepository
} from "../../src/persistence/postgres-core002-outbox.js";

import type {
  Core002OutboxContract
} from "../../src/persistence/postgres-core002-outbox.js";

interface QueryResult {
  readonly rows: readonly Record<string, unknown>[];
  readonly rowCount: number | null;
}

interface TestClient {
  query(
    text: string,
    values?: unknown[]
  ): Promise<QueryResult>;

  release(error?: Error | boolean): void;
}

interface TestPool {
  query(
    text: string,
    values?: unknown[]
  ): Promise<QueryResult>;

  connect(): Promise<TestClient>;

  end(): Promise<void>;
}

interface PgModule {
  readonly Pool: new (options: {
    readonly connectionString: string;
    readonly max?: number;
  }) => TestPool;
}

const require = createRequire(import.meta.url);
const pgModule = require("pg") as PgModule;

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;

const enabled =
  typeof adminUrl === "string" &&
  adminUrl.length > 0;

function quoteIdentifier(value: string): string {
  return `"${value.replaceAll('"', '""')}"`;
}

function quoteLiteral(value: string): string {
  return `'${value.replaceAll("'", "''")}'`;
}

function connectionUrl(
  baseUrl: string,
  database: string,
  role?: string,
  password?: string
): string {
  const url = new URL(baseUrl);

  url.pathname = `/${database}`;

  if (role !== undefined) {
    url.username = role;
  }

  if (password !== undefined) {
    url.password = password;
  }

  url.search = "";
  url.hash = "";

  return url.toString();
}

function makeCanonicalEvent(
  tenantId: string,
  eventId: string,
  idempotencyKey: string
): {
  readonly serializedEnvelope: string;
  readonly immutableFingerprint: string;
} {
  const timestamp = new Date().toISOString();

  const envelope = {
    causation_id: null,
    correlation_id: randomUUID(),
    event_id: eventId,
    event_type: "core002.integration.probe",
    event_version: 1,
    idempotency_key: idempotencyKey,
    metadata: {},
    observed_at: timestamp,
    occurred_at: timestamp,
    ordering_key: null,
    payload: {
      marker: "postgres-integration"
    },
    producer_id: randomUUID(),
    schema_name: "homio.integration",
    schema_version: 1,
    sequence: null,
    tenant_id: tenantId,
    trace_context: null
  };

  const serializedEnvelope = JSON.stringify(envelope);

  const immutableFingerprint = createHash("sha256")
    .update(serializedEnvelope, "utf8")
    .digest("hex");

  return {
    serializedEnvelope,
    immutableFingerprint
  };
}

function makeContract(
  tenantId: string,
  eventId: string,
  eventFingerprint: string
): Core002OutboxContract {
  return {
    publicationId: randomUUID(),
    tenantId,
    eventId,
    eventFingerprint,
    createdAt: new Date(),
    state: "CREATED"
  };
}

describe.skipIf(!enabled)(
  "CORE-002 actual PostgreSQL event and outbox persistence",
  () => {
    const suffix = randomBytes(8).toString("hex");

    const databaseName = `homio_b4_${suffix}`;
    const migrationRole = `homio_b4_m_${suffix}`;
    const applicationRole = `homio_b4_a_${suffix}`;

    const migrationPassword = randomBytes(32).toString("hex");
    const applicationPassword = randomBytes(32).toString("hex");

    const tenantA = randomUUID();
    const tenantB = randomUUID();

    let rootPool: TestPool | undefined;
    let adminPool: TestPool | undefined;
    let migrationPool: TestPool | undefined;
    let applicationPool: TestPool | undefined;
    let runtime: PostgresRuntime | undefined;

    let databaseCreated = false;
    let migrationRoleCreated = false;
    let applicationRoleCreated = false;

    beforeAll(async () => {
      if (!adminUrl) {
        throw new Error(
          "HOMIO_TEST_POSTGRES_ADMIN_URL is required."
        );
      }

      rootPool = new pgModule.Pool({
        connectionString: adminUrl,
        max: 2
      });

      const versionResult = await rootPool.query(
        `
          SELECT
            current_setting('server_version_num')::integer
              AS server_version_num
        `
      );

      const version = Number(
        versionResult.rows[0]?.server_version_num
      );

      if (
        !Number.isSafeInteger(version) ||
        version < 180004
      ) {
        throw new Error(
          "CORE-002 integration requires PostgreSQL 18.4 or newer."
        );
      }

      await rootPool.query(
        `CREATE DATABASE ${quoteIdentifier(databaseName)}`
      );

      databaseCreated = true;

      await rootPool.query(`
        CREATE ROLE ${quoteIdentifier(migrationRole)}
          LOGIN INHERIT NOSUPERUSER NOBYPASSRLS
          PASSWORD ${quoteLiteral(migrationPassword)}
      `);

      migrationRoleCreated = true;

      await rootPool.query(`
        CREATE ROLE ${quoteIdentifier(applicationRole)}
          LOGIN INHERIT NOSUPERUSER NOBYPASSRLS
          PASSWORD ${quoteLiteral(applicationPassword)}
      `);

      applicationRoleCreated = true;

      adminPool = new pgModule.Pool({
        connectionString: connectionUrl(
          adminUrl,
          databaseName
        ),
        max: 4
      });

      await adminPool.query(`
        CREATE SCHEMA reos_infra
          AUTHORIZATION ${quoteIdentifier(migrationRole)}
      `);

      const ledgerOwner = await adminPool.connect();

      try {
        await ledgerOwner.query(
          `SET ROLE ${quoteIdentifier(migrationRole)}`
        );

        await ledgerOwner.query(`
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

        await ledgerOwner.query("RESET ROLE");
      } finally {
        ledgerOwner.release();
      }

      await adminPool.query(`
        ALTER DEFAULT PRIVILEGES
        FOR ROLE ${quoteIdentifier(migrationRole)}
        IN SCHEMA reos_infra
        REVOKE ALL ON TABLES
        FROM PUBLIC, ${quoteIdentifier(applicationRole)}
      `);

      await adminPool.query(
        "REVOKE ALL ON SCHEMA reos_infra FROM PUBLIC"
      );

      await adminPool.query(`
        REVOKE ALL ON SCHEMA reos_infra
        FROM ${quoteIdentifier(applicationRole)}
      `);

      await adminPool.query(
        "REVOKE ALL ON TABLE reos_infra.schema_migrations FROM PUBLIC"
      );

      await adminPool.query(`
        REVOKE ALL ON TABLE reos_infra.schema_migrations
        FROM ${quoteIdentifier(applicationRole)}
      `);

      await adminPool.query(`
        CREATE SCHEMA core002
          AUTHORIZATION ${quoteIdentifier(migrationRole)}
      `);

      await adminPool.query(`
        GRANT USAGE ON SCHEMA core002
        TO ${quoteIdentifier(applicationRole)}
      `);

      await adminPool.query(`
        ALTER DEFAULT PRIVILEGES
        FOR ROLE ${quoteIdentifier(migrationRole)}
        IN SCHEMA core002
        REVOKE ALL ON TABLES
        FROM PUBLIC, ${quoteIdentifier(applicationRole)}
      `);

      migrationPool = new pgModule.Pool({
        connectionString: connectionUrl(
          adminUrl,
          databaseName,
          migrationRole,
          migrationPassword
        ),
        max: 1
      });

      applicationPool = new pgModule.Pool({
        connectionString: connectionUrl(
          adminUrl,
          databaseName,
          applicationRole,
          applicationPassword
        ),
        max: 3
      });

      const migrations = await loadPostgresMigrationManifest(
        resolve(process.cwd(), "scripts", "postgres", "migrations"),
        {
          migrationRole,
          applicationRole,
          schemaName: "core002"
        }
      );

      const runner = new PostgresMigrationRunner(
        migrationPool as unknown as PostgresDriverPool,
        {
          migrationRole,
          applicationRole
        }
      );

      const report = await runner.migrate(migrations);

      expect(report.appliedCount).toBe(1);
      expect(report.latestMigrationId).toBe("00000001");

      runtime = new PostgresRuntime(
        applicationPool as unknown as PostgresDriverPool
      );

      await runtime.verifyRuntimeRoleSafety();
    }, 60000);

    afterAll(async () => {
      if (runtime !== undefined) {
        await runtime.close().catch(() => undefined);
      } else {
        await applicationPool?.end().catch(() => undefined);
      }

      await migrationPool?.end().catch(() => undefined);
      await adminPool?.end().catch(() => undefined);

      if (rootPool !== undefined) {
        if (databaseCreated) {
          await rootPool.query(
            `DROP DATABASE IF EXISTS ${quoteIdentifier(databaseName)} WITH (FORCE)`
          ).catch(() => undefined);
        }

        if (applicationRoleCreated) {
          await rootPool.query(
            `DROP ROLE IF EXISTS ${quoteIdentifier(applicationRole)}`
          ).catch(() => undefined);
        }

        if (migrationRoleCreated) {
          await rootPool.query(
            `DROP ROLE IF EXISTS ${quoteIdentifier(migrationRole)}`
          ).catch(() => undefined);
        }

        await rootPool.end().catch(() => undefined);
      }
    }, 60000);

    it("enforces append, outbox transitions, tenant isolation and atomic rollback", async () => {
      if (runtime === undefined || applicationPool === undefined) {
        throw new Error(
          "The CORE-002 PostgreSQL fixture was not initialized."
        );
      }

      const eventId = randomUUID();

      const event = makeCanonicalEvent(
        tenantA,
        eventId,
        `integration-${randomUUID()}`
      );

      const contract = makeContract(
        tenantA,
        eventId,
        event.immutableFingerprint
      );

      const inserted = await runtime.withTenantTransaction(
        { tenantId: tenantA },
        async (transaction) => {
          const repository =
            new PostgresCore002EventOutboxRepository(transaction);

          const created = await repository.appendEvent(event);

          await repository.stage(contract);
          await repository.commit(contract.publicationId);

          return created;
        }
      );

      expect(inserted).toBe(true);

      const pending = await runtime.withTenantTransaction(
        { tenantId: tenantA },
        (transaction) =>
          new PostgresCore002EventOutboxRepository(
            transaction
          ).recoverUnpublished()
      );

      expect(pending).toHaveLength(1);
      expect(pending[0]?.publicationId).toBe(
        contract.publicationId
      );
      expect(pending[0]?.state).toBe("COMMITTED");

      await runtime.withTenantTransaction(
        { tenantId: tenantA },
        (transaction) =>
          new PostgresCore002EventOutboxRepository(
            transaction
          ).markPublished(contract.publicationId)
      );

      const recoveredAfterPublish =
        await runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).recoverUnpublished()
        );

      expect(recoveredAfterPublish).toHaveLength(0);

      const duplicate = await runtime.withTenantTransaction(
        { tenantId: tenantA },
        (transaction) =>
          new PostgresCore002EventOutboxRepository(
            transaction
          ).appendEvent(event)
      );

      expect(duplicate).toBe(false);

      const concurrentId = randomUUID();

      const concurrentEvent = makeCanonicalEvent(
        tenantA,
        concurrentId,
        `concurrent-${randomUUID()}`
      );

      const concurrentResults = await Promise.all([
        runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).appendEvent(concurrentEvent)
        ),
        runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).appendEvent(concurrentEvent)
        )
      ]);

      expect(
        concurrentResults.filter((value) => value === true)
      ).toHaveLength(1);

      expect(
        concurrentResults.filter((value) => value === false)
      ).toHaveLength(1);

      const rolledBackEventId = randomUUID();

      const rolledBackEvent = makeCanonicalEvent(
        tenantA,
        rolledBackEventId,
        `rollback-${randomUUID()}`
      );

      const rolledBackContract = makeContract(
        tenantA,
        rolledBackEventId,
        rolledBackEvent.immutableFingerprint
      );

      await expect(
        runtime.withTenantTransaction(
          { tenantId: tenantA },
          async (transaction) => {
            const repository =
              new PostgresCore002EventOutboxRepository(
                transaction
              );

            await repository.appendEvent(rolledBackEvent);
            await repository.stage(rolledBackContract);
            await repository.commit(
              rolledBackContract.publicationId
            );

            throw new Error("intentional aggregate rollback");
          }
        )
      ).rejects.toThrow("intentional aggregate rollback");

      const rolledBackCount =
        await runtime.withTenantTransaction(
          { tenantId: tenantA },
          async (transaction) => {
            const result = await transaction.query<{
              count: number;
            }>(
              `
                SELECT count(*)::integer AS count
                FROM core002.events
                WHERE tenant_id = $1
                  AND event_id = $2
              `,
              [tenantA, rolledBackEventId]
            );

            return Number(result.rows[0]?.count ?? 0);
          }
        );

      expect(rolledBackCount).toBe(0);

      const visibleToTenantB =
        await runtime.withTenantTransaction(
          { tenantId: tenantB },
          async (transaction) => {
            const result = await transaction.query<{
              count: number;
            }>(
              `
                SELECT count(*)::integer AS count
                FROM core002.events
                WHERE tenant_id = $1
              `,
              [tenantA]
            );

            return Number(result.rows[0]?.count ?? 0);
          }
        );

      expect(visibleToTenantB).toBe(0);

      const noContext = await applicationPool.query(
        `
          SELECT count(*)::integer AS count
          FROM core002.events
        `
      );

      expect(Number(noContext.rows[0]?.count ?? 0)).toBe(0);

      const crossTenantEvent = makeCanonicalEvent(
        tenantB,
        randomUUID(),
        `cross-tenant-${randomUUID()}`
      );

      const crossTenantEventId = (
        JSON.parse(crossTenantEvent.serializedEnvelope) as {
          event_id: string;
        }
      ).event_id;

      await expect(
        runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).appendEvent(crossTenantEvent)
        )
      ).rejects.toThrow(
        "event tenant does not match the PostgreSQL transaction tenant"
      );

      await expect(
        runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            transaction.query(
              `
                INSERT INTO core002.events (
                  tenant_id,
                  event_id,
                  envelope,
                  immutable_fingerprint
                )
                VALUES ($1, $2, $3::jsonb, $4)
              `,
              [
                tenantB,
                crossTenantEventId,
                crossTenantEvent.serializedEnvelope,
                crossTenantEvent.immutableFingerprint
              ]
            )
        )
      ).rejects.toThrow();
    }, 60000);
  }
);
