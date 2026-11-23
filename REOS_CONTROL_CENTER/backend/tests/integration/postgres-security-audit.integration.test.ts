import { randomUUID } from "node:crypto";

import { Pool } from "pg";
import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import {
  PostgresSecurityAuditStore
} from "../../src/persistence/postgres-security-audit.js";
import type {
  SecurityAuditEvent
} from "../../src/security/contracts.js";

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
const applicationRole =
  process.env.HOMIO_TEST_POSTGRES_APPLICATION_ROLE;

const postgresSuite =
  adminUrl !== undefined && applicationRole !== undefined
    ? describe
    : describe.skip;

function quoteRole(role: string): string {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(role)) {
    throw new Error("Invalid PostgreSQL application role name.");
  }

  return `"${role}"`;
}

postgresSuite("PostgresSecurityAuditStore PostgreSQL integration", () => {
  let pool: Pool;

  beforeAll(async () => {
    pool = new Pool({
      connectionString: adminUrl,
      max: 2
    });

    await pool.query("SELECT 1");
  });

  afterAll(async () => {
    await pool?.end();
  });

  it("allows minimized inserts only and rejects application reads and mutations", async () => {
    const client = await pool.connect();
    const requestId = randomUUID();

    const event: SecurityAuditEvent = {
      eventType: "API_ACCESS_DENIED",
      requestId,
      occurredAt: new Date().toISOString(),
      reasonCode: "B4_AUDIT_INTEGRATION",
      operation: "inventory.read",
      actorIdentityId: randomUUID(),
      tenantId: randomUUID()
    };

    try {
      await client.query("BEGIN");
      await client.query(`SET LOCAL ROLE ${quoteRole(applicationRole!)}`);

      const store = new PostgresSecurityAuditStore({
        query: async (sql, values) => {
          const result = await client.query(
            sql,
            values as never[]
          );

          return {
            rowCount: result.rowCount
          };
        }
      });

      await store.record(event);

      await expect(
        client.query(
          `SELECT event_id
             FROM reos_infra.security_audit_events
            WHERE request_id = $1`,
          [requestId]
        )
      ).rejects.toMatchObject({
        code: "42501"
      });

      await client.query("RESET ROLE");

      const stored = await client.query<{
        readonly event_type: string;
        readonly request_id: string;
        readonly reason_code: string;
        readonly operation: string | null;
        readonly actor_identity_reference: string | null;
        readonly tenant_reference: string | null;
      }>(
        `SELECT
           event_type,
           request_id,
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
        reason_code: "B4_AUDIT_INTEGRATION",
        operation: "inventory.read"
      });

      await client.query("SAVEPOINT audit_mutation");

      await expect(
        client.query(
          `UPDATE reos_infra.security_audit_events
              SET reason_code = 'MUTATED'
            WHERE request_id = $1`,
          [requestId]
        )
      ).rejects.toMatchObject({
        code: "55000"
      });

      await client.query("ROLLBACK TO SAVEPOINT audit_mutation");
    } finally {
      await client.query("ROLLBACK").catch(() => undefined);
      client.release();
    }
  });

  it("does not expose request body, bearer token or credential columns", async () => {
    const result = await pool.query<{
      readonly column_name: string;
    }>(
      `SELECT column_name
         FROM information_schema.columns
        WHERE table_schema = 'reos_infra'
          AND table_name = 'security_audit_events'
        ORDER BY ordinal_position`
    );

    expect(result.rows.map((row) => row.column_name)).toEqual([
      "event_id",
      "event_type",
      "request_id",
      "occurred_at",
      "reason_code",
      "operation",
      "actor_identity_reference",
      "tenant_reference"
    ]);
  });
});
