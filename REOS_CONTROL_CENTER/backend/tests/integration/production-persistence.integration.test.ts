import { randomBytes, randomUUID } from "node:crypto";
import { createRequire } from "node:module";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import type { BackendSettings } from "../../src/config/settings.js";
import type { PostgresDriverPool } from "../../src/persistence/postgres.js";
import {
  PostgresMigrationRunner
} from "../../src/persistence/postgres-migrations.js";
import {
  createProductionPersistenceRuntime,
  type ProductionPersistenceRuntime,
  type ProductionRedisClient
} from "../../src/persistence/production-runtime.js";
import {
  RedisRateLimiter
} from "../../src/persistence/redis-rate-limit.js";

interface TestQueryResult {
  readonly rows: readonly Record<string, unknown>[];
  readonly rowCount: number | null;
}

interface TestPostgresClient {
  query(
    text: string,
    values?: unknown[]
  ): Promise<TestQueryResult>;

  release(error?: Error | boolean): void;
}

interface TestPostgresPool {
  connect(): Promise<TestPostgresClient>;

  query(
    text: string,
    values?: unknown[]
  ): Promise<TestQueryResult>;

  end(): Promise<void>;
}

interface PgModule {
  readonly Pool: new (options: {
    readonly connectionString: string;
    readonly max?: number;
  }) => TestPostgresPool;
}

interface RedisModule {
  readonly createClient: (options: {
    readonly url: string;
  }) => ProductionRedisClient;
}

const require = createRequire(import.meta.url);

const pgModule = require("pg") as PgModule;
const redisModule = require("@redis/client") as RedisModule;

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
const redisUrl = process.env.HOMIO_TEST_REDIS_URL;

const integrationEnabled =
  typeof adminUrl === "string" &&
  adminUrl.length > 0 &&
  typeof redisUrl === "string" &&
  redisUrl.length > 0;

const API_ROLE = "homio_b4_api";
const SCHEMA_OWNER_ROLE = "homio_b4_schema_owner";

function quoteIdentifier(value: string): string {
  return `"${value.replaceAll("\"", "\"\"")}"`;
}

function quoteLiteral(value: string): string {
  return `'${value.replaceAll("'", "''")}'`;
}

function connectionUrl(
  baseUrl: string,
  username: string,
  password: string
): string {
  const url = new URL(baseUrl);

  url.username = username;
  url.password = password;

  return url.toString();
}

const testTimeoutMs = 30_000;

describe.skipIf(!integrationEnabled)(
  "B4 real Node.js PostgreSQL and Redis integration",
  () => {
    let adminPool: TestPostgresPool | undefined;
    let migrationPool: TestPostgresPool | undefined;
    let runtime: ProductionPersistenceRuntime | undefined;
    let secondaryRedis: ProductionRedisClient | undefined;

    let tenantSchema = "";
    let migrationSchema = "";
    let migrationRole = "";

    let createdTenantSchema = false;
    let createdMigrationSchema = false;
    let createdInfraSchema = false;
    let createdMigrationRole = false;

    let applicationUrl = "";
    let migrationUrl = "";

    const suffix = randomBytes(8).toString("hex");

    const applicationPassword = randomBytes(32).toString("hex");
    const migrationPassword = randomBytes(32).toString("hex");

    const tenantA = randomUUID();
    const tenantB = randomUUID();

    const migrationTableName = "migration_probe";

    const tenantTable = (): string =>
      `${quoteIdentifier(tenantSchema)}.tenant_records`;

    beforeAll(async () => {
      if (!adminUrl || !redisUrl) {
        throw new Error(
          "The PostgreSQL and Redis integration endpoints are required."
        );
      }

      adminPool = new pgModule.Pool({
        connectionString: adminUrl,
        max: 4
      });

      const versionResult = await adminPool.query(
        "SELECT current_setting('server_version_num')::integer AS server_version_num"
      );

      const version = Number(
        versionResult.rows[0]?.server_version_num
      );

      if (!Number.isSafeInteger(version) || version < 180004) {
        throw new Error(
          "The Node.js PostgreSQL integration test requires PostgreSQL 18.4 or newer."
        );
      }

      tenantSchema = `homio_node_${suffix}`;
      migrationSchema = `homio_node_mig_${suffix}`;
      migrationRole = `homio_node_m_${suffix}`;

      applicationUrl = connectionUrl(
        adminUrl,
        API_ROLE,
        applicationPassword
      );

      migrationUrl = connectionUrl(
        adminUrl,
        migrationRole,
        migrationPassword
      );

      // The previous Python integration steps provision this existing role
      // and its schema-owner role. Reuse them; do not create another API role.
      await adminPool.query(
        `ALTER ROLE ${quoteIdentifier(API_ROLE)} PASSWORD ${quoteLiteral(applicationPassword)}`
      );

      await adminPool.query(
        `CREATE SCHEMA ${quoteIdentifier(tenantSchema)} AUTHORIZATION ${quoteIdentifier(SCHEMA_OWNER_ROLE)}`
      );

      createdTenantSchema = true;

      const ownerClient = await adminPool.connect();

      try {
        await ownerClient.query(
          `SET ROLE ${quoteIdentifier(SCHEMA_OWNER_ROLE)}`
        );

        await ownerClient.query(`
          CREATE TABLE ${tenantTable()} (
            record_id uuid PRIMARY KEY,
            tenant_id uuid NOT NULL,
            payload text NOT NULL
          )
        `);

        await ownerClient.query(
          `ALTER TABLE ${tenantTable()} ENABLE ROW LEVEL SECURITY`
        );

        await ownerClient.query(
          `ALTER TABLE ${tenantTable()} FORCE ROW LEVEL SECURITY`
        );

        await ownerClient.query(`
          CREATE POLICY homio_node_test_permissive
          ON ${tenantTable()}
          AS PERMISSIVE
          FOR ALL
          TO ${quoteIdentifier(API_ROLE)}
          USING (true)
          WITH CHECK (true)
        `);

        await ownerClient.query(`
          CREATE POLICY homio_node_test_tenant_guard
          ON ${tenantTable()}
          AS RESTRICTIVE
          FOR ALL
          TO ${quoteIdentifier(API_ROLE)}
          USING (
            tenant_id = CASE
              WHEN pg_input_is_valid(
                current_setting('app.tenant_id', true),
                'uuid'
              )
              THEN current_setting('app.tenant_id', true)::uuid
              ELSE NULL::uuid
            END
          )
          WITH CHECK (
            tenant_id = CASE
              WHEN pg_input_is_valid(
                current_setting('app.tenant_id', true),
                'uuid'
              )
              THEN current_setting('app.tenant_id', true)::uuid
              ELSE NULL::uuid
            END
          )
        `);
      } finally {
        await ownerClient.query("RESET ROLE").catch(() => undefined);
        ownerClient.release();
      }

      await adminPool.query(
        `GRANT USAGE ON SCHEMA ${quoteIdentifier(tenantSchema)} TO ${quoteIdentifier(API_ROLE)}`
      );

      await adminPool.query(
        `GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE ${tenantTable()} TO ${quoteIdentifier(API_ROLE)}`
      );

      // The canonical migration runner expects the already-provisioned
      // reos_infra.schema_migrations ledger. This test provisions only its
      // disposable CI instance and never touches business-domain tables.
      const infraResult = await adminPool.query(`
        SELECT count(*)::integer AS count
        FROM pg_namespace
        WHERE nspname = 'reos_infra'
      `);

      if (Number(infraResult.rows[0]?.count) !== 0) {
        throw new Error(
          "The disposable PostgreSQL test database already contains reos_infra."
        );
      }

      await adminPool.query(`
        CREATE ROLE ${quoteIdentifier(migrationRole)}
        LOGIN INHERIT NOSUPERUSER NOBYPASSRLS
        PASSWORD ${quoteLiteral(migrationPassword)}
      `);

      createdMigrationRole = true;

      await adminPool.query(
        `CREATE SCHEMA reos_infra AUTHORIZATION ${quoteIdentifier(migrationRole)}`
      );

      createdInfraSchema = true;

      await adminPool.query(
        `CREATE SCHEMA ${quoteIdentifier(migrationSchema)} AUTHORIZATION ${quoteIdentifier(migrationRole)}`
      );

      createdMigrationSchema = true;

      const migrationOwnerClient = await adminPool.connect();

      try {
        await migrationOwnerClient.query(
          `SET ROLE ${quoteIdentifier(migrationRole)}`
        );

        await migrationOwnerClient.query(`
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
      } finally {
        await migrationOwnerClient.query("RESET ROLE").catch(() => undefined);
        migrationOwnerClient.release();
      }

      await adminPool.query(`
        ALTER DEFAULT PRIVILEGES
        FOR ROLE ${quoteIdentifier(migrationRole)}
        IN SCHEMA reos_infra
        REVOKE ALL ON TABLES FROM PUBLIC, ${quoteIdentifier(API_ROLE)}
      `);

      await adminPool.query(
        "REVOKE ALL ON SCHEMA reos_infra FROM PUBLIC"
      );

      await adminPool.query(
        `REVOKE ALL ON SCHEMA reos_infra FROM ${quoteIdentifier(API_ROLE)}`
      );

      await adminPool.query(
        "REVOKE ALL ON TABLE reos_infra.schema_migrations FROM PUBLIC"
      );

      await adminPool.query(
        `REVOKE ALL ON TABLE reos_infra.schema_migrations FROM ${quoteIdentifier(API_ROLE)}`
      );

      migrationPool = new pgModule.Pool({
        connectionString: migrationUrl,
        max: 1
      });

      const settings = {
        nodeEnv: "test",
        host: "127.0.0.1",
        port: 0,
        logLevel: "silent",
        requestTimeoutMs: 10_000,
        shutdownTimeoutMs: 5_000,

        postgres: {
          connectionString: applicationUrl,
          sslMode: "disable",
          poolMax: 1,
          connectionTimeoutMs: 5_000,
          idleTimeoutMs: 5_000,
          statementTimeoutMs: 5_000
        },

        redis: {
          url: redisUrl,
          connectTimeoutMs: 5_000
        }
      } satisfies BackendSettings;

      runtime = await createProductionPersistenceRuntime(settings);

      await runtime.verifyReadiness();

      if (!runtime.isHealthy()) {
        throw new Error(
          "The real Node.js PostgreSQL and Redis clients did not become healthy."
        );
      }
    }, testTimeoutMs);

    afterAll(async () => {
      await runtime?.close().catch(() => undefined);

      await migrationPool?.end().catch(() => undefined);

      if (secondaryRedis !== undefined) {
        try {
          if (secondaryRedis.isOpen) {
            await secondaryRedis.quit();
          } else {
            secondaryRedis.destroy();
          }
        } catch {
          secondaryRedis.destroy();
        }
      }

      if (adminPool !== undefined) {
        if (createdTenantSchema) {
          await adminPool.query(
            `DROP SCHEMA IF EXISTS ${quoteIdentifier(tenantSchema)} CASCADE`
          ).catch(() => undefined);
        }

        if (createdMigrationSchema) {
          await adminPool.query(
            `DROP SCHEMA IF EXISTS ${quoteIdentifier(migrationSchema)} CASCADE`
          ).catch(() => undefined);
        }

        if (createdInfraSchema) {
          await adminPool.query(
            "DROP SCHEMA IF EXISTS reos_infra CASCADE"
          ).catch(() => undefined);
        }

        if (createdMigrationRole) {
          await adminPool.query(
            `DROP ROLE IF EXISTS ${quoteIdentifier(migrationRole)}`
          ).catch(() => undefined);
        }

        await adminPool.end().catch(() => undefined);
      }
    }, testTimeoutMs);

    it("verifies the actual Node.js database, migration, RLS and Redis owners", async () => {
      if (
        adminPool === undefined ||
        migrationPool === undefined ||
        runtime === undefined
      ) {
        throw new Error(
          "The real-service integration fixture was not initialized."
        );
      }

      // One checked-out PostgreSQL connection is reused deliberately.
      // The transaction-local tenant must not leak into the next transaction.
      const inserted = await runtime.postgres.withTenantTransaction(
        { tenantId: tenantA },
        (transaction) => transaction.query(
          `INSERT INTO ${tenantTable()} (record_id, tenant_id, payload)
           VALUES ($1, $2, $3)
           RETURNING record_id`,
          [randomUUID(), tenantA, "tenant-a"]
        )
      );

      expect(inserted.rows).toHaveLength(1);

      const visibleToA = await runtime.postgres.withTenantTransaction(
        { tenantId: tenantA },
        (transaction) => transaction.query(
          `SELECT count(*)::integer AS count
           FROM ${tenantTable()}`
        )
      );

      expect(
        Number(visibleToA.rows[0]?.count)
      ).toBe(1);

      await expect(
        runtime.postgres.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) => transaction.query(
            `INSERT INTO ${tenantTable()} (record_id, tenant_id, payload)
             VALUES ($1, $2, $3)`,
            [randomUUID(), tenantB, "cross-tenant-forbidden"]
          )
        )
      ).rejects.toThrow();

      const visibleToB = await runtime.postgres.withTenantTransaction(
        { tenantId: tenantB },
        (transaction) => transaction.query(
          `SELECT count(*)::integer AS count
           FROM ${tenantTable()}`
        )
      );

      expect(
        Number(visibleToB.rows[0]?.count)
      ).toBe(0);

      // Run the existing TypeScript migration owner through the real pg Pool.
      const migrationPoolAsOwner =
        migrationPool as unknown as PostgresDriverPool;

      const runner = new PostgresMigrationRunner(
        migrationPoolAsOwner,
        {
          migrationRole,
          applicationRole: API_ROLE
        }
      );

      const migrations = [{
        id: "00000001",
        name: "node-driver-integration-proof",
        sql: `
          CREATE TABLE ${quoteIdentifier(migrationSchema)}.${migrationTableName} (
            marker text PRIMARY KEY NOT NULL
          )
        `
      }] as const;

      const firstReport = await runner.migrate(migrations);

      expect(firstReport.appliedCount).toBe(1);
      expect(firstReport.latestMigrationId).toBe("00000001");
      expect(firstReport.latestChecksum).toMatch(/^[a-f0-9]{64}$/);

      const secondReport = await runner.migrate(migrations);

      expect(secondReport.appliedCount).toBe(0);
      expect(secondReport.latestMigrationId).toBe("00000001");

      const createdMigrationTable = await adminPool.query(
        `SELECT to_regclass($1)::text AS relation`,
        [`${migrationSchema}.${migrationTableName}`]
      );

      expect(
        createdMigrationTable.rows[0]?.relation
      ).not.toBeNull();

      // The API role must not be able to read the infrastructure ledger.
      const apiProbePool = new pgModule.Pool({
        connectionString: applicationUrl,
        max: 1
      });

      try {
        await expect(
          apiProbePool.query(
            "SELECT migration_id FROM reos_infra.schema_migrations"
          )
        ).rejects.toThrow();
      } finally {
        await apiProbePool.end();
      }

      // Two independent Redis clients must observe the same atomic counter.
      secondaryRedis = redisModule.createClient({
        url: redisUrl as string
      });

      await secondaryRedis.connect();

      const rateLimitOptions = {
        keySecret: randomBytes(32).toString("hex"),
        keyVersion: "node-integration-v1",
        policyVersion: `ci-${suffix}`,
        policies: {
          "api-ip": {
            maxRequests: 10,
            windowMs: 5_000
          },
          "api-identity-tenant": {
            maxRequests: 15,
            windowMs: 5_000
          }
        }
      } as const;

      const limiterA = new RedisRateLimiter(
        runtime.redis,
        rateLimitOptions
      );

      const limiterB = new RedisRateLimiter(
        secondaryRedis,
        rateLimitOptions
      );

      const decisions = await Promise.all(
        Array.from({ length: 24 }, (_, index) => {
          const limiter = index % 2 === 0
            ? limiterA
            : limiterB;

          return limiter.consume({
            bucket: "api-ip",
            key: `node-integration-${suffix}`
          });
        })
      );

      const allowed = decisions.filter(
        (decision) => decision.allowed
      );

      const denied = decisions.filter(
        (decision) => !decision.allowed
      );

      expect(allowed).toHaveLength(10);
      expect(denied).toHaveLength(14);

      expect(
        denied.every(
          (decision) =>
            decision.retryAfterSeconds !== undefined &&
            decision.retryAfterSeconds >= 1
        )
      ).toBe(true);

      await runtime.verifyReadiness();

      expect(runtime.isHealthy()).toBe(true);
    }, testTimeoutMs);
  }
);
