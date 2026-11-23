import {
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  PostgresSecurityAuditStore,
  PostgresSecurityAuditUnavailableError
} from "../../src/persistence/postgres-security-audit.js";

import type {
  SecurityAuditEvent
} from "../../src/security/contracts.js";

type AuditQuery = (
  sql: string,
  values?: unknown[]
) => Promise<{
  readonly rowCount: number | null;
}>;

const VALID_EVENT: SecurityAuditEvent = {
  eventType: "API_ACCESS_DENIED",
  requestId: "11111111-1111-4111-8111-111111111111",
  occurredAt: "2026-11-23T10:00:00.000Z",
  reasonCode: "INVALID_BEARER_TOKEN",
  operation: "inventory.read",
  actorIdentityId: "22222222-2222-4222-8222-222222222222",
  tenantId: "33333333-3333-4333-8333-333333333333"
};

function createQueryMock(options: {
  readonly rowCount?: number | null;
  readonly failure?: Error;
} = {}) {
  return vi.fn<AuditQuery>(async (sql, values) => {
    void sql;
    void values;

    if (options.failure !== undefined) {
      throw options.failure;
    }

    return {
      rowCount:
        options.rowCount === undefined
          ? 1
          : options.rowCount
    };
  });
}

describe("PostgresSecurityAuditStore", () => {
  it("inserts only minimized allowlisted audit fields", async () => {
    const query = createQueryMock();
    const store = new PostgresSecurityAuditStore({ query });

    await store.record(VALID_EVENT);

    expect(query).toHaveBeenCalledTimes(1);

    const call = query.mock.calls[0];

    expect(call?.[0]).toContain(
      "INSERT INTO reos_infra.security_audit_events"
    );

    expect(call?.[1]).toEqual([
      expect.any(String),
      "API_ACCESS_DENIED",
      VALID_EVENT.requestId,
      VALID_EVENT.occurredAt,
      "INVALID_BEARER_TOKEN",
      "inventory.read",
      VALID_EVENT.actorIdentityId,
      VALID_EVENT.tenantId
    ]);

    const serialized = JSON.stringify(call?.[1]);

    expect(serialized).not.toContain("Authorization");
    expect(serialized).not.toContain("Bearer ");
    expect(serialized).not.toContain("password");
    expect(serialized).not.toContain("cookie");
  });

  it("records denied events without trusted tenant context", async () => {
    const query = createQueryMock();
    const store = new PostgresSecurityAuditStore({ query });

    const event: SecurityAuditEvent = {
      eventType: "API_ACCESS_DENIED",
      requestId: "44444444-4444-4444-8444-444444444444",
      occurredAt: "2026-11-23T10:00:00.000Z",
      reasonCode: "BEARER_TOKEN_REQUIRED"
    };

    await store.record(event);

    const values = query.mock.calls[0]?.[1];

    expect(values?.[6]).toBeNull();
    expect(values?.[7]).toBeNull();
  });

  it("rejects invalid reason codes before database access", async () => {
    const query = createQueryMock();
    const store = new PostgresSecurityAuditStore({ query });

    await expect(
      store.record({
        ...VALID_EVENT,
        reasonCode: "invalid reason"
      })
    ).rejects.toThrow(
      "The API security audit event is invalid."
    );

    expect(query).not.toHaveBeenCalled();
  });

  it("rejects a non-UUID request ID before database access", async () => {
    const query = createQueryMock();
    const store = new PostgresSecurityAuditStore({ query });

    await expect(
      store.record({
        ...VALID_EVENT,
        requestId: "not-a-uuid"
      })
    ).rejects.toThrow(
      "The API security audit event is invalid."
    );

    expect(query).not.toHaveBeenCalled();
  });

  it("rejects timestamps without an explicit timezone", async () => {
    const query = createQueryMock();
    const store = new PostgresSecurityAuditStore({ query });

    await expect(
      store.record({
        ...VALID_EVENT,
        occurredAt: "2026-11-23T10:00:00"
      })
    ).rejects.toThrow(
      "The API security audit timestamp must be timezone-aware."
    );

    expect(query).not.toHaveBeenCalled();
  });

  it("fails closed when the insert fails", async () => {
    const query = createQueryMock({
      failure: new Error("private PostgreSQL detail")
    });

    const store = new PostgresSecurityAuditStore({ query });

    await expect(
      store.record(VALID_EVENT)
    ).rejects.toBeInstanceOf(
      PostgresSecurityAuditUnavailableError
    );
  });

  it("fails closed when the insert affects no row", async () => {
    const query = createQueryMock({
      rowCount: 0
    });

    const store = new PostgresSecurityAuditStore({ query });

    await expect(
      store.record(VALID_EVENT)
    ).rejects.toBeInstanceOf(
      PostgresSecurityAuditUnavailableError
    );
  });
});
