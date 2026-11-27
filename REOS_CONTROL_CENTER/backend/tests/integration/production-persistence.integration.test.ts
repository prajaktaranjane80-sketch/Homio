import { execFileSync } from "node:child_process";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

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
  loadPostgresMigrationManifest
} from "../../src/persistence/postgres-migration-manifest.js";
import {
  PostgresMigrationRunner
} from "../../src/persistence/postgres-migrations.js";
import {
  createProductionPersistenceRuntime,
  type ProductionPersistenceRuntime,
  type ProductionRedisClient
} from "../../src/persistence/production-runtime.js";
import type {
  SecurityAuditEvent,
  TrustedRequestContext,
  VerifiedExternalPrincipal
} from "../../src/security/contracts.js";
import {
  PostgresSessionStore
} from "../../src/persistence/postgres-session-store.js";
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

const testTimeoutMs = 30_000;

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

function sha256(value: string): string {
  return createHash("sha256")
    .update(value, "utf8")
    .digest("hex");
}

describe.skipIf(!integrationEnabled)(
  "B4 real Node.js PostgreSQL and Redis integration",
  () => {
    let adminPool: TestPostgresPool | undefined;
    let migrationPool: TestPostgresPool | undefined;
    let runtime: ProductionPersistenceRuntime | undefined;

    let tenantSchema = "";
    let migrationRole = "";

    let createdTenantSchema = false;
    let createdInfraSchema = false;
    let createdMigrationRole = false;

    let applicationUrl = "";
    let migrationUrl = "";

    let b4Migrations:
      Awaited<ReturnType<typeof loadPostgresMigrationManifest>> = [];

    let migrationRunner: PostgresMigrationRunner | undefined;

    let initialMigrationAppliedCount = -1;
    let initialMigrationLatestId = "";

    const suffix = randomBytes(8).toString("hex");

    const applicationPassword = randomBytes(32).toString("hex");
    const migrationPassword = randomBytes(32).toString("hex");

    const tenantA = randomUUID();
    const tenantB = randomUUID();

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

      /*
       * Reuse the existing CI API and schema-owner roles.
       * This test does not create another API identity or persistence owner.
       */

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

      /*
       * Provision only the infrastructure migration ledger.
       *
       * The ledger is owned by a separate migration login.
       * The API role cannot read or create objects in this schema.
       */

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

      /*
       * Load the existing canonical manifest.
       *
       * Execute the B4-owned session, base audit and tenant-write-guard
       * migrations 00000003, 00000004 and 00000011. CORE-002 and other
       * domain migrations are not applied by this fixture.
       */

      const migrationsDirectory = fileURLToPath(
        new URL("../../scripts/postgres/migrations/", import.meta.url)
      );

      const completeManifest = await loadPostgresMigrationManifest(
        migrationsDirectory,
        {
          migrationRole,
          applicationRole: API_ROLE,
          schemaName: "core002"
        }
      );

      b4Migrations = completeManifest.filter(
        (migration) =>
          migration.id === "00000003" ||
          migration.id === "00000004" ||
          migration.id === "00000011"
      );

      const expectedMigrationIds = [
        "00000003",
        "00000004",
        "00000011"
      ];

      if (
        JSON.stringify(b4Migrations.map(({ id }) => id)) !==
        JSON.stringify(expectedMigrationIds)
      ) {
        throw new Error(
          "The canonical B4 infrastructure migration manifest is incomplete or out of order."
        );
      }

      migrationRunner = new PostgresMigrationRunner(
        migrationPool as unknown as PostgresDriverPool,
        {
          migrationRole,
          applicationRole: API_ROLE
        }
      );

      const firstMigrationReport =
        await migrationRunner.migrate(b4Migrations);

      initialMigrationAppliedCount =
        firstMigrationReport.appliedCount;

      initialMigrationLatestId =
        firstMigrationReport.latestMigrationId;

      if (
        initialMigrationAppliedCount !== 3 ||
        initialMigrationLatestId !== "00000011"
      ) {
        throw new Error(
          "The canonical B4 session, audit and tenant-write-guard migrations were not fully applied."
        );
      }

      /*
       * Re-verify the real target role after api_sessions exists.
       * This now checks the session table's FORCE RLS and tenant policy too.
       */

      await runtime.postgres.verifyRuntimeRoleSafety();
      await runtime.verifyReadiness();
    }, testTimeoutMs);

    afterAll(async () => {
      const cleanupErrors: Error[] = [];

      const attemptCleanup = async (
        operation: string,
        cleanup: () => Promise<unknown>
      ): Promise<void> => {
        try {
          await cleanup();
        } catch (error) {
          cleanupErrors.push(
            new Error(
              `B4 integration fixture cleanup failed: ${operation}.`,
              { cause: error }
            )
          );
        }
      };

      await attemptCleanup(
        "production persistence runtime",
        async () => {
          await runtime?.close();
        }
      );

      await attemptCleanup(
        "migration pool",
        async () => {
          await migrationPool?.end();
        }
      );

      const activeAdminPool = adminPool;

      if (activeAdminPool !== undefined) {
        if (createdTenantSchema) {
          await attemptCleanup(
            "temporary tenant schema",
            async () => {
              await activeAdminPool.query(
                `DROP SCHEMA IF EXISTS ${quoteIdentifier(tenantSchema)} CASCADE`
              );
            }
          );
        }

        if (createdInfraSchema) {
          await attemptCleanup(
            "infrastructure schema",
            async () => {
              await activeAdminPool.query(
                "DROP SCHEMA IF EXISTS reos_infra CASCADE"

                    );
            }
          );
        }

        if (createdMigrationRole) {
          await attemptCleanup(
            "temporary migration role",
            async () => {
              await activeAdminPool.query(
                `DROP ROLE IF EXISTS ${quoteIdentifier(migrationRole)}`
              );
            }
          );
        }

        await attemptCleanup(
          "administrative PostgreSQL pool",
          async () => {
            await activeAdminPool.end();
          }
        );
      }

      if (cleanupErrors.length > 0) {
        throw new AggregateError(
          cleanupErrors,
          "B4 production persistence integration fixture cleanup failed."
        );
      }
    }, testTimeoutMs);

    it(
      "applies the actual B4 migrations deterministically and idempotently",
      async () => {
        if (
          adminPool === undefined ||
          migrationRunner === undefined
        ) {
          throw new Error(
            "The B4 migration integration fixture was not initialized."
          );
        }

        expect(initialMigrationAppliedCount).toBe(3);
        expect(initialMigrationLatestId).toBe("00000011");

        const latestMigration =
          b4Migrations[b4Migrations.length - 1];

        if (latestMigration === undefined) {
          throw new Error(
            "The canonical B4 infrastructure migration manifest is empty."
          );
        }

        const secondReport =
          await migrationRunner.migrate(b4Migrations);

        expect(secondReport.appliedCount).toBe(0);
        expect(secondReport.latestMigrationId).toBe("00000011");
        expect(secondReport.latestChecksum).toBe(
          latestMigration.checksum
        );

        const ledger = await adminPool.query(`
          SELECT migration_id, migration_name, checksum
          FROM reos_infra.schema_migrations
          ORDER BY migration_id ASC
        `);

        expect(ledger.rows).toHaveLength(3);

        expect(
          ledger.rows.map((row) => row.migration_id)
        ).toEqual([
          "00000003",
          "00000004",
          "00000011"
        ]);

        expect(
          ledger.rows.map((row) => row.checksum)
        ).toEqual(
          b4Migrations.map((migration) => migration.checksum)
        );

        const owners = await adminPool.query(`
          SELECT
            relation.relname AS relation_name,
            pg_get_userbyid(relation.relowner) AS owner_name
          FROM pg_class AS relation
          JOIN pg_namespace AS namespace
            ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'reos_infra'
            AND relation.relname IN (
              'api_sessions',
              'security_audit_events',
              'schema_migrations'
            )
          ORDER BY relation.relname
        `);

        expect(owners.rows).toHaveLength(3);

        for (const row of owners.rows) {
          expect(row.owner_name).toBe(migrationRole);
        }

        /*
         * The B4 infrastructure fixture must not silently create CORE
         * business schemas or become another domain persistence authority.
         */

        const domainSchemaProbe = await adminPool.query(`
          SELECT
            to_regclass('core002.events') IS NOT NULL AS core002_events_exist
        `);

        expect(
          domainSchemaProbe.rows[0]?.core002_events_exist
        ).toBe(false);

        const apiProbePool = new pgModule.Pool({
          connectionString: applicationUrl,
          max: 1
        });

        try {
          await expect(
            apiProbePool.query(
              "SELECT migration_id FROM reos_infra.schema_migrations"
            )
          ).rejects.toMatchObject({
            code: "42501"
          });
        } finally {
          await apiProbePool.end();
        }
      },
      testTimeoutMs
    );

    it(
      "enforces tenant isolation through the real Node.js PostgreSQL transaction owner",
      async () => {
        if (runtime === undefined) {
          throw new Error(
            "The real PostgreSQL runtime was not initialized."
          );
        }

        const inserted = await runtime.postgres.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) => transaction.query(
            `INSERT INTO ${tenantTable()} (
               record_id,
               tenant_id,
               payload
             )
             VALUES ($1, $2, $3)
             RETURNING record_id`,
            [
              randomUUID(),
              tenantA,
              "tenant-a"
            ]
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
              `INSERT INTO ${tenantTable()} (
                 record_id,
                 tenant_id,
                 payload
               )
               VALUES ($1, $2, $3)`,
              [
                randomUUID(),
                tenantB,
                "cross-tenant-forbidden"
              ]
            )
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

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

        /*
         * The pool maximum is one connection.
         * The second tenant transaction proves tenant context is
         * transaction-local rather than inherited from the previous request.
         */

        await runtime.postgres.verifyRuntimeRoleSafety();
      },
      testTimeoutMs
    );

    it(
      "persists durable sessions, binds them to trusted context and enforces revocation",
      async () => {
        if (
          adminPool === undefined ||
          runtime === undefined
        ) {
          throw new Error(
            "The durable PostgreSQL session fixture was not initialized."
          );
        }

        const now = Math.floor(Date.now() / 1_000);

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

        const principal: VerifiedExternalPrincipal = {
          issuer: "https://issuer.example.test/",
          subject: `b4-session-${suffix}`,
          audiences: ["homio-api"],
                    clientId: "homio-backend-ci",
          tokenId: randomUUID(),
          issuedAtEpochSeconds: now - 5,
          expiresAtEpochSeconds: now + 3_600
        };

        const sessionId = await runtime.sessions.establishSession({
          principal,
          context
        });

        expect(sessionId).toMatch(
          /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
        );

        /*
         * A new adapter instance reads the persisted session.
         * This is not an in-memory session registry.
         */

        const reloadedStore = new PostgresSessionStore(
          runtime.postgres
        );

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context
          })
        ).resolves.toBe(true);

        const persisted = await adminPool.query(
          `SELECT
             tenant_id,
             account_id,
             identity_id,
             authentication_epoch,
             issuer_digest,
             token_id_digest,
             revoked_at
           FROM reos_infra.api_sessions
           WHERE session_id = $1`,
          [sessionId]
        );

        expect(persisted.rows).toHaveLength(1);

        expect(persisted.rows[0]).toMatchObject({
          tenant_id: tenantA,
          account_id: context.accountId,
          identity_id: context.identityId,
          issuer_digest: sha256(principal.issuer),
          token_id_digest: sha256(principal.tokenId),
          revoked_at: null
        });

        /*
         * Raw issuer and token identifiers are never stored in the session row.
         */

        expect(persisted.rows[0]?.issuer_digest).not.toBe(
          principal.issuer
        );

        expect(persisted.rows[0]?.token_id_digest).not.toBe(
          principal.tokenId
        );

        /*
         * Changing the trusted authentication epoch invalidates the old
         * session binding without deleting durable session history.
         */

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context: {
              ...context,
              authenticationEpoch: 2
            }
          })
        ).resolves.toBe(false);

        /*
         * Cross-tenant context cannot resolve the session.
         */

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context: {
              ...context,
              tenantId: tenantB
            }
          })
        ).resolves.toBe(false);

        /*
         * Session identity fields are immutable after creation.
         */

        await expect(
          runtime.postgres.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) => transaction.query(
              `UPDATE reos_infra.api_sessions
                  SET account_id = $2
                WHERE session_id = $1
                RETURNING session_id`,
              [
                sessionId,
                randomUUID()
              ]
            )
          )
        ).rejects.toMatchObject({
          code: "55000"
        });

        /*
         * Token-specific revocation is durable and idempotent.
         */

        await expect(
          reloadedStore.revokeSession({
            principal,
            context,
            reasonCode: "B4_CI_LOGOUT"
          })
        ).resolves.toBe(true);

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context
          })
        ).resolves.toBe(false);

        await expect(
          reloadedStore.revokeSession({
            principal,
            context,
            reasonCode: "B4_CI_LOGOUT"
          })
        ).resolves.toBe(true);

        /*
         * Account-level revocation invalidates all active sessions for
         * the same trusted account context.
         */

        const secondPrincipal: VerifiedExternalPrincipal = {
          ...principal,
          tokenId: randomUUID()
        };

        await reloadedStore.establishSession({
          principal: secondPrincipal,
          context
        });

        await expect(
          reloadedStore.isSessionActive({
            principal: secondPrincipal,
            context
          })
        ).resolves.toBe(true);

        await expect(
          reloadedStore.revokeAccountSessions({
            context,
            reasonCode: "B4_CI_ACCOUNT_REVOCATION"
          })
        ).resolves.toBe(1);

        await expect(
          reloadedStore.isSessionActive({
            principal: secondPrincipal,
            context
          })
        ).resolves.toBe(false);

        /*
         * Expired verified credentials cannot establish new durable sessions.
         */

        const expiredPrincipal: VerifiedExternalPrincipal = {
          ...principal,
          tokenId: randomUUID(),
          issuedAtEpochSeconds: now - 3_600,
          expiresAtEpochSeconds: now - 1
        };

        await expect(
          reloadedStore.establishSession({
            principal: expiredPrincipal,
            context
          })
        ).rejects.toThrow(
          "An expired verified token cannot establish a session."
        );
      },
      testTimeoutMs
    );
        it(
      "persists minimized append-only security audit events with least-privilege access",
      async () => {
        if (
          adminPool === undefined ||
          runtime === undefined
        ) {
          throw new Error(
            "The PostgreSQL security audit fixture was not initialized."
          );
        }

        const requestId = randomUUID();

        const event: SecurityAuditEvent = {
          eventType: "API_ACCESS_DENIED",
          requestId,
          occurredAt: new Date().toISOString(),
          reasonCode: "B4_CI_AUDIT",
          operation: "inventory.read",
          actorIdentityId: randomUUID(),
          tenantId: tenantA
        };

        await runtime.securityAudit.record(event);

        const stored = await adminPool.query(
          `SELECT
             event_type,
             request_id,
             occurred_at,
             reason_code,
             operation,
             actor_identity_reference,
             tenant_reference
           FROM reos_infra.security_audit_events
           WHERE request_id = $1`,
          [requestId]
        );

        expect(stored.rows).toHaveLength(1);

        expect(stored.rows[0]).toMatchObject({
          event_type: "API_ACCESS_DENIED",
          request_id: requestId,
          reason_code: "B4_CI_AUDIT",
          operation: "inventory.read",
          actor_identity_reference: event.actorIdentityId,
          tenant_reference: tenantA
        });

        /*
         * The application role may append only through the approved
         * SECURITY DEFINER function; direct table reads and mutations
         * remain unavailable to the application role.
         */

        const apiProbePool = new pgModule.Pool({
          connectionString: applicationUrl,
          max: 1
        });

        try {
          await expect(
            apiProbePool.query(
              `SELECT event_id
                 FROM reos_infra.security_audit_events
                WHERE request_id = $1`,
              [requestId]
            )
          ).rejects.toMatchObject({
            code: "42501"
          });

          await expect(
            apiProbePool.query(
              `UPDATE reos_infra.security_audit_events
                  SET reason_code = 'MUTATED'
                WHERE request_id = $1`,
              [requestId]
            )
          ).rejects.toMatchObject({
            code: "42501"
          });

          await expect(
            apiProbePool.query(
              `DELETE FROM reos_infra.security_audit_events
                WHERE request_id = $1`,
              [requestId]
            )
          ).rejects.toMatchObject({
            code: "42501"
          });
                        [requestId]
            )
          ).rejects.toMatchObject({
            code: "42501"
          });
        } finally {
          await apiProbePool.end();
        }

        /*
         * The append-only database trigger independently rejects mutation,
         * even when the operation is attempted by the administrative owner.
         */

        const adminClient = await adminPool.connect();

        try {
          await adminClient.query("BEGIN");
          await adminClient.query("SAVEPOINT audit_mutation");

          await expect(
            adminClient.query(
              `UPDATE reos_infra.security_audit_events
                  SET reason_code = 'MUTATED'
                WHERE request_id = $1`,
              [requestId]
            )
          ).rejects.toMatchObject({
            code: "55000"
          });

          await adminClient.query(
            "ROLLBACK TO SAVEPOINT audit_mutation"
          );

          await adminClient.query("ROLLBACK");
        } finally {
          await adminClient.query("ROLLBACK").catch(() => undefined);
          adminClient.release();
        }

        /*
         * Verify the physical audit record does not expose request bodies,
         * bearer tokens, credential values or authentication secrets.
         */

        const columns = await adminPool.query(`
          SELECT column_name
          FROM information_schema.columns
          WHERE table_schema = 'reos_infra'
            AND table_name = 'security_audit_events'
          ORDER BY ordinal_position
        `);

        expect(
          columns.rows.map((row) => row.column_name)
        ).toEqual([
          "event_id",
          "event_type",
          "request_id",
          "occurred_at",
          "reason_code",
          "operation",
          "actor_identity_reference",
          "tenant_reference"
        ]);
      },
      testTimeoutMs
    );

    it(
      "enforces shared Redis rate limits across independent clients",
      async () => {
        if (runtime === undefined || !redisUrl) {
          throw new Error(
            "The real Redis persistence fixture was not initialized."
          );
        }

        /*
         * This test-owned client must never outlive this test. In particular,
         * it must be closed before the following test deliberately restarts
         * the disposable Redis service.
         */
        const secondaryRedis = redisModule.createClient({
          url: redisUrl
        });

        let secondaryRedisConnected = false;
        let secondaryRedisError: unknown;
        let operationFailed = false;
        let operationError: unknown;
        let cleanupFailed = false;
        let cleanupError: unknown;

        /*
         * Node Redis requires an error listener. Capture the event so it is
         * reported as a test failure rather than an unhandled process error.
         */
        secondaryRedis.on("error", (error) => {
          secondaryRedisError = error;
        });

        try {
          await secondaryRedis.connect();
          secondaryRedisConnected = true;

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

          if (secondaryRedisError !== undefined) {
            throw new Error(
              "The secondary Redis client emitted an error during the shared rate-limit integration test.",
              { cause: secondaryRedisError }
            );
          }

          await runtime.verifyReadiness();

          expect(runtime.isHealthy()).toBe(true);
        } catch (error) {
          operationFailed = true;
          operationError = error;
        }

        /*
         * Close while Redis is still available. If connection setup did not
         * finish, destroy the client directly instead of sending QUIT over
         * an unestablished or failed connection.
         */
        try {
          if (secondaryRedisConnected && secondaryRedis.isOpen) {
            await secondaryRedis.quit();
          } else {
            secondaryRedis.destroy();
          }

          expect(secondaryRedis.isOpen).toBe(false);
        } catch (error) {
          secondaryRedis.destroy();
          cleanupFailed = true;
          cleanupError = error;
        }

        if (operationFailed && cleanupFailed) {
          throw new AggregateError(
            [operationError, cleanupError],
            "The shared Redis rate-limit test failed and its secondary client also failed to close."
          );
        }

        if (operationFailed) {
          throw operationError;
        }

        if (cleanupFailed) {
          throw cleanupError;
        }
      },
      testTimeoutMs
    );

    /*
     * This destructive service-restart probe is restricted to the disposable
     * Redis container owned by the GitHub Actions job.
     */
    it.skipIf(process.env.GITHUB_ACTIONS !== "true")(
      "fails readiness during Redis service loss and recovers the production runtime after Redis restart",
      async () => {
        const activeRuntime = runtime;

        if (activeRuntime === undefined || !redisUrl || adminPool === undefined) {
          throw new Error(
            "The real PostgreSQL and Redis production runtime was not initialized."
          );
        }

        const endpoint = new URL(redisUrl);
        const loopbackHosts = new Set([
          "127.0.0.1",
          "localhost",
          "::1"
        ]);

        if (!loopbackHosts.has(endpoint.hostname)) {
          throw new Error(
            "The Redis restart probe is restricted to the isolated loopback CI service."
          );
        }

        const publishedPort = Number(endpoint.port || "6379");

        if (
          !Number.isInteger(publishedPort) ||
          publishedPort < 1 ||
          publishedPort > 65_535
        ) {
          throw new Error(
            "The Redis integration endpoint has an invalid published port."
          );
        }

        const runDocker = (
          args: readonly string[],
          timeoutMs = 15_000
        ): string => {
          try {
            return execFileSync("docker", [...args], {
              encoding: "utf8",
              stdio: ["ignore", "pipe", "pipe"],
              timeout: timeoutMs,
              maxBuffer: 1024 * 1024
            }).trim();
          } catch (error) {
            throw new Error(
              "The disposable Redis CI container operation failed.",
              { cause: error }
            );
          }
        };

        const pause = (milliseconds: number): Promise<void> =>
          new Promise((resolve) => setTimeout(resolve, milliseconds));

        let redisContainerId: string | undefined;
        let operationError: unknown;
        const cleanupErrors: Error[] = [];

        const waitForRedisServer = async (): Promise<void> => {
          if (redisContainerId === undefined) {
            throw new Error(
              "The Redis CI container identity was not established."
            );
          }

          const deadline = Date.now() + 30_000;
          let lastError: unknown;

          while (Date.now() < deadline) {
            try {
              const response = runDocker([
                "exec",
                redisContainerId,
                "redis-cli",
                "--raw",
                "PING"
              ]);

              if (response === "PONG") {
                return;
              }

              lastError = new Error(
                "The Redis service returned an unexpected readiness response."
              );
            } catch (error) {
              lastError = error;
            }

            await pause(250);
          }

          throw new Error(
            "Redis 8.0.3 did not become ready after the container restart.",
            { cause: lastError }
          );
        };

        const waitForRuntimeReadiness = async (): Promise<void> => {
          const deadline = Date.now() + 30_000;
          let lastError: unknown;

          while (Date.now() < deadline) {
            try {
              await activeRuntime.verifyReadiness();

              if (activeRuntime.isHealthy()) {
                return;
              }

              lastError = new Error(
                "The production persistence runtime remained unhealthy after readiness verification."
              );
            } catch (error) {
              lastError = error;
            }

            await pause(250);
          }

          throw new Error(
            "The production persistence runtime did not recover after Redis restart.",
            { cause: lastError }
          );
        };

        try {
          const containerIds = runDocker([
            "ps",
            "--filter",
            "publish=" + publishedPort,
            "--format",
            "{{.ID}}"
          ])
            .split(/\r?\n/)
            .map((value) => value.trim())
            .filter((value) => value.length > 0);

          if (containerIds.length !== 1 || containerIds[0] === undefined) {
            throw new Error(
              "The Redis restart probe requires exactly one Docker container published on the configured Redis port."
            );
          }

          redisContainerId = containerIds[0];

          const image = runDocker([
            "inspect",
            "--format",
            "{{.Config.Image}}",
            redisContainerId
          ]);

          if (!/(^|\/)redis:8\.0\.3(?:$|[-@])/.test(image)) {
            throw new Error(
              "The selected Redis CI container does not use the approved redis:8.0.3 image."
            );
          }

          await activeRuntime.verifyReadiness();
          expect(activeRuntime.isHealthy()).toBe(true);
          expect(await activeRuntime.redis.ping()).toBe("PONG");

          /*
           * Stop only the loopback-published Redis 8.0.3 service container
           * owned by this GitHub Actions job. PostgreSQL remains untouched.
           */
          runDocker([
            "stop",
            "--time",
            "2",
            redisContainerId
          ]);

          expect(
            runDocker([
              "inspect",
              "--format",
              "{{.State.Running}}",
              redisContainerId
            ])
          ).toBe("false");

          /*
           * The mandatory Redis dependency is unavailable, so the existing
           * production readiness owner must fail closed. PostgreSQL is probed
           * independently through the same production PostgresRuntime.
           */
          await expect(
            activeRuntime.verifyReadiness()
          ).rejects.toMatchObject({
            name: "ProductionPersistenceUnavailableError"
          });

          expect(activeRuntime.isHealthy()).toBe(false);

          const postgresProbe = await activeRuntime.postgres.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) => transaction.query(
              "SELECT 1 AS postgres_available"
            )
          );

          expect(postgresProbe.rowCount).toBe(1);
          expect(
            Number(postgresProbe.rows[0]?.postgres_available)
          ).toBe(1);

          /*
           * Redis rate-limit counters are not durable business history.
           * This test proves dependency recovery only; it makes no claim that
           * ephemeral Redis state survives a restart.
           */
        } catch (error) {
          operationError = error;
        } finally {
          /*
           * Always restore the disposable CI service, including when an
           * assertion or readiness probe fails after the stop operation.
           */
          if (redisContainerId !== undefined) {
            try {
              const isRunning = runDocker([
                "inspect",
                "--format",
                "{{.State.Running}}",
                redisContainerId
              ]) === "true";

              if (!isRunning) {
                runDocker([
                  "start",
                  redisContainerId
                ]);
              }

              await waitForRedisServer();
              await waitForRuntimeReadiness();
            } catch (error) {
              cleanupErrors.push(
                error instanceof Error
                  ? error
                  : new Error(
                      "Redis CI service cleanup failed.",
                      { cause: error }
                    )
              );
            }
          }
        }

        if (operationError !== undefined && cleanupErrors.length > 0) {
          throw new AggregateError(
            [operationError, ...cleanupErrors],
            "Redis outage verification failed and the CI dependency cleanup also failed."
          );
        }

        if (operationError !== undefined) {
          throw operationError;
        }

        if (cleanupErrors.length > 0) {
          throw new AggregateError(
            cleanupErrors,
            "The Redis CI dependency did not recover cleanly."
          );
        }

        expect(activeRuntime.isHealthy()).toBe(true);

        /*
         * Exercise the real production shutdown path after successful
         * dependency recovery. Repeated close must remain idempotent.
         */
        await activeRuntime.close();
        await activeRuntime.close();

        expect(activeRuntime.redis.isOpen).toBe(false);
        expect(activeRuntime.isHealthy()).toBe(false);

        await expect(
          activeRuntime.verifyReadiness()
        ).rejects.toMatchObject({
          name: "ProductionPersistenceUnavailableError"
        });

        const remainingApplicationSessions = await adminPool.query(
          "SELECT count(*)::integer AS count " +
          "FROM pg_stat_activity " +
          "WHERE usename = $1 AND datname = current_database()",
          [API_ROLE]
        );

        expect(
          Number(remainingApplicationSessions.rows[0]?.count)
        ).toBe(0);
      },
      60_000
    );
  }
);

                
