
import { describe, expect, it, vi } from "vitest";

import {
  PostgresRuntime,
  POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
  PostgresRuntimeRoleError
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

describe("PostgreSQL effective runtime-role protection", () => {
  it("checks inherited and SET ROLE privileges, not only current_user", () => {
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
        {
          tenantId: "11111111-1111-4111-8111-111111111111"
        },
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

  it("allows a verified non-owner application role", async () => {
    const fixture = makePool([SAFE_ROLE_RESULT]);
    const runtime = new PostgresRuntime(fixture.pool);

    const result = await runtime.withTenantTransaction(
      {
        tenantId: "11111111-1111-4111-8111-111111111111"
      },
      async (transaction) => {
        expect(transaction.tenantId).toBe(
          "11111111-1111-4111-8111-111111111111"
        );
        return "verified";
      }
    );

    expect(result).toBe("verified");
    expect(fixture.calls.at(-1)).toBe("COMMIT");
  });
});
