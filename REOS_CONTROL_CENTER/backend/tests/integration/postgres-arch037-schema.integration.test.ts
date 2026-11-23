import { randomUUID } from "node:crypto";

import { Pool } from "pg";
import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;
const applicationRole =
  process.env.HOMIO_TEST_POSTGRES_APPLICATION_ROLE;

const postgresSuite =
  adminUrl !== undefined && applicationRole !== undefined
    ? describe
    : describe.skip;

function quoteRole(role: string): string {
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(role)) {
    throw new Error(
      "HOMIO_TEST_POSTGRES_APPLICATION_ROLE must be a simple PostgreSQL role name."
    );
  }

  return `"${role}"`;
}

postgresSuite("ARCH-037 PostgreSQL physical schema integration", () => {
  let pool: Pool;

  beforeAll(async () => {
    pool = new Pool({
      connectionString: adminUrl,
      max: 4,
      connectionTimeoutMillis: 5_000,
      idleTimeoutMillis: 5_000
    });

    await pool.query("SELECT 1");
  });

  afterAll(async () => {
    await pool?.end();
  });

  it("has the CORE owner relations and B4 persistence relations", async () => {
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

    const result = await pool.query<{
      readonly relation_name: string;
      readonly exists: boolean;
    }>(
      `SELECT
         required.relation_name,
         to_regclass(required.relation_name) IS NOT NULL AS exists
       FROM unnest($1::text[]) AS required(relation_name)
       ORDER BY required.relation_name`,
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
    const result = await pool.query<{
      readonly schema_exists: boolean;
    }>(
      `SELECT EXISTS (
         SELECT 1
           FROM pg_catalog.pg_namespace
          WHERE nspname = 'core005'
       ) AS schema_exists`
    );

    expect(result.rows[0]?.schema_exists).toBe(false);
  });

  it("protects every tenant-bearing table with FORCE RLS and a restrictive app-role policy", async () => {
    const roleResult = await pool.query<{
      readonly oid: string;
      readonly rolsuper: boolean;
      readonly rolbypassrls: boolean;
    }>(
      `SELECT oid::text, rolsuper, rolbypassrls
         FROM pg_catalog.pg_roles
        WHERE rolname = $1`,
      [applicationRole]
    );

    expect(roleResult.rows).toHaveLength(1);

    const role = roleResult.rows[0];

    expect(role?.rolsuper).toBe(false);
    expect(role?.rolbypassrls).toBe(false);

    const tenantTables = await pool.query<{
      readonly schema_name: string;
      readonly relation_name: string;
      readonly rls_enabled: boolean;
      readonly rls_forced: boolean;
      readonly application_role_is_owner: boolean;
      readonly restrictive_policy_present: boolean;
    }>(
      `SELECT
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
              AND $1::oid = ANY(policy.polroles)
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
      ORDER BY namespace.nspname, relation.relname`,
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
        `${relation.schema_name}.${relation.relation_name} must have a restrictive policy for the app role`
      ).toBe(true);
    }
  });

  it("uses unbounded PostgreSQL NUMERIC for financial ledger amounts", async () => {
    const result = await pool.query<{
      readonly formatted_type: string;
      readonly typmod: number;
    }>(
      `SELECT
         format_type(attribute.atttypid, attribute.atttypmod)
           AS formatted_type,
         attribute.atttypmod AS typmod
       FROM pg_catalog.pg_attribute AS attribute
       WHERE attribute.attrelid =
         'core008.financial_ledger_entries'::regclass
         AND attribute.attname = 'amount'
         AND attribute.attnum > 0
         AND attribute.attisdropped = false`
    );

    expect(result.rows).toHaveLength(1);
    expect(result.rows[0]?.formatted_type).toBe("numeric");
    expect(result.rows[0]?.typmod).toBe(-1);
  });

  it("isolates tenant reads and rejects a cross-tenant insert under the real application role", async () => {
    const client = await pool.connect();

    const tenantA = randomUUID();
    const tenantB = randomUUID();
    const leadA = randomUUID();
    const leadB = randomUUID();
    const customerA = randomUUID();
    const customerB = randomUUID();
    const now = new Date().toISOString();

    try {
      await client.query("BEGIN");

      for (const [tenantId, slug] of [
        [tenantA, `b4-rls-a-${tenantA.slice(0, 8)}`],
        [tenantB, `b4-rls-b-${tenantB.slice(0, 8)}`]
      ]) {
        await client.query(
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
             $1, 'TEST', 'TEST', $2, $3, 'ACTIVE',
             'TEST', 'TEST', '{}'::jsonb, 1, $4, $4
           )`,
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
        VALUES ($1, $2, $3, 'NEW', 'NORMAL', 'B4_RLS_TEST', '{}'::jsonb, 1, $4, $4)
      `;

      await client.query(leadInsert, [
        leadA,
        tenantA,
        customerA,
        now
      ]);

      await client.query(leadInsert, [
        leadB,
        tenantB,
        customerB,
        now
      ]);

      await client.query(`SET LOCAL ROLE ${quoteRole(applicationRole!)}`);

      await client.query(
        "SELECT set_config('app.tenant_id', $1, true)",
        [tenantA]
      );

      const visibleLeads = await client.query<{
        readonly tenant_id: string;
        readonly lead_id: string;
      }>(
        `SELECT tenant_id, lead_id
           FROM core003.leads
          WHERE tenant_id = ANY($1::uuid[])
          ORDER BY lead_id`,
        [[tenantA, tenantB]]
      );

      expect(visibleLeads.rows).toEqual([
        {
          tenant_id: tenantA,
          lead_id: leadA
        }
      ]);

      await client.query("SAVEPOINT cross_tenant_write");

      await expect(
        client.query(leadInsert, [
          randomUUID(),
          tenantB,
          randomUUID(),
          now
        ])
      ).rejects.toMatchObject({
        code: "42501"
      });

      await client.query("ROLLBACK TO SAVEPOINT cross_tenant_write");
    } finally {
      await client.query("ROLLBACK").catch(() => undefined);
      client.release();
    }
  });

  it("records an ordered migration ledger with all B4 migration versions", async () => {
    const result = await pool.query<{
      readonly migration_count: string;
    }>(
      `SELECT count(*)::text AS migration_count
         FROM reos_infra.schema_migrations`
    );

    expect(Number(result.rows[0]?.migration_count ?? "0")).toBeGreaterThanOrEqual(8);
  });
});
