import { describe, expect, it, vi } from "vitest";

import {
  POSTGRES_MIGRATION_BOOTSTRAP_SQL,
  POSTGRES_MIGRATION_CREATE_SCHEMA_SQL,
  POSTGRES_MIGRATION_HISTORY_SQL,
  POSTGRES_MIGRATION_INSERT_SQL,
  POSTGRES_MIGRATION_LOCK_SQL,
  POSTGRES_MIGRATION_RUNTIME_SQL,
  POSTGRES_MIGRATION_UNLOCK_SQL,
  POSTGRES_MIGRATION_VERIFY_SQL,
  PostgresMigrationError,
  PostgresMigrationRunner,
  postgresMigrationChecksum,
  validatePostgresMigrationManifest
} from "../../src/persistence/postgres-migrations.js";
import type {
  PostgresMigration,
  PostgresMigrationRunnerOptions
} from "../../src/persistence/postgres-migrations.js";
import type {
  PostgresDriverClient,
  PostgresDriverPool,
  PostgresQueryResult
} from "../../src/persistence/postgres.js";

interface StoredMigration {
  readonly migration_id: string;
  readonly migration_name: string;
  readonly checksum: string;
}

interface QueryCall {
  readonly sql: string;
  readonly values: readonly unknown[] | undefined;
}

interface FixtureOptions {
  readonly applied?: readonly StoredMigration[];
  readonly lockAcquired?: boolean;
  readonly unlockResult?: boolean;
  readonly failOnSql?: string;
  readonly failRollback?: boolean;
  readonly failCommit?: boolean;
  readonly connectFailure?: Error;
  readonly runtimeRow?: unknown;
  readonly metadataRow?: unknown;
}

function makePool(options: FixtureOptions = {}): {
  readonly pool: PostgresDriverPool;
  readonly calls: QueryCall[];
  readonly history: StoredMigration[];
  readonly releaseErrors: (Error | boolean | undefined)[];
  readonly connect: ReturnType<typeof vi.fn>;
} {
  const calls: QueryCall[] = [];
  const history = [...(options.applied ?? [])];
  const releaseErrors: (Error | boolean | undefined)[] = [];

  const client: PostgresDriverClient = {
    query: vi.fn(async (
      sql: string,
      values?: unknown[]
    ): Promise<PostgresQueryResult> => {
      calls.push({
        sql,
        values: values === undefined ? undefined : [...values]
      });

      if (
        sql === options.failOnSql ||
        (sql === "ROLLBACK" && options.failRollback) ||
        (sql === "COMMIT" && options.failCommit)
      ) {
        throw new Error(`query failed: ${sql}`);
      }

      if (sql === POSTGRES_MIGRATION_RUNTIME_SQL) {
        return {
          rows: [options.runtimeRow ?? {
            session_user: "homio_migrator",
            current_user: "homio_migrator",
            server_version_num: 180004
          }],
          rowCount: 1
        };
      }

      if (sql === POSTGRES_MIGRATION_LOCK_SQL) {
        return {
          rows: [{ acquired: options.lockAcquired ?? true }],
          rowCount: 1
        };
      }

      if (sql === POSTGRES_MIGRATION_UNLOCK_SQL) {
        return {
          rows: [{ unlocked: options.unlockResult ?? true }],
          rowCount: 1
        };
      }

      if (sql === POSTGRES_MIGRATION_VERIFY_SQL) {
        return {
          rows: [options.metadataRow ?? {
            schema_owner: "homio_migrator",
            table_owner: "homio_migrator",
            columns: [
              "migration_id:text:NO",
              "migration_name:text:NO",
              "checksum:text:NO",
              "applied_at:timestamp with time zone:NO"
            ],
            primary_key: "PRIMARY KEY (migration_id)",
            unique_key: "UNIQUE (migration_name)",
            check_constraint_count: 3,
            row_security_enabled: false
          }],
          rowCount: 1
        };
      }

      if (sql === POSTGRES_MIGRATION_HISTORY_SQL) {
        return {
          rows: [...history],
          rowCount: history.length
        };
      }

      if (sql === POSTGRES_MIGRATION_INSERT_SQL) {
        const [migrationId, migrationName, checksum] = values ?? [];
        history.push({
          migration_id: String(migrationId),
          migration_name: String(migrationName),
          checksum: String(checksum)
        });
        return { rows: [], rowCount: 1 };
      }

      return { rows: [], rowCount: 0 };
    }),
    release: vi.fn((error?: Error | boolean) => {
      releaseErrors.push(error);
    })
  };

  const connect = vi.fn(async () => {
    if (options.connectFailure !== undefined) {
      throw options.connectFailure;
    }

    return client;
  });

  return {
    pool: { connect, end: vi.fn(async () => undefined) },
    calls,
    history,
    releaseErrors,
    connect
  };
}

const VALID_RUNNER_OPTIONS: PostgresMigrationRunnerOptions = {
  migrationRole: "homio_migrator",
  applicationRole: "homio_api"
};

const MIGRATIONS: readonly PostgresMigration[] = [
  {
    id: "00000001",
    name: "bootstrap-domain-schema",
    sql: "CREATE TABLE core_test_one (id UUID PRIMARY KEY);"
  },
  {
    id: "00000002",
    name: "add-domain-index",
    sql: "CREATE INDEX core_test_one_id_idx ON core_test_one (id);"
  }
];

function historyFor(
  migration: PostgresMigration
): StoredMigration {
  return {
    migration_id: migration.id,
    migration_name: migration.name,
    checksum: postgresMigrationChecksum(migration.sql)
  };
}

describe("immutable PostgreSQL migration runner", () => {
  it("validates and freezes a strictly ordered manifest with exact SQL checksums", () => {
    const manifest = validatePostgresMigrationManifest(MIGRATIONS);

    expect(Object.isFrozen(manifest)).toBe(true);
    expect(Object.isFrozen(manifest[0])).toBe(true);
    expect(manifest.map((item) => item.id)).toEqual([
      "00000001",
      "00000002"
    ]);
    expect(manifest[0]?.checksum).toBe(
      postgresMigrationChecksum(MIGRATIONS[0]?.sql ?? "")
    );
  });

  it("requires an explicitly separate migration role and API role", () => {
    const fixture = makePool();

    expect(() => new PostgresMigrationRunner(fixture.pool, {
      migrationRole: "homio_api",
      applicationRole: "homio_api"
    })).toThrow("distinct from the API role");
  });

  it("refuses a connection authenticated as the API role before attempting DDL", async () => {
    const fixture = makePool({
      runtimeRow: {
        session_user: "homio_api",
        current_user: "homio_api",
        server_version_num: 180004
      }
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_ROLE_MISMATCH"
    });
    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_MIGRATION_RUNTIME_SQL
    ]);
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("refuses PostgreSQL versions older than the approved 18.4 minimum", async () => {
    const fixture = makePool({
      runtimeRow: {
        session_user: "homio_migrator",
        current_user: "homio_migrator",
        server_version_num: 180003
      }
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_SERVER_VERSION_UNSUPPORTED"
    });
    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_MIGRATION_RUNTIME_SQL
    ]);
  });

  it("rejects an empty, unsorted, duplicate or malformed manifest before connecting", async () => {
    const fixture = makePool();
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    expect(() => validatePostgresMigrationManifest([])).toThrow(
      PostgresMigrationError
    );
    expect(() => validatePostgresMigrationManifest([
      MIGRATIONS[1] as PostgresMigration,
      MIGRATIONS[0] as PostgresMigration
    ])).toThrow("strictly increasing ID order");
    expect(() => validatePostgresMigrationManifest([
      MIGRATIONS[0] as PostgresMigration,
      { ...MIGRATIONS[0] as PostgresMigration, name: "second-name" }
    ])).toThrow("must both be unique");
    expect(() => validatePostgresMigrationManifest([
      { id: "1", name: "bad-name", sql: " " }
    ])).toThrow("invalid ID, name or empty SQL body");

    await expect(runner.migrate([])).rejects.toMatchObject({
      code: "INVALID_MANIFEST"
    });
    expect(fixture.connect).not.toHaveBeenCalled();
  });

  it("applies ordered migrations and writes each checksum in the same transaction", async () => {
    const fixture = makePool();
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    const report = await runner.migrate(MIGRATIONS);

    expect(report).toEqual({
      appliedCount: 2,
      latestMigrationId: "00000002",
      latestChecksum: postgresMigrationChecksum(MIGRATIONS[1]?.sql ?? "")
    });
    expect(fixture.history).toEqual(MIGRATIONS.map(historyFor));
    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_MIGRATION_RUNTIME_SQL,
      POSTGRES_MIGRATION_LOCK_SQL,
      POSTGRES_MIGRATION_CREATE_SCHEMA_SQL,
      POSTGRES_MIGRATION_BOOTSTRAP_SQL,
      POSTGRES_MIGRATION_VERIFY_SQL,
      POSTGRES_MIGRATION_HISTORY_SQL,
      "BEGIN",
      MIGRATIONS[0]?.sql,
      POSTGRES_MIGRATION_INSERT_SQL,
      "COMMIT",
      "BEGIN",
      MIGRATIONS[1]?.sql,
      POSTGRES_MIGRATION_INSERT_SQL,
      "COMMIT",
      POSTGRES_MIGRATION_UNLOCK_SQL
    ]);
    expect(fixture.calls[1]?.values).toEqual([0x484f4d49, 1]);
    expect(fixture.calls[8]?.values).toEqual([
      "00000001",
      "bootstrap-domain-schema",
      postgresMigrationChecksum(MIGRATIONS[0]?.sql ?? "")
    ]);
    expect(fixture.releaseErrors).toEqual([undefined]);
  });

  it("does not reapply an already verified manifest prefix", async () => {
    const fixture = makePool({
      applied: MIGRATIONS.map(historyFor)
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    const report = await runner.migrate(MIGRATIONS);

    expect(report.appliedCount).toBe(0);
    expect(fixture.calls.some((call) => call.sql === MIGRATIONS[0]?.sql)).toBe(false);
    expect(fixture.calls.some((call) => call.sql === MIGRATIONS[1]?.sql)).toBe(false);
    expect(fixture.releaseErrors).toEqual([undefined]);
  });

  it("rejects changed applied SQL, renamed migrations and removed history", async () => {
    const changed: readonly PostgresMigration[] = [
      { ...MIGRATIONS[0] as PostgresMigration, sql: "SELECT 1;" },
      MIGRATIONS[1] as PostgresMigration
    ];
    const changedFixture = makePool({ applied: [historyFor(MIGRATIONS[0] as PostgresMigration)] });
    const changedRunner = new PostgresMigrationRunner(changedFixture.pool, VALID_RUNNER_OPTIONS);

    await expect(changedRunner.migrate(changed)).rejects.toMatchObject({
      code: "MIGRATION_HISTORY_DRIFT"
    });
    expect(changedFixture.calls.some((call) => call.sql === "SELECT 1;")).toBe(false);

    const removedFixture = makePool({
      applied: [
        historyFor(MIGRATIONS[0] as PostgresMigration),
        historyFor(MIGRATIONS[1] as PostgresMigration)
      ]
    });
    const removedRunner = new PostgresMigrationRunner(removedFixture.pool, VALID_RUNNER_OPTIONS);

    await expect(removedRunner.migrate([MIGRATIONS[0] as PostgresMigration])).rejects.toMatchObject({
      code: "MIGRATION_HISTORY_DRIFT"
    });
  });

  it("rejects a non-prefix history rather than applying over a migration gap", async () => {
    const fixture = makePool({
      applied: [
        historyFor(MIGRATIONS[0] as PostgresMigration),
        {
          ...historyFor(MIGRATIONS[1] as PostgresMigration),
          migration_id: "00000003"
        }
      ]
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_HISTORY_DRIFT"
    });
    expect(fixture.calls.some((call) => call.sql === MIGRATIONS[1]?.sql)).toBe(false);
  });

  it("fails fast when another runner owns the advisory lock", async () => {
    const fixture = makePool({ lockAcquired: false });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_LOCK_UNAVAILABLE"
    });
    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_MIGRATION_RUNTIME_SQL,
      POSTGRES_MIGRATION_LOCK_SQL
    ]);
    expect(fixture.releaseErrors).toEqual([undefined]);
  });

  it("destroys a connection when the advisory-lock response is lost", async () => {
    const fixture = makePool({ failOnSql: POSTGRES_MIGRATION_LOCK_SQL });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_LOCK_UNAVAILABLE"
    });
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("rolls back a failed migration and leaves the history unchanged", async () => {
    const failingMigration: readonly PostgresMigration[] = [
      { id: "00000001", name: "failing-ddl", sql: "SELECT fail_migration();" }
    ];
    const fixture = makePool({ failOnSql: "SELECT fail_migration();" });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(failingMigration)).rejects.toMatchObject({
      code: "MIGRATION_EXECUTION_FAILED",
      migrationId: "00000001"
    });
    expect(fixture.calls.map((call) => call.sql)).toContain("ROLLBACK");
    expect(fixture.history).toEqual([]);
    expect(fixture.releaseErrors).toEqual([undefined]);
  });

  it("destroys a connection if rollback fails while preserving both failures", async () => {
    const fixture = makePool({
      failOnSql: "SELECT fail_migration();",
      failRollback: true
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate([
      { id: "00000001", name: "failing-ddl", sql: "SELECT fail_migration();" }
    ])).rejects.toMatchObject({
      code: "MIGRATION_ROLLBACK_FAILED",
      migrationId: "00000001"
    });
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("never retries or rolls back an ambiguous COMMIT result", async () => {
    const fixture = makePool({ failCommit: true });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_OUTCOME_UNKNOWN",
      migrationId: "00000001"
    });
    expect(fixture.calls.map((call) => call.sql)).toContain("COMMIT");
    expect(fixture.calls.map((call) => call.sql)).not.toContain("ROLLBACK");
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("destroys the connection if the advisory lock cannot be released", async () => {
    const fixture = makePool({ unlockResult: false });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_LOCK_RELEASE_FAILED"
    });
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("fails closed when the database migration history is malformed", async () => {
    const fixture = makePool({
      applied: [{
        migration_id: "not-a-version",
        migration_name: "bad-history",
        checksum: "not-a-checksum"
      }]
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_HISTORY_CORRUPT"
    });
  });

  it("rejects duplicate migration names in persisted history", async () => {
    const fixture = makePool({
      applied: [
        historyFor(MIGRATIONS[0] as PostgresMigration),
        {
          ...historyFor(MIGRATIONS[1] as PostgresMigration),
          migration_id: "00000003",
          migration_name: MIGRATIONS[0]?.name ?? "duplicate-name"
        }
      ]
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_HISTORY_CORRUPT"
    });
    expect(fixture.calls.some((call) => call.sql === MIGRATIONS[0]?.sql)).toBe(false);
  });

  it("refuses a pre-existing migration ledger with an unapproved shape or owner", async () => {
    const fixture = makePool({
      metadataRow: {
        schema_owner: "database_admin",
        table_owner: "homio_api",
        columns: ["migration_id:text:NO"],
        primary_key: "PRIMARY KEY (migration_id)",
        unique_key: null,
        check_constraint_count: 0,
        row_security_enabled: false
      }
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_BOOTSTRAP_FAILED"
    });
    expect(fixture.calls.some((call) => call.sql === POSTGRES_MIGRATION_HISTORY_SQL)).toBe(false);
  });

  it("destroys a connection when migration metadata bootstrap fails", async () => {
    const fixture = makePool({
      failOnSql: POSTGRES_MIGRATION_BOOTSTRAP_SQL
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_BOOTSTRAP_FAILED"
    });
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("destroys a connection when migration history cannot be read", async () => {
    const fixture = makePool({
      failOnSql: POSTGRES_MIGRATION_HISTORY_SQL
    });
    const runner = new PostgresMigrationRunner(fixture.pool, VALID_RUNNER_OPTIONS);

    await expect(runner.migrate(MIGRATIONS)).rejects.toMatchObject({
      code: "MIGRATION_HISTORY_READ_FAILED"
    });
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });
});
