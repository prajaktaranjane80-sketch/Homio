import { describe, expect, it, vi } from "vitest";

import {
  PostgresRuntime,
  POSTGRES_RUNTIME_ROLE_SAFETY_SQL
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
  tenant_tables_force_rls: true
};

function makePool(roleRows: readonly unknown[]): {
  readonly pool: PostgresDriverPool;
  readonly calls: string[];
} {
  const calls: string[] = [];

  const client: PostgresDriverClient = {
    query: vi.fn(async (sql: string): Promise<PostgresQueryResult> => {
      calls.push(sql);

      if (sql === POSTGRES_RUNTIME_ROLE_SAFETY_SQL) {
        return {
          rows: roleRows,
          rowCount: roleRows.length
        };
      }

      return {
        rows: [],
        rowCount: 0
      };
    }),
    release: vi.fn()
  };

  const pool: PostgresDriverPool = {
    connect: vi.fn(async () => client),
    end: vi.fn(async () => undefined)
  };

  return { pool, calls };
}

function makeSequencedPool(
  roleRowsByConnection: readonly (readonly unknown[])[]
): {
  readonly pool: PostgresDriverPool;
  readonly callsByConnection: readonly string[][];
  readonly connect: ReturnType<typeof vi.fn>;
} {
  const callsByConnection: string[][] = [];

  const clients = roleRowsByConnection.map((roleRows) => {
    const calls: string[] = [];
    callsByConnection.push(calls);

    const client: PostgresDriverClient = {
      query: vi.fn(async (sql: string): Promise<PostgresQueryResult> => {
        calls.push(sql);

        if (sql === POSTGRES_RUNTIME_ROLE_SAFETY_SQL) {
          return {
            rows: roleRows,
            rowCount: roleRows.length
          };
        }

        return {
          rows: [],
          rowCount: 0
        };
      }),
      release: vi.fn()
    };

    return client;
  });

  let connectionIndex = 0;

  const connect = vi.fn(async (): Promise<PostgresDriverClient> => {
    const client = clients[connectionIndex];
    connectionIndex += 1;

    if (client === undefined) {
      throw new Error("No test PostgreSQL connection is configured.");
    }

    return client;
  });

  const pool: PostgresDriverPool = {
    connect,
    end: vi.fn(async () => undefined)
  };

  return {
    pool,
    callsByConnection,
    connect
  };
}

const TENANT_ID = "11111111-1111-4111-8111-111111111111";

describe("PostgreSQL effective runtime-role protection", () => {
  it("includes inherited and SET ROLE checks in the safety query", () => {
    expect(POSTGRES_RUNTIME_ROLE_SAFETY_SQL).toContain(
      "pg_has_role(session_user, candidate.oid, 'USAGE')"
    );

    expect(POSTGRES_RUNTIME_ROLE_SAFETY_SQL).toContain(
      "pg_has_role(session_user, candidate.oid, 'SET')"
    );

    expect(POSTGRES_RUNTIME_ROLE_SAFETY_SQL).toContain(
      "current_user = session_user"
    );

    expect(POSTGRES_RUNTIME_ROLE_SAFETY_SQL).toContain(
      "relation.relowner IN (SELECT oid FROM effective_roles)"
    );
  });

  it("fails closed when a connection has a changed session role", async () => {
    const fixture = makePool([
      {
        ...SAFE_ROLE_RESULT,
        role_name: ""
      }
    ]);

    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => undefined
      )
    ).rejects.toMatchObject({
      name: "PostgresRuntimeRoleError",
      code: "INVALID_ROLE_RESULT"
    });

    expect(fixture.calls).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    ]);
  });

  it("rechecks the exact pooled connection before every transaction", async () => {
    const fixture = makeSequencedPool([
      [SAFE_ROLE_RESULT],
      [
        {
          ...SAFE_ROLE_RESULT,
          role_name: ""
        }
      ]
    ]);

    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => "first transaction"
      )
    ).resolves.toBe("first transaction");

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => "must never execute"
      )
    ).rejects.toMatchObject({
      name: "PostgresRuntimeRoleError",
      code: "INVALID_ROLE_RESULT"
    });

    expect(fixture.connect).toHaveBeenCalledTimes(2);

    expect(fixture.callsByConnection[0]).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED",
      "SELECT set_config('app.tenant_id', $1, true) AS tenant_id",
      "COMMIT"
    ]);

    expect(fixture.callsByConnection[1]).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    ]);
  });

  it("does not permanently cache a failed role verification", async () => {
    const fixture = makeSequencedPool([
      [
        {
          ...SAFE_ROLE_RESULT,
          role_name: ""
        }
      ],
      [SAFE_ROLE_RESULT]
    ]);

    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.verifyRuntimeRoleSafety()
    ).rejects.toMatchObject({
      name: "PostgresRuntimeRoleError",
      code: "INVALID_ROLE_RESULT"
    });

    await expect(
      runtime.verifyRuntimeRoleSafety()
    ).resolves.toBeUndefined();

    expect(fixture.connect).toHaveBeenCalledTimes(2);

    expect(fixture.callsByConnection[0]).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    ]);

    expect(fixture.callsByConnection[1]).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    ]);
  });

  it("allows a verified non-owner application role", async () => {
    const fixture = makePool([SAFE_ROLE_RESULT]);
    const runtime = new PostgresRuntime(fixture.pool);

    const result = await runtime.withTenantTransaction(
      { tenantId: TENANT_ID },
      async (transaction) => {
        expect(transaction.tenantId).toBe(TENANT_ID);
        return "verified";
      }
    );

    expect(result).toBe("verified");
    expect(fixture.calls.at(-1)).toBe("COMMIT");
  });
});
