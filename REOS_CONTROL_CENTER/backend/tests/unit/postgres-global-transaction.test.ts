import { describe, expect, it, vi } from "vitest";

import {
  PostgresRuntime,
  POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
  PostgresTransactionQueryPolicyError
} from "../../src/persistence/postgres.js";

import type {
  PostgresDriverClient,
  PostgresDriverPool,
  PostgresQueryResult
} from "../../src/persistence/postgres.js";

const SAFE_ROLE_RESULT = {
  role_name: "homio_api",
  is_superuser: false,
  bypasses_row_security: false,
  owns_application_tables: false,
  tenant_table_count: 2,
  tenant_tables_force_rls: true,
  tenant_tables_have_tenant_restrictive_guard: true
};

const TENANT_SETTING_SQL =
  "SELECT set_config('app.tenant_id', $1, true) AS tenant_id";

interface QueryCall {
  readonly sql: string;
  readonly values: readonly unknown[] | undefined;
}

function makePool(options: {
  readonly failOn?: string;
} = {}): {
  readonly pool: PostgresDriverPool;
  readonly calls: QueryCall[];
  readonly connect: ReturnType<typeof vi.fn>;
  readonly release: ReturnType<typeof vi.fn>;
} {
  const calls: QueryCall[] = [];
  const release = vi.fn();

  const client: PostgresDriverClient = {
    query: vi.fn(async (
      sql: string,
      values?: unknown[]
    ): Promise<PostgresQueryResult> => {
      calls.push({
        sql,
        values: values === undefined ? undefined : [...values]
      });

      if (sql === options.failOn) {
        throw new Error(`query failed: ${sql}`);
      }

      if (sql === POSTGRES_RUNTIME_ROLE_SAFETY_SQL) {
        return {
          rows: [SAFE_ROLE_RESULT],
          rowCount: 1
        };
      }

      return {
        rows: [{ accepted: true }],
        rowCount: 1
      };
    }),
    release
  };

  const connect = vi.fn(async () => client);

  const pool: PostgresDriverPool = {
    connect,
    end: vi.fn(async () => undefined)
  };

  return {
    pool,
    calls,
    connect,
    release
  };
}

describe("PostgresRuntime global transaction boundary", () => {
  it("checks the exact application connection and clears tenant context before global work", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await runtime.withGlobalTransaction(async (transaction) => {
      expect(Object.isFrozen(transaction)).toBe(true);
      expect("tenantId" in transaction).toBe(false);

      const result = await transaction.query(
        "SELECT reos_infra.append_security_audit_event($1::uuid)",
        ["11111111-1111-4111-8111-111111111111"]
      );

      expect(result.rowCount).toBe(1);
    });

    expect(fixture.connect).toHaveBeenCalledTimes(1);

    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED",
      TENANT_SETTING_SQL,
      "SELECT reos_infra.append_security_audit_event($1::uuid)",
      "COMMIT"
    ]);

    expect(fixture.calls[2]?.values).toEqual([""]);
    expect(fixture.calls[3]?.values).toEqual([
      "11111111-1111-4111-8111-111111111111"
    ]);
    expect(fixture.release).toHaveBeenCalledWith(undefined);
  });

  it("rolls back global work when the transaction SQL policy rejects a session escape", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withGlobalTransaction(async (transaction) => {
        await transaction.query(
          "SELECT set_config('app.tenant_id', $1, true)",
          ["22222222-2222-4222-8222-222222222222"]
        );
      })
    ).rejects.toBeInstanceOf(PostgresTransactionQueryPolicyError);

    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED",
      TENANT_SETTING_SQL,
      "ROLLBACK"
    ]);

    expect(fixture.calls.map((call) => call.sql)).not.toContain("COMMIT");
  });

  it("fails closed before BEGIN when the exact connection role check fails", async () => {
    const fixture = makePool({
      failOn: POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    });
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withGlobalTransaction(async () => undefined)
    ).rejects.toMatchObject({
      name: "PostgresRuntimeRoleError",
      code: "ROLE_CHECK_UNAVAILABLE"
    });

    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    ]);

    expect(fixture.release).toHaveBeenCalledWith(expect.any(Error));
  });
});
