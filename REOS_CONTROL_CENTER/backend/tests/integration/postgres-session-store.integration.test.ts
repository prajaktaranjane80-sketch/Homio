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
  PostgresRuntime,
  type PostgresDriverPool
} from "../../src/persistence/postgres.js";
import {
  PostgresSessionStore
} from "../../src/persistence/postgres-session-store.js";
import type {
  TrustedRequestContext,
  VerifiedExternalPrincipal
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

postgresSuite("PostgresSessionStore PostgreSQL integration", () => {
  let adminPool: Pool;
  let roleScopedPool: Pool;
  let runtime: PostgresRuntime;

  beforeAll(async () => {
    adminPool = new Pool({
      connectionString: adminUrl,
      max: 3
    });

    roleScopedPool = new Pool({
      connectionString: adminUrl,
      max: 3
    });

    const role = quoteRole(applicationRole!);

    const rolePool = {
      connect: async () => {
        const client = await roleScopedPool.connect();

        try {
          await client.query(`SET ROLE ${role}`);
          return client;
        } catch (error) {
          client.release();
          throw error;
        }
      },
      end: async () => roleScopedPool.end()
    };

    runtime = new PostgresRuntime(
      rolePool as unknown as PostgresDriverPool
    );

    await runtime.verifyRuntimeRoleSafety();
  });

  afterAll(async () => {
    await runtime?.close().catch(() => undefined);
    await adminPool?.end();
  });

  it("persists, validates and revokes a session bound to CORE-001 context and authentication epoch", async () => {
    const identityId = randomUUID();
    const accountId = randomUUID();
    const tenantId = randomUUID();
    const organizationId = randomUUID();
    const membershipId = randomUUID();
    const suffix = randomUUID().slice(0, 8);
    const now = new Date();
    const createdAt = now.toISOString();
    const issuedAtEpochSeconds =
      Math.floor(now.getTime() / 1_000) - 5;
    const expiresAtEpochSeconds =
      issuedAtEpochSeconds + 3_600;

    const context: TrustedRequestContext = {
      identityId,
      accountId,
      authenticationEpoch: 1,
      tenantId,
      tenantRevision: 1,
      organizationId,
      membershipId,
      membershipRevision: 1
    };

    const principal: VerifiedExternalPrincipal = {
      issuer: "https://identity.example.test/",
      subject: `b4-session-subject-${suffix}`,
      audiences: ["homio-api"],
      clientId: "homio-frontend",
      tokenId: randomUUID(),
      issuedAtEpochSeconds,
      expiresAtEpochSeconds
    };

    const adminClient = await adminPool.connect();

    try {
      await adminClient.query("BEGIN");

      await adminClient.query(
        `INSERT INTO core001.identities (
           identity_id,
           identity_type,
           display_name,
           handle,
           status,
           privacy_class,
           revision,
           created_at,
           updated_at
         )
         VALUES ($1, 'TEST', 'B4 Session Test', $2, 'ACTIVE', 'TEST', 1, $3, $3)`,
        [
          identityId,
          `b4-session-${suffix}`,
          createdAt
        ]
      );

      await adminClient.query(
        `INSERT INTO core001.identity_accounts (
           account_id,
           identity_id,
           status,
           authentication_epoch,
           created_at,
           updated_at
         )
         VALUES ($1, $2, 'ENABLED', 1, $3, $3)`,
        [
          accountId,
          identityId,
          createdAt
        ]
      );

      await adminClient.query(
        `INSERT INTO core001.tenants (
           tenant_id,
           tenant_kind,
           operating_mode,
           display_name,
           slug,
           status,
           isolation_profile,
           residency_mode,
           quota_profile,
           revision,
           created_at,
           updated_at
         )
         VALUES (
           $1, 'TEST', 'TEST', 'B4 Session Tenant', $2,
           'ACTIVE', 'TEST', 'TEST', '{}'::jsonb, 1, $3, $3
         )`,
        [
          tenantId,
          `b4-session-tenant-${suffix}`,
          createdAt
        ]
      );

      await adminClient.query(
        `INSERT INTO core001.organizations (
           organization_id,
           tenant_id,
           display_name,
           slug,
           status,
           revision,
           created_at,
           updated_at
         )
         VALUES (
           $1, $2, 'B4 Session Organization', $3,
           'ACTIVE', 1, $4, $4
         )`,
        [
          organizationId,
          tenantId,
          `b4-session-org-${suffix}`,
          createdAt
        ]
      );

      await adminClient.query(
        `INSERT INTO core001.memberships (
           membership_id,
           tenant_id,
           organization_id,
           identity_id,
           status,
           assurance,
           valid_from,
           revision,
           created_at,
           updated_at
         )
         VALUES (
           $1, $2, $3, $4, 'ACTIVE', 'TEST',
           $5, 1, $5, $5
         )`,
        [
          membershipId,
          tenantId,
          organizationId,
          identityId,
          createdAt
        ]
      );

      await adminClient.query("COMMIT");
    } catch (error) {
      await adminClient.query("ROLLBACK").catch(() => undefined);
      throw error;
    } finally {
      adminClient.release();
    }

    const store = new PostgresSessionStore(runtime);

    try {
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

      const secondPrincipal: VerifiedExternalPrincipal = {
        ...principal,
        tokenId: randomUUID()
      };

      await store.establishSession({
        principal: secondPrincipal,
        context
      });

      await adminPool.query(
        `UPDATE core001.identity_accounts
            SET authentication_epoch = 2,
                updated_at = clock_timestamp()
          WHERE account_id = $1`,
        [accountId]
      );

      await expect(
        store.isSessionActive({
          principal: secondPrincipal,
          context: {
            ...context,
            authenticationEpoch: 2
          }
        })
      ).resolves.toBe(false);

      await adminPool.query(
        `UPDATE core001.identity_accounts
            SET authentication_epoch = 1,
                updated_at = clock_timestamp()
          WHERE account_id = $1`,
        [accountId]
      );
    } finally {
      await adminPool.query(
        "DELETE FROM reos_infra.api_sessions WHERE tenant_id = $1",
        [tenantId]
      );

      await adminPool.query(
        "DELETE FROM core001.memberships WHERE tenant_id = $1",
        [tenantId]
      );

      await adminPool.query(
        "DELETE FROM core001.organizations WHERE tenant_id = $1",
        [tenantId]
      );

      await adminPool.query(
        "DELETE FROM core001.tenants WHERE tenant_id = $1",
        [tenantId]
      );

      await adminPool.query(
        "DELETE FROM core001.identity_accounts WHERE account_id = $1",
        [accountId]
      );

      await adminPool.query(
        "DELETE FROM core001.identities WHERE identity_id = $1",
        [identityId]
      );
    }
  });
});
