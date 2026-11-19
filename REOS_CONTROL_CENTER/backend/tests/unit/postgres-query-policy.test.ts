
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

const TENANT_ID = "11111111-1111-4111-8111-111111111111";
const TENANT_SETTING_SQL =
  "SELECT set_config('app.tenant_id', $1, true) AS tenant_id";

const SAFE_ROLE_RESULT = {
  role_name: "homio_api",
  is_superuser: false,
  bypasses_row_security: false,
  owns_application_tables: false,
  tenant_table_count: 2,
  tenant_tables_force_rls: true,
  tenant_tables_have_tenant_restrictive_guard: true
};

interface QueryCall {
  readonly sql: string;
  readonly values: readonly unknown[] | undefined;
}

function makePool(options: {
  readonly failOn?: string;
} = {}): {
  readonly pool: PostgresDriverPool;
  readonly calls: QueryCall[];
} {
  const calls: QueryCall[] = [];

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
        return { rows: [SAFE_ROLE_RESULT], rowCount: 1 };
      }

      return { rows: [], rowCount: 0 };
    }),
    release: vi.fn()
  };

  const pool: PostgresDriverPool = {
    connect: vi.fn(async () => client),
    end: vi.fn(async () => undefined)
  };

  return { pool, calls };
}

const forbiddenQueries = [
  {
    sql: "COMMIT",
    code: "STATEMENT_NOT_ALLOWED"
  },
  {
    sql: "-- caller comment\nSET LOCAL app.tenant_id = '22222222-2222-4222-8222-222222222222'",
    code: "STATEMENT_NOT_ALLOWED"
  },
  {
    sql: "RESET app.tenant_id",
    code: "STATEMENT_NOT_ALLOWED"
  },
  {
    sql: "DISCARD ALL",
    code: "STATEMENT_NOT_ALLOWED"
  },
  {
    sql: "CREATE TEMP TABLE tenant_escape(id integer)",
    code: "STATEMENT_NOT_ALLOWED"
  },
  {
    sql: "SELECT set_config('app.tenant_id', $1, true)",
    code: "TENANT_CONTEXT_MUTATION"
  },
  {
    sql: "WITH changed AS (SELECT pg_catalog.set_config('app.tenant_id', $1, true)) SELECT 1",
    code: "TENANT_CONTEXT_MUTATION"
  },
  {
    sql: "SELECT pg_catalog.\"set_config\"('app.tenant_id', $1, true)",
    code: "TENANT_CONTEXT_MUTATION"
  },
  {
    sql: "SELECT U&\"set\\005fconfig\"('app.tenant_id', $1, true)",
    code: "INVALID_SQL"
  },
  {
    sql: "SELECT U&\"set!005fconfig\"('app.tenant_id', $1, true) UESCAPE '!'",
    code: "INVALID_SQL"
  },
  {
    sql: "SELECT pg_advisory_lock(9001)",
    code: "SESSION_STATE_MUTATION"
  },
  {
    sql: "SELECT pg_advisory_xact_lock(9001)",
    code: "SESSION_STATE_MUTATION"
  },
  {
    sql: "SELECT 1; COMMIT",
    code: "MULTIPLE_STATEMENTS"
  }
] as const;

describe("PostgreSQL transaction SQL boundary", () => {
  it.each(forbiddenQueries)(
    "rejects transaction/session escape SQL and poisons the transaction: $sql",
    async ({ sql, code }: (typeof forbiddenQueries)[number]) => {
      const fixture = makePool();
      const runtime = new PostgresRuntime(fixture.pool);

      const transaction = runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async (handle) => {
          await expect(handle.query(sql)).rejects.toMatchObject({
            name: "PostgresTransactionQueryPolicyError",
            code
          });

          return "handler attempted to ignore the policy denial";
        }
      );

      await expect(transaction).rejects.toBeInstanceOf(
        PostgresTransactionQueryPolicyError
      );

      expect(fixture.calls.map((call) => call.sql)).toEqual([
        POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
        "BEGIN ISOLATION LEVEL READ COMMITTED",
        TENANT_SETTING_SQL,
        "ROLLBACK"
      ]);
      expect(fixture.calls.map((call) => call.sql)).not.toContain(sql);
      expect(fixture.calls.map((call) => call.sql)).not.toContain("COMMIT");
    }
  );

  it("does not mistake semicolons and protected words inside literals for SQL commands", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await runtime.withTenantTransaction(
      { tenantId: TENANT_ID },
      async (transaction) => {
        await transaction.query(
          "SELECT 'semi;colon COMMIT set_config'::text AS safe_literal"
        );
        await transaction.query(
          "SELECT $body$COMMIT; SELECT set_config('app.tenant_id')$body$::text AS safe_body"
        );
        await transaction.query(
          "SELECT E'escaped\\' COMMIT; still literal'::text AS safe_escape"
        );
      }
    );

    expect(fixture.calls.map((call) => call.sql)).toContain(
      "SELECT 'semi;colon COMMIT set_config'::text AS safe_literal"
    );
    expect(fixture.calls.map((call) => call.sql)).toContain(
      "SELECT $body$COMMIT; SELECT set_config('app.tenant_id')$body$::text AS safe_body"
    );
    expect(fixture.calls.map((call) => call.sql)).toContain(
      "SELECT E'escaped\\' COMMIT; still literal'::text AS safe_escape"
    );
    expect(fixture.calls.map((call) => call.sql).at(-1)).toBe("COMMIT");
  });

  it("snapshots bind values before the query waits in the transaction queue", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await runtime.withTenantTransaction(
      { tenantId: TENANT_ID },
      async (transaction) => {
        const values = ["original-value"];
        const pending = transaction.query(
          "SELECT $1::text AS value",
          values
        );

        values[0] = "mutated-after-enqueue";
        await pending;
      }
    );

    const queryCall = fixture.calls.find(
      (call) => call.sql === "SELECT $1::text AS value"
    );

    expect(queryCall?.values).toEqual(["original-value"]);
  });

  it("stops dispatching queued queries after the first database query fails", async () => {
    const fixture = makePool({ failOn: "SELECT fail_now" });
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async (transaction) => {
          const first = transaction.query("SELECT fail_now");
          const second = transaction.query("SELECT must_not_reach_server");

          await Promise.allSettled([first, second]);
          return "handler ignored query failures";
        }
      )
    ).rejects.toThrow("query failed: SELECT fail_now");

    expect(fixture.calls.map((call) => call.sql)).toContain("SELECT fail_now");
    expect(fixture.calls.map((call) => call.sql)).not.toContain(
      "SELECT must_not_reach_server"
    );
    expect(fixture.calls.map((call) => call.sql).at(-1)).toBe("ROLLBACK");
    expect(fixture.calls.map((call) => call.sql)).not.toContain("COMMIT");
  });

  it("allows application DML and quoted identifiers without confusing UPDATE SET with SET commands", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await runtime.withTenantTransaction(
      { tenantId: TENANT_ID },
      async (transaction) => {
        await transaction.query(
          "UPDATE core003_leads SET status = $1 WHERE lead_id = $2",
          ["QUALIFIED", "lead-opaque-001"]
        );
        await transaction.query('SELECT * FROM "into"');
      }
    );

    expect(fixture.calls.map((call) => call.sql)).toContain(
      "UPDATE core003_leads SET status = $1 WHERE lead_id = $2"
    );
    expect(fixture.calls.map((call) => call.sql)).toContain(
      'SELECT * FROM "into"'
    );
    expect(fixture.calls.map((call) => call.sql).at(-1)).toBe("COMMIT");
  });

  it("rejects malformed or comment-only SQL and rolls back", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async (transaction) => {
          await transaction.query("/* first /* nested */ comment */ -- only comments");
        }
      )
    ).rejects.toMatchObject({
      name: "PostgresTransactionQueryPolicyError",
      code: "INVALID_SQL"
    });

    expect(fixture.calls.map((call) => call.sql).at(-1)).toBe("ROLLBACK");
  });
});
