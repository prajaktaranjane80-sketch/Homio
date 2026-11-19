
import { describe, expect, it, vi } from "vitest";

import {
  PostgresRuntime,
  POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
  PostgresRuntimeClosedError,
  PostgresRuntimeRoleError,
  PostgresTenantContextError,
  PostgresTransactionClosedError,
  PostgresTransactionOutcomeUnknownError,
  PostgresTransactionRollbackError
} from "../../src/persistence/postgres.js";
import type {
  PostgresDriverClient,
  PostgresDriverPool,
  PostgresQueryResult,
  PostgresTransaction
} from "../../src/persistence/postgres.js";

interface QueryCall {
  readonly sql: string;
  readonly values: readonly unknown[] | undefined;
}

const SAFE_ROLE_RESULT = {
  role_name: "homio_api",
  is_superuser: false,
  bypasses_row_security: false,
  owns_application_tables: false,
  tenant_table_count: 2,
  tenant_tables_force_rls: true,
  tenant_tables_have_tenant_restrictive_guard: true
};

function makePool(options: {
  readonly failOn?: string;
  readonly connectionFailure?: Error;
  readonly roleRows?: readonly unknown[];
} = {}): {
  readonly pool: PostgresDriverPool;
  readonly calls: QueryCall[];
  readonly releaseErrors: (Error | boolean | undefined)[];
  readonly connect: ReturnType<typeof vi.fn>;
  readonly end: ReturnType<typeof vi.fn>;
} {
  const calls: QueryCall[] = [];
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

      if (sql === options.failOn) {
        throw new Error(`query failed: ${sql}`);
      }

      if (sql === POSTGRES_RUNTIME_ROLE_SAFETY_SQL) {
        return {
          rows: options.roleRows ?? [SAFE_ROLE_RESULT],
          rowCount: 1
        };
      }

      return {
        rows: [],
        rowCount: 0
      };
    }),
    release: vi.fn((error?: Error | boolean) => {
      releaseErrors.push(error);
    })
  };

  const connect = vi.fn(async () => {
    if (options.connectionFailure !== undefined) {
      throw options.connectionFailure;
    }

    return client;
  });
  const end = vi.fn(async () => undefined);

  return {
    pool: { connect, end },
    calls,
    releaseErrors,
    connect,
    end
  };
}

const TENANT_ID = "11111111-1111-4111-8111-111111111111";

describe("PostgreSQL tenant transaction owner", () => {
  it("sets a transaction-local tenant and uses one checked-out client through commit", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    const result = await runtime.withTenantTransaction(
      { tenantId: TENANT_ID.toUpperCase() },
      async (transaction) => {
        expect(transaction.tenantId).toBe(TENANT_ID);
        expect(Object.isFrozen(transaction)).toBe(true);

        await transaction.query(
          "SELECT lead_id FROM core003_leads WHERE lead_id = $1",
          ["lead-opaque-001"]
        );

        return "committed";
      }
    );

    expect(result).toBe("committed");
    expect(fixture.connect).toHaveBeenCalledTimes(1);
    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED",
      "SELECT set_config('app.tenant_id', $1, true) AS tenant_id",
      "SELECT lead_id FROM core003_leads WHERE lead_id = $1",
      "COMMIT"
    ]);
    expect(fixture.calls[2]?.values).toEqual([TENANT_ID]);
    expect(fixture.calls[3]?.values).toEqual(["lead-opaque-001"]);
    expect(fixture.releaseErrors).toEqual([undefined]);
  });

  it("rolls back handler failures and preserves the original error", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);
    const failure = new Error("repository operation failed");

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => {
          throw failure;
        }
      )
    ).rejects.toBe(failure);

    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED",
      "SELECT set_config('app.tenant_id', $1, true) AS tenant_id",
      "ROLLBACK"
    ]);
    expect(fixture.releaseErrors).toEqual([undefined]);
  });

  it("destroys a connection when rollback fails and retains both failures", async () => {
    const fixture = makePool({ failOn: "ROLLBACK" });
    const runtime = new PostgresRuntime(fixture.pool);
    const failure = new Error("repository operation failed");

    let thrown: unknown;

    try {
      await runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => {
          throw failure;
        }
      );
    } catch (error) {
      thrown = error;
    }

    expect(thrown).toBeInstanceOf(PostgresTransactionRollbackError);
    expect((thrown as PostgresTransactionRollbackError).originalError).toBe(failure);
    expect(
      ((thrown as PostgresTransactionRollbackError).rollbackError as Error).message
    ).toBe("query failed: ROLLBACK");
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("does not retry or roll back after an ambiguous commit failure", async () => {
    const fixture = makePool({ failOn: "COMMIT" });
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => "write-result"
      )
    ).rejects.toBeInstanceOf(PostgresTransactionOutcomeUnknownError);

    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED",
      "SELECT set_config('app.tenant_id', $1, true) AS tenant_id",
      "COMMIT"
    ]);
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("blocks superuser, BYPASSRLS and missing tenant policy guards before BEGIN", async () => {
    for (const unsafeRow of [
      { ...SAFE_ROLE_RESULT, is_superuser: true },
      { ...SAFE_ROLE_RESULT, bypasses_row_security: true },
      { ...SAFE_ROLE_RESULT, owns_application_tables: true },
      { ...SAFE_ROLE_RESULT, tenant_tables_force_rls: false },
      { ...SAFE_ROLE_RESULT, tenant_table_count: 0 },
      {
        ...SAFE_ROLE_RESULT,
        tenant_tables_have_tenant_restrictive_guard: false
      }
    ]) {
      const fixture = makePool({ roleRows: [unsafeRow] });
      const runtime = new PostgresRuntime(fixture.pool);

      await expect(
        runtime.withTenantTransaction(
          { tenantId: TENANT_ID },
          async () => undefined
        )
      ).rejects.toBeInstanceOf(PostgresRuntimeRoleError);

      expect(fixture.calls.map((call) => call.sql)).toEqual([
        POSTGRES_RUNTIME_ROLE_SAFETY_SQL
      ]);
    }
  });

  it("fails closed when runtime-role catalog verification is unavailable", async () => {
    const fixture = makePool({
      failOn: POSTGRES_RUNTIME_ROLE_SAFETY_SQL
    });
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => undefined
      )
    ).rejects.toMatchObject({
      name: "PostgresRuntimeRoleError",
      code: "ROLE_CHECK_UNAVAILABLE"
    });

    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });

  it("rejects malformed tenant identifiers before acquiring a connection", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: " tenant-a " },
        async () => undefined
      )
    ).rejects.toBeInstanceOf(PostgresTenantContextError);

    expect(fixture.connect).not.toHaveBeenCalled();
  });

  it("rejects caller-controlled isolation SQL before acquiring a connection", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => undefined,
        { isolationLevel: "READ COMMITTED; DROP TABLE core003_leads" as never }
      )
    ).rejects.toThrow("Unsupported PostgreSQL transaction isolation level");

    expect(fixture.connect).not.toHaveBeenCalled();
  });

  it("uses a read-only transaction when requested", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    await runtime.withTenantTransaction(
      { tenantId: TENANT_ID },
      async (transaction) => {
        expect(transaction.readOnly).toBe(true);
      },
      {
        isolationLevel: "REPEATABLE READ",
        readOnly: true
      }
    );

    expect(fixture.calls[1]?.sql).toBe(
      "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"
    );
  });

  it("does not allow a transaction handle to escape its callback", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);
    let escaped: PostgresTransaction | undefined;

    await runtime.withTenantTransaction(
      { tenantId: TENANT_ID },
      async (transaction) => {
        escaped = transaction;
      }
    );

    await expect(
      escaped?.query("SELECT 1")
    ).rejects.toBeInstanceOf(PostgresTransactionClosedError);

    expect(fixture.calls.map((call) => call.sql)).not.toContain("SELECT 1");
  });

  it("closes the owned pool once and refuses transactions afterward", async () => {
    const fixture = makePool();
    const runtime = new PostgresRuntime(fixture.pool);

    const firstClose = runtime.close();
    const secondClose = runtime.close();

    expect(secondClose).toBe(firstClose);
    await firstClose;
    expect(fixture.end).toHaveBeenCalledTimes(1);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => undefined
      )
    ).rejects.toBeInstanceOf(PostgresRuntimeClosedError);
    expect(fixture.connect).not.toHaveBeenCalled();
  });

  it("destroys a connection when BEGIN fails", async () => {
    const fixture = makePool({
      failOn: "BEGIN ISOLATION LEVEL READ COMMITTED"
    });
    const runtime = new PostgresRuntime(fixture.pool);

    await expect(
      runtime.withTenantTransaction(
        { tenantId: TENANT_ID },
        async () => undefined
      )
    ).rejects.toThrow(
      "query failed: BEGIN ISOLATION LEVEL READ COMMITTED"
    );

    expect(fixture.calls.map((call) => call.sql)).toEqual([
      POSTGRES_RUNTIME_ROLE_SAFETY_SQL,
      "BEGIN ISOLATION LEVEL READ COMMITTED"
    ]);
    expect(fixture.releaseErrors[0]).toBeInstanceOf(Error);
  });
});
