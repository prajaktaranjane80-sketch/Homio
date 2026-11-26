
import { randomUUID } from "node:crypto";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import {
  PostgresFinancialLedgerRepository,
  type FinancialLedgerPersistenceRecord
} from "../../src/persistence/postgres-financial-ledger.js";

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

function createRecord(
  tenantId: string,
  overrides: Partial<FinancialLedgerPersistenceRecord> = {}
): FinancialLedgerPersistenceRecord {
  return {
    entryId: randomUUID(),
    tenantId,
    commissionId: `commission-${randomUUID()}`,
    entryVersion: 1,
    transactionReference: `transaction-${randomUUID()}`,
    debitAccountId: `receivable-${randomUUID()}`,
    debitAccountType: "RECEIVABLE",
    creditAccountId: `commission-${randomUUID()}`,
    creditAccountType: "COMMISSION_PAYABLE",
    amount: "123456789012345.67",
    currencyCode: "USD",
    currencyMinorUnit: 2,
    currencyRoundingMode: "ROUND_HALF_EVEN",
    entryTimestamp: new Date().toISOString(),
    sourceReference: `deal-${randomUUID()}`,
    provenanceReference: `provenance-${randomUUID()}`,
    metadata: {
      source: "B4_FINANCIAL_LEDGER_INTEGRATION",
      contractVersion: 1
    },
    ...overrides
  };
}

async function createTenant(
  database: B4PostgresTestDatabase,
  tenantId: string
): Promise<void> {
  const now = new Date().toISOString();
  const slug = `b4-financial-${tenantId.slice(0, 8)}`;

  await database.adminPool.query(
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
        $1::uuid,
        'BROKERAGE',
        'BROKER_SAAS',
        $2::text,
        $3::text,
        'PROVISIONING',
        'SHARED_LOGICAL',
        'GLOBAL_ALLOWED',
        'default',
        1,
        $4::timestamptz,
        $4::timestamptz
      )
    `,
    [tenantId, slug, slug, now]
  );
}

function insertValues(
  record: FinancialLedgerPersistenceRecord
): unknown[] {
  return [
    record.entryId,
    record.tenantId,
    record.commissionId,
    record.entryVersion,
    record.transactionReference,
    record.debitAccountId,
    record.debitAccountType,
    record.creditAccountId,
    record.creditAccountType,
    record.amount,
    record.currencyCode,
    record.currencyMinorUnit,
    record.currencyRoundingMode,
    record.entryTimestamp,
    record.sourceReference,
    record.provenanceReference,
    JSON.stringify(record.metadata ?? {})
  ];
}

const DIRECT_INSERT_SQL = `
  INSERT INTO core008.financial_ledger_entries (
    entry_id,
    tenant_id,
    commission_id,
    entry_version,
    transaction_reference,
    debit_account_id,
    debit_account_type,
    credit_account_id,
    credit_account_type,
    amount,
    currency_code,
    currency_minor_unit,
    currency_rounding_mode,
    entry_timestamp,
    source_reference,
    provenance_reference,
    metadata
  )
  VALUES (
    $1::text,
    $2::uuid,
    $3::text,
    $4::integer,
    $5::text,
    $6::text,
    $7::text,
    $8::text,
    $9::text,
    $10::numeric,
    $11::text,
    $12::smallint,
    $13::text,
    $14::timestamptz,
    $15::text,
    $16::text,
    $17::jsonb
  )
`;

postgresSuite(
  "CORE-008 financial ledger persistence through the canonical B4 PostgreSQL runtime",
  () => {
    let database: B4PostgresTestDatabase | undefined;
    let tenantA: string;
    let tenantB: string;
    let repository: PostgresFinancialLedgerRepository;

    beforeAll(async () => {
      database = await createB4PostgresTestDatabase();

      tenantA = randomUUID();
      tenantB = randomUUID();

      await createTenant(database, tenantA);
      await createTenant(database, tenantB);

      repository = new PostgresFinancialLedgerRepository(
        database.runtime
      );
    }, TEST_TIMEOUT_MS);

    afterAll(async () => {
      await database?.close();
    }, TEST_TIMEOUT_MS);

    it(
      "round-trips a high-precision decimal and its currency semantics without floating-point conversion",
      async () => {
        const target = requireDatabase(database);
        const record = createRecord(tenantA);

        const inserted = await repository.append(
          { tenantId: tenantA },
          record
        );

        expect(inserted.amount).toBe("123456789012345.67");
        expect(inserted.currencyCode).toBe("USD");
        expect(inserted.currencyMinorUnit).toBe(2);
        expect(inserted.currencyRoundingMode).toBe(
          "ROUND_HALF_EVEN"
        );

        const reloaded = await repository.get(
          { tenantId: tenantA },
          {
            entryId: record.entryId,
            entryVersion: record.entryVersion
          }
        );

        expect(reloaded).not.toBeNull();
        expect(reloaded?.amount).toBe("123456789012345.67");
        expect(reloaded?.commissionId).toBe(record.commissionId);
        expect(reloaded?.debitAccountId).toBe(
          record.debitAccountId
        );
        expect(reloaded?.creditAccountId).toBe(
          record.creditAccountId
        );
        expect(reloaded?.metadata).toEqual(record.metadata);

        const persisted = await target.adminPool.query<{
          readonly amount: string;
          readonly currency_code: string;
          readonly currency_minor_unit: number;
          readonly currency_rounding_mode: string;
        }>(
          `
            SELECT
              amount::text AS amount,
              currency_code,
              currency_minor_unit,
              currency_rounding_mode
            FROM core008.financial_ledger_entries
            WHERE tenant_id = $1::uuid
              AND entry_id = $2::text
              AND entry_version = $3::integer
          `,
          [tenantA, record.entryId, record.entryVersion]
        );

        expect(persisted.rows).toHaveLength(1);
        expect(persisted.rows[0]).toEqual({
          amount: "123456789012345.67",
          currency_code: "USD",
          currency_minor_unit: 2,
          currency_rounding_mode: "ROUND_HALF_EVEN"
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "rejects non-zero decimal digits beyond the currency minor-unit scale at the database boundary",
      async () => {
        const target = requireDatabase(database);
        const invalid = createRecord(tenantA, {
          amount: "19.999",
          currencyMinorUnit: 2
        });

        await expect(
          target.runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) => transaction.query(
              DIRECT_INSERT_SQL,
              insertValues(invalid)
            )
          )
        ).rejects.toMatchObject({
          code: "23514"
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "rejects JavaScript floating-point amounts and tenant-context mismatches before SQL execution",
      async () => {
        const target = requireDatabase(database);
        const record = createRecord(tenantA);

        await expect(
          repository.append(
            { tenantId: tenantA },
            {
              ...record,
              amount: 19.99 as unknown as string
            }
          )
        ).rejects.toThrow(
          "amount must be a finite decimal string"
        );

        await expect(
          repository.append(
            { tenantId: tenantB },
            record
          )
        ).rejects.toThrow(
          "differs from trusted transaction context"
        );

        const stored = await target.adminPool.query(
          `
            SELECT entry_id
            FROM core008.financial_ledger_entries
            WHERE entry_id = $1
          `,
          [record.entryId]
        );

        expect(stored.rows).toHaveLength(0);
      },
      TEST_TIMEOUT_MS
    );

    it(
      "prevents duplicate ledger identity and duplicate posting of the same entry version",
      async () => {
        const record = createRecord(tenantA);

        await repository.append(
          { tenantId: tenantA },
          record
        );

        await expect(
          repository.append(
            { tenantId: tenantA },
            record
          )
        ).rejects.toMatchObject({
          code: "23505"
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "enforces append-only ledger immutability for UPDATE and DELETE",
      async () => {
        const target = requireDatabase(database);
        const record = createRecord(tenantA);

        await repository.append(
          { tenantId: tenantA },
          record
        );

        await expect(
          target.runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) => transaction.query(
              `
                UPDATE core008.financial_ledger_entries
                SET amount = amount
                WHERE entry_id = $1
                  AND entry_version = $2
              `,
              [record.entryId, record.entryVersion]
            )
          )
        ).rejects.toMatchObject({
          code: "55000"
        });

        await expect(
          target.runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) => transaction.query(
              `
                DELETE FROM core008.financial_ledger_entries
                WHERE entry_id = $1
                  AND entry_version = $2
              `,
              [record.entryId, record.entryVersion]
            )
          )
        ).rejects.toMatchObject({
          code: "55000"
        });

        await expect(
          repository.get(
            { tenantId: tenantA },
            {
              entryId: record.entryId,
              entryVersion: record.entryVersion
            }
          )
        ).resolves.toMatchObject({
          entryId: record.entryId,
          amount: record.amount
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "isolates financial ledger reads between two tenant transaction contexts",
      async () => {
        const record = createRecord(tenantA);

        await repository.append(
          { tenantId: tenantA },
          record
        );

        await expect(
          repository.get(
            { tenantId: tenantB },
            {
              entryId: record.entryId,
              entryVersion: record.entryVersion
            }
          )
        ).resolves.toBeNull();

        await expect(
          repository.get(
            { tenantId: tenantA },
            {
              entryId: record.entryId,
              entryVersion: record.entryVersion
            }
          )
        ).resolves.toMatchObject({
          tenantId: tenantA,
          entryId: record.entryId
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "records reversals as new compensating entries without rewriting original financial history",
      async () => {
        const original = createRecord(tenantA);

        await repository.append(
          { tenantId: tenantA },
          original
        );

        const reversal = createRecord(tenantA, {
          commissionId: original.commissionId,
          transactionReference: `reversal-${original.transactionReference}`,
          debitAccountId: original.creditAccountId,
          debitAccountType: original.creditAccountType,
          creditAccountId: original.debitAccountId,
          creditAccountType: original.debitAccountType,
          amount: original.amount,
          currencyCode: original.currencyCode,
          currencyMinorUnit: original.currencyMinorUnit,
          currencyRoundingMode: original.currencyRoundingMode,
          metadata: {
            reversal: true,
            reversalOfEntryId: original.entryId
          }
        });

        await repository.append(
          { tenantId: tenantA },
          reversal
        );

        const [originalReloaded, reversalReloaded] = await Promise.all([
          repository.get(
            { tenantId: tenantA },
            {
              entryId: original.entryId,
              entryVersion: original.entryVersion
            }
          ),
          repository.get(
            { tenantId: tenantA },
            {
              entryId: reversal.entryId,
              entryVersion: reversal.entryVersion
            }
          )
        ]);

        expect(originalReloaded).toMatchObject({
          entryId: original.entryId,
          debitAccountId: original.debitAccountId,
          creditAccountId: original.creditAccountId,
          amount: original.amount
        });

        expect(reversalReloaded).toMatchObject({
          entryId: reversal.entryId,
          debitAccountId: original.creditAccountId,
          creditAccountId: original.debitAccountId,
          amount: original.amount,
          metadata: {
            reversal: true,
            reversalOfEntryId: original.entryId
          }
        });
      },
      TEST_TIMEOUT_MS
    );

    it(
      "serializes concurrent ledger inserts safely and allows only one winner for a duplicate identity",
      async () => {
        const target = requireDatabase(database);

        const concurrentEntries = Array.from(
          { length: 12 },
          () => createRecord(tenantA)
        );

        const concurrentResults = await Promise.all(
          concurrentEntries.map((record) =>
            repository.append(
              { tenantId: tenantA },
              record
            )
          )
        );

        expect(concurrentResults).toHaveLength(12);

        const concurrentIds = concurrentEntries.map(
          (record) => record.entryId
        );

        const persisted = await target.adminPool.query<{
          readonly entry_id: string;
        }>(
          `
            SELECT entry_id
            FROM core008.financial_ledger_entries
            WHERE tenant_id = $1::uuid
              AND entry_id = ANY($2::text[])
          `,
          [tenantA, concurrentIds]
        );

        expect(persisted.rows).toHaveLength(12);

        const duplicate = createRecord(tenantA);
        const attempts = await Promise.allSettled([
          repository.append({ tenantId: tenantA }, duplicate),
          repository.append({ tenantId: tenantA }, duplicate)
        ]);

        expect(
          attempts.filter((result) => result.status === "fulfilled")
        ).toHaveLength(1);

        const rejected = attempts.filter(
          (result): result is PromiseRejectedResult =>
            result.status === "rejected"
        );

        expect(rejected).toHaveLength(1);
        expect(rejected[0]?.reason).toMatchObject({
          code: "23505"
        });
      },
      TEST_TIMEOUT_MS
    );
  }
);
