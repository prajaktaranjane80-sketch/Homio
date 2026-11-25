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

const APPEND_SQL = `
  SELECT reos_infra.append_security_audit_event(
    $1::uuid,
    $2::text,
    $3::uuid,
    $4::timestamptz,
    $5::text,
    $6::text,
    $7::uuid,
    $8::uuid
  )
`;

const DIRECT_INSERT_SQL = `
  INSERT INTO reos_infra.security_audit_events (
    event_id,
    event_type,
    request_id,
    occurred_at,
    reason_code,
    operation,
    actor_identity_reference,
    tenant_reference
  )
  VALUES (
    $1::uuid,
    $2::text,
    $3::uuid,
    $4::timestamptz,
    $5::text,
    $6::text,
    $7::uuid,
    $8::uuid
  )
`;

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

function createTenantEvent(): SecurityAuditEvent {
  return {
    eventType: "API_ACCESS_DENIED",
    requestId: randomUUID(),
    occurredAt: new Date().toISOString(),
    reasonCode: "B4_AUDIT_INTEGRATION",
    operation: "inventory.read",
    actorIdentityId: randomUUID(),
    tenantId: randomUUID()
  };
}

function createGlobalEvent(): SecurityAuditEvent {
  return {
    eventType: "API_ACCESS_DENIED",
    requestId: randomUUID(),
    occurredAt: new Date().toISOString(),
    reasonCode: "B4_GLOBAL_AUDIT"
  };
}

function appendValues(
  event: SecurityAuditEvent,
  eventId = randomUUID()
): unknown[] {
  return [
    eventId,
    event.eventType,
    event.requestId,
    event.occurredAt,
    event.reasonCode,
    event.operation ?? null,
    event.actorIdentityId ?? null,
    event.tenantId ?? null
  ];
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
      "persists tenant audit events through the actual application role and blocks direct table access",
      async () => {
        const target = requireDatabase(database);
        const event = createTenantEvent();
        const store = new PostgresSecurityAuditStore(target.runtime);

        await store.record(event);

        /*
         * The application role does not receive direct INSERT, SELECT,
         * UPDATE, DELETE or TRUNCATE access to audit history.
         */
        await expect(
          target.applicationPool.query(
            DIRECT_INSERT_SQL,
            appendValues(createTenantEvent())
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

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

        await expect(
          target.applicationPool.query(
            "TRUNCATE TABLE reos_infra.security_audit_events"
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

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
          event_type: event.eventType,
          request_id: event.requestId,
          reason_code: event.reasonCode,
          operation: event.operation,
          actor_identity_reference: event.actorIdentityId,
          tenant_reference: event.tenantId
        });

        /*
         * The existing append-only trigger also protects against
         * privileged accidental updates and deletes.
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
      "accepts a legitimate global event only through the global transaction path",
      async () => {
        const target = requireDatabase(database);
        const event = createGlobalEvent();
        const store = new PostgresSecurityAuditStore(target.runtime);

        await store.record(event);

        const stored = await target.adminPool.query<{
          readonly request_id: string;
          readonly actor_identity_reference: string | null;
          readonly tenant_reference: string | null;
        }>(
          `
            SELECT
              request_id,
              actor_identity_reference,
              tenant_reference
            FROM reos_infra.security_audit_events
            WHERE request_id = $1
          `,
          [event.requestId]
        );

        expect(stored.rows).toHaveLength(1);
        expect(stored.rows[0]).toEqual({
          request_id: event.requestId,
          actor_identity_reference: null,
          tenant_reference: null
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "rejects a tenant-scoped append when no tenant transaction context exists",
      async () => {
        const target = requireDatabase(database);
        const event = createTenantEvent();

        await expect(
          target.runtime.withGlobalTransaction(
            async (transaction) =>
              transaction.query(
                APPEND_SQL,
                appendValues(event)
              )
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

        const stored = await target.adminPool.query(
          `
            SELECT event_id
            FROM reos_infra.security_audit_events
            WHERE request_id = $1
          `,
          [event.requestId]
        );

        expect(stored.rows).toHaveLength(0);
      },
      TEST_TIMEOUT_MS
    );

    it(
      "rejects an audit row whose tenant reference differs from the trusted transaction tenant",
      async () => {
        const target = requireDatabase(database);
        const trustedTenantId = randomUUID();
        const forgedTenantId = randomUUID();

        expect(forgedTenantId).not.toBe(trustedTenantId);

        const event: SecurityAuditEvent = {
          eventType: "API_ACCESS_DENIED",
          requestId: randomUUID(),
          occurredAt: new Date().toISOString(),
          reasonCode: "B4_FORGED_TENANT",
          operation: "inventory.read",
          actorIdentityId: randomUUID(),
          tenantId: forgedTenantId
        };

        await expect(
          target.runtime.withTenantTransaction(
            { tenantId: trustedTenantId },
            async (transaction) =>
              transaction.query(
                APPEND_SQL,
                appendValues(event)
              )
          )
        ).rejects.toMatchObject({
          code: "42501"
        });

        const stored = await target.adminPool.query(
          `
            SELECT event_id
            FROM reos_infra.security_audit_events
            WHERE request_id = $1
          `,
          [event.requestId]
        );

        expect(stored.rows).toHaveLength(0);
      },
      TEST_TIMEOUT_MS
    );

    it(
      "enforces the tenant-context trigger even for a privileged direct table insert",
      async () => {
        const target = requireDatabase(database);
        const trustedTenantId = randomUUID();
        const forgedTenantId = randomUUID();

        const event: SecurityAuditEvent = {
          eventType: "API_ACCESS_DENIED",
          requestId: randomUUID(),
          occurredAt: new Date().toISOString(),
          reasonCode: "B4_TRIGGER_TENANT_GUARD",
          operation: "inventory.read",
          actorIdentityId: randomUUID(),
          tenantId: forgedTenantId
        };

        const client = await target.adminPool.connect();

        try {
          await client.query("BEGIN");

          await client.query(
            "SELECT set_config('app.tenant_id', $1, true)",
            [trustedTenantId]
          );

          await expect(
            client.query(
              DIRECT_INSERT_SQL,
              appendValues(event)
            )
          ).rejects.toMatchObject({
            code: "42501"
          });

          await client.query("ROLLBACK");
        } catch (error) {
          await client.query("ROLLBACK").catch(() => undefined);
          throw error;
        } finally {
          client.release();
        }

        const stored = await target.adminPool.query(
          `
            SELECT event_id
            FROM reos_infra.security_audit_events
            WHERE request_id = $1
          `,
          [event.requestId]
        );

        expect(stored.rows).toHaveLength(0);
      },
      TEST_TIMEOUT_MS
    );

    it(
      "keeps append-function ownership and grants restricted to the migration boundary",
      async () => {
        const target = requireDatabase(database);

        const result = await target.adminPool.query<{
          readonly function_owner: string;
          readonly table_owner: string;
          readonly app_can_execute: boolean;
          readonly public_can_execute: boolean;
          readonly app_can_insert: boolean;
          readonly app_can_select: boolean;
          readonly app_can_update: boolean;
          readonly app_can_delete: boolean;
          readonly app_can_truncate: boolean;
          readonly function_settings: string[] | null;
        }>(
          `
            SELECT
              pg_catalog.pg_get_userbyid(functions.proowner)
                AS function_owner,
              pg_catalog.pg_get_userbyid(relations.relowner)
                AS table_owner,
              pg_catalog.has_function_privilege(
                $1,
                functions.oid,
                'EXECUTE'
              ) AS app_can_execute,
              EXISTS (
                SELECT 1
                FROM pg_catalog.aclexplode(
                  COALESCE(
                    functions.proacl,
                    pg_catalog.acldefault('f', functions.proowner)
                  )
                ) AS function_acl
                WHERE function_acl.grantee = 0
                  AND function_acl.privilege_type = 'EXECUTE'
              ) AS public_can_execute,
              pg_catalog.has_table_privilege(
                $1,
                relations.oid,
                'INSERT'
              ) AS app_can_insert,
              pg_catalog.has_table_privilege(
                $1,
                relations.oid,
                'SELECT'
              ) AS app_can_select,
              pg_catalog.has_table_privilege(
                $1,
                relations.oid,
                'UPDATE'
              ) AS app_can_update,
              pg_catalog.has_table_privilege(
                $1,
                relations.oid,
                'DELETE'
              ) AS app_can_delete,
              pg_catalog.has_table_privilege(
                $1,
                relations.oid,
                'TRUNCATE'
              ) AS app_can_truncate,
              functions.proconfig AS function_settings
            FROM pg_catalog.pg_proc AS functions
            CROSS JOIN pg_catalog.pg_class AS relations
            WHERE functions.oid =
              'reos_infra.append_security_audit_event(uuid,text,uuid,timestamptz,text,text,uuid,uuid)'::regprocedure
              AND relations.oid =
              'reos_infra.security_audit_events'::regclass
          `,
          [target.applicationRole]
        );

        expect(result.rows).toHaveLength(1);

        const privileges = result.rows[0];

        expect(privileges).toBeDefined();

        expect(privileges?.function_owner).toBe(
          privileges?.table_owner
        );

        expect(privileges?.function_owner).not.toBe(
          target.applicationRole
        );

        expect(privileges?.app_can_execute).toBe(true);
        expect(privileges?.public_can_execute).toBe(false);

        expect(privileges?.app_can_insert).toBe(false);
        expect(privileges?.app_can_select).toBe(false);
        expect(privileges?.app_can_update).toBe(false);
        expect(privileges?.app_can_delete).toBe(false);
        expect(privileges?.app_can_truncate).toBe(false);

        expect(privileges?.function_settings).toContain(
          "search_path=pg_catalog"
        );

        const triggerFunction = await target.adminPool.query<{
          readonly function_owner: string;
          readonly function_settings: string[] | null;
        }>(
          `
            SELECT
              pg_catalog.pg_get_userbyid(proowner) AS function_owner,
              proconfig AS function_settings
            FROM pg_catalog.pg_proc
            WHERE oid =
              'reos_infra.enforce_security_audit_tenant_context()'::regprocedure
          `
        );

        expect(triggerFunction.rows).toHaveLength(1);
        expect(triggerFunction.rows[0]?.function_owner).toBe(
          privileges?.table_owner
        );
        expect(
          triggerFunction.rows[0]?.function_settings
        ).toContain("search_path=pg_catalog");
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
