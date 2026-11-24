import { randomUUID } from "node:crypto";

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

import {
  createB4PostgresTestDatabase
} from "../helpers/postgres-b4-test-database.js";

import type {
  B4PostgresTestDatabase
} from "../helpers/postgres-b4-test-database.js";

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;

const integrationEnabled =
  typeof adminUrl === "string" &&
  adminUrl.length > 0;

const postgresSuite = integrationEnabled
  ? describe
  : describe.skip;

const TEST_TIMEOUT_MS = 60_000;

function requireDatabase(
  database: B4PostgresTestDatabase | undefined
): B4PostgresTestDatabase {
  if (database === undefined) {
    throw new Error(
      "The isolated B4 PostgreSQL integration database was not initialized."
    );
  }

  return database;
}

postgresSuite(
  "PostgresSecurityAuditStore real PostgreSQL integration",
  () => {
    let database: B4PostgresTestDatabase | undefined;

    beforeAll(async () => {
      database = await createB4PostgresTestDatabase();
    }, TEST_TIMEOUT_MS);

    afterAll(async () => {
      await database?.close();
    }, TEST_TIMEOUT_MS);

    it(
      "allows the actual API login to insert minimized audit events only",
      async () => {
        const target = requireDatabase(database);

        const event: SecurityAuditEvent = {
          eventType: "API_ACCESS_DENIED",
          requestId: randomUUID(),
          occurredAt: new Date().toISOString(),
          reasonCode: "B4_AUDIT_INTEGRATION",
          operation: "inventory.read",
          actorIdentityId: randomUUID(),
          tenantId: randomUUID()
        };

        /*
         * This store call uses the actual PostgreSQL application login.
         * It does not simulate the application role with SET ROLE.
         */
        const store = new PostgresSecurityAuditStore({
          query: async (sql, values) => {
            const result = await target.applicationPool.query(
              sql,
              values as never[]
            );

            return {
              rowCount: result.rowCount
            };
          }
        });

        await store.record(event);

        /*
         * The API role has INSERT only. It cannot read its own audit
         * records or mutate/delete them.
         */
        await expect(
          target.applicationPool.query(
            `
              SELECT event_id
              FROM reos_infra.security_audit_events
              WHERE request_id = $1
            `,
            [event.requestId]
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

        await expect(
          target.applicationPool.query(
            `
              UPDATE reos_infra.security_audit_events
                 SET reason_code = 'MUTATED'
               WHERE request_id = $1
            `,
            [event.requestId]
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

        await expect(
          target.applicationPool.query(
            `
              DELETE FROM reos_infra.security_audit_events
               WHERE request_id = $1
            `,
            [event.requestId]
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

        /*
         * The privileged verification connection confirms the stored
         * record contains only the normalized audit references.
         */
        const stored = await target.adminPool.query<{
          readonly event_type: string;
          readonly request_id: string;
          readonly reason_code: string;
          readonly operation: string | null;
          readonly actor_identity_reference: string | null;
          readonly tenant_reference: string | null;
        }>(
          `
            SELECT
              event_type,
              request_id,
              reason_code,
              operation,
              actor_identity_reference,
              tenant_reference
            FROM reos_infra.security_audit_events
            WHERE request_id = $1
          `,
          [event.requestId]
        );

        expect(stored.rows).toHaveLength(1);

        expect(stored.rows[0]).toMatchObject({
          event_type: "API_ACCESS_DENIED",
          request_id: event.requestId,
          reason_code: "B4_AUDIT_INTEGRATION",
          operation: "inventory.read",
          actor_identity_reference: event.actorIdentityId,
          tenant_reference: event.tenantId
        });

        /*
         * The append-only trigger also protects against privileged
         * accidental updates and deletes.
         */
        await expect(
          target.adminPool.query(
            `
              UPDATE reos_infra.security_audit_events
                 SET reason_code = 'PRIVILEGED_MUTATION'
               WHERE request_id = $1
            `,
            [event.requestId]
          )
        ).rejects.toMatchObject({
          code: "55000"
        });

        await expect(
          target.adminPool.query(
            `
              DELETE FROM reos_infra.security_audit_events
               WHERE request_id = $1
            `,
            [event.requestId]
          )
        ).rejects.toMatchObject({
          code: "55000"
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "does not expose request bodies, bearer tokens or credential columns in persisted audit records",
      async () => {
        const target = requireDatabase(database);

        const result = await target.adminPool.query<{
          readonly column_name: string;
        }>(
          `
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'reos_infra'
              AND table_name = 'security_audit_events'
            ORDER BY ordinal_position
          `
        );

        expect(
          result.rows.map((row) => row.column_name)
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
      TEST_TIMEOUT_MS
    );
  }
);
