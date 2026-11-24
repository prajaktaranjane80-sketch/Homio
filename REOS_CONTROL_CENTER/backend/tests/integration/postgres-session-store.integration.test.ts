import { createHash, randomUUID } from "node:crypto";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import {
  PostgresSessionStore
} from "../../src/persistence/postgres-session-store.js";

import type {
  TrustedRequestContext,
  VerifiedExternalPrincipal
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

function digest(value: string): string {
  return createHash("sha256")
    .update(value, "utf8")
    .digest("hex");
}

function createContext(): TrustedRequestContext {
  return {
    identityId: randomUUID(),
    accountId: randomUUID(),
    authenticationEpoch: 1,
    tenantId: randomUUID(),
    tenantRevision: 1,
    organizationId: randomUUID(),
    membershipId: randomUUID(),
    membershipRevision: 1
  };
}

function createPrincipal(
  tokenId: string
): VerifiedExternalPrincipal {
  const now = Math.floor(Date.now() / 1_000);

  return {
    issuer: "https://identity.example.test/",
    subject: `b4-session-${randomUUID()}`,
    audiences: ["homio-api"],
    clientId: "homio-backend-b4-integration",
    tokenId,
    issuedAtEpochSeconds: now - 5,
    expiresAtEpochSeconds: now + 3_600
  };
}

postgresSuite(
  "PostgresSessionStore real PostgreSQL integration",
  () => {
    let database: B4PostgresTestDatabase | undefined;

    beforeAll(async () => {
      database = await createB4PostgresTestDatabase();
    }, TEST_TIMEOUT_MS);

    afterAll(async () => {
      await database?.close();
    }, TEST_TIMEOUT_MS);

    it(
      "persists token-bound sessions and verifies them through the actual API database login",
      async () => {
        const target = requireDatabase(database);
        const store = new PostgresSessionStore(target.runtime);

        const context = createContext();
        const principal = createPrincipal(randomUUID());

        const sessionId = await store.establishSession({
          principal,
          context
        });

        expect(sessionId).toMatch(
          /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
        );

        await expect(
          store.isSessionActive({
            principal,
            context
          })
        ).resolves.toBe(true);

        /*
         * A fresh store instance reads the durable database row.
         * This is not an in-memory session registry.
         */
        const reloadedStore = new PostgresSessionStore(
          target.runtime
        );

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context
          })
        ).resolves.toBe(true);

        const persisted = await target.adminPool.query<{
          readonly tenant_id: string;
          readonly account_id: string;
          readonly identity_id: string;
          readonly authentication_epoch: string;
          readonly issuer_digest: string;
          readonly token_id_digest: string;
          readonly revoked_at: Date | null;
        }>(
          `
            SELECT
              tenant_id,
              account_id,
              identity_id,
              authentication_epoch,
              issuer_digest,
              token_id_digest,
              revoked_at
            FROM reos_infra.api_sessions
            WHERE session_id = $1
          `,
          [sessionId]
        );

        expect(persisted.rows).toHaveLength(1);

        expect(persisted.rows[0]).toMatchObject({
          tenant_id: context.tenantId,
          account_id: context.accountId,
          identity_id: context.identityId,
          issuer_digest: digest(principal.issuer),
          token_id_digest: digest(principal.tokenId),
          revoked_at: null
        });

        expect(persisted.rows[0]?.issuer_digest).not.toBe(
          principal.issuer
        );

        expect(persisted.rows[0]?.token_id_digest).not.toBe(
          principal.tokenId
        );

        /*
         * The session is bound to the exact CORE-001 trusted context.
         * A new authentication epoch or changed tenant/account cannot
         * resolve the original durable session.
         */
        await expect(
          reloadedStore.isSessionActive({
            principal,
            context: {
              ...context,
              authenticationEpoch: 2
            }
          })
        ).resolves.toBe(false);

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context: {
              ...context,
              tenantId: randomUUID()
            }
          })
        ).resolves.toBe(false);

        await expect(
          reloadedStore.isSessionActive({
            principal,
            context: {
              ...context,
              accountId: randomUUID()
            }
          })
        ).resolves.toBe(false);
      },
      TEST_TIMEOUT_MS
    );

    it(
      "makes token revocation durable, idempotent and irreversible",
      async () => {
        const target = requireDatabase(database);
        const store = new PostgresSessionStore(target.runtime);

        const context = createContext();
        const principal = createPrincipal(randomUUID());

        const sessionId = await store.establishSession({
          principal,
          context
        });

        await expect(
          store.revokeSession({
            principal,
            context,
            reasonCode: "B4_INTEGRATION_LOGOUT"
          })
        ).resolves.toBe(true);

        await expect(
          store.isSessionActive({
            principal,
            context
          })
        ).resolves.toBe(false);

        /*
         * Repeating the same revocation is safe and does not rewrite
         * the original timestamp or reason.
         */
        await expect(
          store.revokeSession({
            principal,
            context,
            reasonCode: "B4_INTEGRATION_LOGOUT"
          })
        ).resolves.toBe(true);

        const revoked = await target.adminPool.query<{
          readonly revoked_at: Date | null;
          readonly revocation_reason_code: string | null;
        }>(
          `
            SELECT
              revoked_at,
              revocation_reason_code
            FROM reos_infra.api_sessions
            WHERE session_id = $1
          `,
          [sessionId]
        );

        expect(revoked.rows).toHaveLength(1);
        expect(revoked.rows[0]?.revoked_at).not.toBeNull();
        expect(
          revoked.rows[0]?.revocation_reason_code
        ).toBe("B4_INTEGRATION_LOGOUT");

        /*
         * Even the database administrator cannot rewrite immutable
         * identity fields or delete the durable revocation record.
         */
        await expect(
          target.adminPool.query(
            `
              UPDATE reos_infra.api_sessions
                 SET account_id = $2
               WHERE session_id = $1
            `,
            [
              sessionId,
              randomUUID()
            ]
          )
        ).rejects.toMatchObject({
          code: "55000"
        });

        await expect(
          target.adminPool.query(
            `
              DELETE FROM reos_infra.api_sessions
               WHERE session_id = $1
            `,
            [sessionId]
          )
        ).rejects.toMatchObject({
          code: "55000"
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "revokes all active sessions for one tenant-scoped account without deleting history",
      async () => {
        const target = requireDatabase(database);
        const store = new PostgresSessionStore(target.runtime);

        const context = createContext();
        const firstPrincipal = createPrincipal(randomUUID());
        const secondPrincipal = createPrincipal(randomUUID());

        const firstSessionId = await store.establishSession({
          principal: firstPrincipal,
          context
        });

        const secondSessionId = await store.establishSession({
          principal: secondPrincipal,
          context
        });

        await expect(
          store.isSessionActive({
            principal: firstPrincipal,
            context
          })
        ).resolves.toBe(true);

        await expect(
          store.isSessionActive({
            principal: secondPrincipal,
            context
          })
        ).resolves.toBe(true);

        await expect(
          store.revokeAccountSessions({
            context,
            reasonCode: "B4_INTEGRATION_ACCOUNT_REVOKE"
          })
        ).resolves.toBe(2);

        await expect(
          store.isSessionActive({
            principal: firstPrincipal,
            context
          })
        ).resolves.toBe(false);

        await expect(
          store.isSessionActive({
            principal: secondPrincipal,
            context
          })
        ).resolves.toBe(false);

        const history = await target.adminPool.query<{
          readonly session_id: string;
          readonly revoked_at: Date | null;
          readonly revocation_reason_code: string | null;
        }>(
          `
            SELECT
              session_id,
              revoked_at,
              revocation_reason_code
            FROM reos_infra.api_sessions
            WHERE tenant_id = $1
              AND account_id = $2
            ORDER BY session_id
          `,
          [
            context.tenantId,
            context.accountId
          ]
        );

        expect(history.rows).toHaveLength(2);

        for (const row of history.rows) {
          expect(row.revoked_at).not.toBeNull();
          expect(row.revocation_reason_code).toBe(
            "B4_INTEGRATION_ACCOUNT_REVOKE"
          );
        }

        expect(
          history.rows.map((row) => row.session_id).sort()
        ).toEqual(
          [firstSessionId, secondSessionId].sort()
        );
      },
      TEST_TIMEOUT_MS
    );
  }
);
