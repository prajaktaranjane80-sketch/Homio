
import { randomUUID } from "node:crypto";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import {
  createB4PostgresTestDatabase,
  type B4PostgresTestDatabase
} from "../helpers/postgres-b4-test-database.js";

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
const requiredSetting =
  process.env.HOMIO_REQUIRE_POSTGRES_INTEGRATION;

if (
  requiredSetting !== undefined &&
  requiredSetting !== "0" &&
  requiredSetting !== "1"
) {
  throw new Error(
    "HOMIO_REQUIRE_POSTGRES_INTEGRATION must be either 0 or 1."
  );
}

const integrationRequired = requiredSetting === "1";

const adminUrlConfigured =
  typeof adminUrl === "string" &&
  adminUrl.length > 0 &&
  adminUrl === adminUrl.trim();

const postgresSuite =
  integrationRequired || adminUrlConfigured
    ? describe
    : describe.skip;

interface RelationRow {
  readonly relation_name: string;
  readonly exists: boolean;
}

interface ApplicationRoleRow {
  readonly oid: string;
  readonly rolcanlogin: boolean;
  readonly rolinherit: boolean;
  readonly rolsuper: boolean;
  readonly rolcreatedb: boolean;
  readonly rolcreaterole: boolean;
  readonly rolreplication: boolean;
  readonly rolbypassrls: boolean;
}

interface TenantTableRow {
  readonly schema_name: string;
  readonly relation_name: string;
  readonly rls_enabled: boolean;
  readonly rls_forced: boolean;
  readonly application_role_is_owner: boolean;
  readonly restrictive_policy_present: boolean;
}

interface FinancialTypeRow {
  readonly formatted_type: string;
  readonly typmod: number;
}

interface MigrationLedgerRow {
  readonly migration_id: string;
  readonly migration_name: string;
  readonly checksum: string;
}

interface ApplicationIdentityRow {
  readonly session_user: string;
  readonly current_user: string;
}

interface LeadRow extends Record<string, unknown> {
  readonly tenant_id: string;
  readonly lead_id: string;
}

postgresSuite(
  "ARCH-037 PostgreSQL physical schema integration",
  () => {
    let database: B4PostgresTestDatabase | undefined;

    function requireDatabase(): B4PostgresTestDatabase {
      if (database === undefined) {
        throw new Error(
          "The shared B4 PostgreSQL test database was not initialized."
        );
      }

      return database;
    }

    beforeAll(async () => {
      database = await createB4PostgresTestDatabase();
    }, 60_000);

    afterAll(async () => {
      const current = database;
      database = undefined;

      await current?.close();
    }, 30_000);

    it("uses the generated application login and the complete canonical migration ledger", async () => {
      const current = requireDatabase();

      expect(current.postgresServerVersion).toBeGreaterThanOrEqual(
        180004
      );

      const identity = await current.applicationPool.query<ApplicationIdentityRow>(
        `
          SELECT
            session_user::text AS session_user,
            current_user::text AS current_user
        `
      );

      expect(identity.rows).toEqual([
        {
          session_user: current.applicationRole,
          current_user: current.applicationRole
        }
      ]);

      const ledger = await current.adminPool.query<MigrationLedgerRow>(
        `
          SELECT
            migration_id,
            migration_name,
            checksum
          FROM reos_infra.schema_migrations
          ORDER BY migration_id
        `
      );

      expect(ledger.rows).toEqual(
        current.migrationHistory.map((migration) => ({
          migration_id: migration.id,
          migration_name: migration.name,
          checksum: migration.checksum
        }))
      );

      expect(
        current.migrationHistory.map((migration) => migration.id)
      ).toEqual(
        current.migrationHistory.map((_, index) =>
          String(index + 1).padStart(8, "0")
        )
      );

      await expect(
        current.applicationPool.query(
          `
            SELECT migration_id
            FROM reos_infra.schema_migrations
          `
        )
      ).rejects.toMatchObject({
        code: "42501"
      });
    });

    it("has the ARCH-037 CORE owner relations and B4 persistence relations", async () => {
      const current = requireDatabase();

      const requiredRelations = [
        "core001.identities",
        "core001.identity_accounts",
        "core001.tenants",
        "core001.organizations",
        "core001.memberships",
        "core002.events",
        "core002.outbox_publications",
        "core003.leads",
        "core003.lead_ownership",
        "core003.ownership_transfers",
        "core004.projects",
        "core004.inventory",
        "core006.deals",
        "core006.deal_parties",
        "core007.governance_decisions",
        "core007.approval_requests",
        "core008.commission_contracts",
        "core008.financial_ledger_entries",
        "reos_infra.api_sessions",
        "reos_infra.security_audit_events"
      ];

      const result = await current.adminPool.query<RelationRow>(
        `
          SELECT
            required.relation_name,
            to_regclass(required.relation_name) IS NOT NULL AS exists
          FROM unnest($1::text[]) AS required(relation_name)
          ORDER BY required.relation_name
        `,
        [requiredRelations]
      );

      expect(result.rows).toHaveLength(requiredRelations.length);

      for (const row of result.rows) {
        expect(
          row.exists,
          `Missing required relation ${row.relation_name}`
        ).toBe(true);
      }
    });

    it("keeps CORE-005 as a derived read-side owner rather than a canonical SQL schema", async () => {
      const current = requireDatabase();

      const result = await current.adminPool.query<{
        readonly schema_exists: boolean;
      }>(
        `
          SELECT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_namespace
            WHERE nspname = 'core005'
          ) AS schema_exists
        `
      );

      expect(result.rows[0]?.schema_exists).toBe(false);
    });

    it("uses a dedicated application login and enforces FORCE RLS with a restrictive tenant policy", async () => {
      const current = requireDatabase();

      const roleResult =
        await current.adminPool.query<ApplicationRoleRow>(
          `
            SELECT
              oid::text AS oid,
              rolcanlogin,
              rolinherit,
              rolsuper,
              rolcreatedb,
              rolcreaterole,
              rolreplication,
              rolbypassrls
            FROM pg_catalog.pg_roles
            WHERE rolname = $1
          `,
          [current.applicationRole]
        );

      expect(roleResult.rows).toHaveLength(1);

      const role = roleResult.rows[0];

      if (role === undefined) {
        throw new Error(
          "The generated PostgreSQL application role was not returned."
        );
      }

      expect(role.rolcanlogin).toBe(true);
      expect(role.rolinherit).toBe(true);
      expect(role.rolsuper).toBe(false);
      expect(role.rolcreatedb).toBe(false);
      expect(role.rolcreaterole).toBe(false);
      expect(role.rolreplication).toBe(false);
      expect(role.rolbypassrls).toBe(false);

      const tenantTables =
        await current.adminPool.query<TenantTableRow>(
          `
            SELECT
              namespace.nspname AS schema_name,
              relation.relname AS relation_name,
              relation.relrowsecurity AS rls_enabled,
              relation.relforcerowsecurity AS rls_forced,
              relation.relowner = $1::oid AS application_role_is_owner,
              EXISTS (
                SELECT 1
                FROM pg_catalog.pg_policy AS policy
                WHERE policy.polrelid = relation.oid
                  AND policy.polpermissive = false
                  AND policy.polcmd = '*'
                  AND (
                    $1::oid = ANY(policy.polroles)
                    OR 0::oid = ANY(policy.polroles)
                  )
                  AND policy.polqual IS NOT NULL
                  AND policy.polwithcheck IS NOT NULL
              ) AS restrictive_policy_present
            FROM pg_catalog.pg_class AS relation
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            WHERE relation.relkind IN ('r', 'p')
              AND namespace.nspname NOT LIKE 'pg_%'
              AND namespace.nspname <> 'information_schema'
              AND EXISTS (
                SELECT 1
                FROM pg_catalog.pg_attribute AS attribute
                WHERE attribute.attrelid = relation.oid
                  AND attribute.attname = 'tenant_id'
                  AND attribute.attnum > 0
                  AND attribute.attisdropped = false
              )
            ORDER BY namespace.nspname, relation.relname
          `,
          [role.oid]
        );

      expect(tenantTables.rows.length).toBeGreaterThan(0);

      for (const relation of tenantTables.rows) {
        expect(
          relation.rls_enabled,
          `${relation.schema_name}.${relation.relation_name} must ENABLE RLS`
        ).toBe(true);

        expect(
          relation.rls_forced,
          `${relation.schema_name}.${relation.relation_name} must FORCE RLS`
        ).toBe(true);

        expect(
          relation.application_role_is_owner,
          `${relation.schema_name}.${relation.relation_name} must not be owned by the application role`
        ).toBe(false);

        expect(
          relation.restrictive_policy_present,
          `${relation.schema_name}.${relation.relation_name} must have an applicable restrictive tenant policy`
        ).toBe(true);
      }

      /*
       * This invokes the existing production safety owner. It verifies the
       * effective/inherited/assumable roles and exact approved policy
       * expressions on a real application-role connection.
       */
      await expect(
        current.runtime.verifyRuntimeRoleSafety()
      ).resolves.toBeUndefined();
    });

    it("uses unbounded PostgreSQL NUMERIC for financial ledger amounts", async () => {
      const current = requireDatabase();

      const result = await current.adminPool.query<FinancialTypeRow>(
        `
          SELECT
            format_type(attribute.atttypid, attribute.atttypmod)
              AS formatted_type,
            attribute.atttypmod AS typmod
          FROM pg_catalog.pg_attribute AS attribute
          WHERE attribute.attrelid =
            'core008.financial_ledger_entries'::regclass
            AND attribute.attname = 'amount'
            AND attribute.attnum > 0
            AND attribute.attisdropped = false
        `
      );

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.formatted_type).toBe("numeric");
      expect(result.rows[0]?.typmod).toBe(-1);
    });

    it("isolates tenant reads and rejects cross-tenant writes through the actual application login", async () => {
      const current = requireDatabase();

      const tenantA = randomUUID();
      const tenantB = randomUUID();

      const leadA = randomUUID();
      const leadB = randomUUID();

      const customerA = randomUUID();
      const customerB = randomUUID();

      const now = new Date().toISOString();

      for (const [tenantId, slug] of [
        [tenantA, `b4-rls-a-${tenantA.slice(0, 8)}`],
        [tenantB, `b4-rls-b-${tenantB.slice(0, 8)}`]
      ]) {
        await current.adminPool.query(
          `
            INSERT INTO core001.tenants (
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
              $1, 'TEST', 'TEST', $2, $3, 'ACTIVE',
              'TEST', 'TEST', '{}'::jsonb, 1, $4, $4
            )
          `,
          [
            tenantId,
            slug,
            slug,
            now
          ]
        );
      }

      const leadInsert = `
        INSERT INTO core003.leads (
          lead_id,
          tenant_id,
          customer_id,
          status,
          priority,
          source_type,
          metadata,
          revision,
          created_at,
          updated_at
        )
        VALUES (
          $1, $2, $3, 'NEW', 'NORMAL',
          'B4_RLS_TEST', '{}'::jsonb, 1, $4, $4
        )
      `;

      await current.adminPool.query(leadInsert, [
        leadA,
        tenantA,
        customerA,
        now
      ]);

      await current.adminPool.query(leadInsert, [
        leadB,
        tenantB,
        customerB,
        now
      ]);

      const visibleToA =
        await current.runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            transaction.query<LeadRow>(
              `
                SELECT tenant_id, lead_id
                FROM core003.leads
                WHERE tenant_id = ANY($1::uuid[])
                ORDER BY lead_id
              `,
              [[tenantA, tenantB]]
            )
        );

      expect(visibleToA.rows).toEqual([
        {
          tenant_id: tenantA,
          lead_id: leadA
        }
      ]);

      const visibleToB =
        await current.runtime.withTenantTransaction(
          { tenantId: tenantB },
          (transaction) =>
            transaction.query<LeadRow>(
              `
                SELECT tenant_id, lead_id
                FROM core003.leads
                WHERE tenant_id = ANY($1::uuid[])
                ORDER BY lead_id
              `,
              [[tenantA, tenantB]]
            )
        );

      expect(visibleToB.rows).toEqual([
        {
          tenant_id: tenantB,
          lead_id: leadB
        }
      ]);

      await expect(
        current.runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            transaction.query(
              leadInsert,
              [
                randomUUID(),
                tenantB,
                randomUUID(),
                now
              ]
            )
        )
      ).rejects.toMatchObject({
        code: "42501"
      });
    });
  }
);
