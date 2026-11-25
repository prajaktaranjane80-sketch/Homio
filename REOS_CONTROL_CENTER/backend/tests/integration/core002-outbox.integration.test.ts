import {
  createHash,
  randomUUID
} from "node:crypto";

import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it
} from "vitest";

import {
  Core002EventConflictError,
  PostgresCore002EventOutboxRepository
} from "../../src/persistence/postgres-core002-outbox.js";

import type {
  Core002OutboxContract
} from "../../src/persistence/postgres-core002-outbox.js";

import {
  createB4PostgresTestDatabase
} from "../helpers/postgres-b4-test-database.js";

import type {
  B4PostgresTestDatabase
} from "../helpers/postgres-b4-test-database.js";

const adminUrl = process.env.HOMIO_TEST_POSTGRES_ADMIN_URL;

const postgresRequired =
  process.env.HOMIO_REQUIRE_POSTGRES_INTEGRATION === "1";

const integrationEnabled =
  postgresRequired ||
  (
    typeof adminUrl === "string" &&
    adminUrl.length > 0
  );

const postgresSuite = integrationEnabled
  ? describe
  : describe.skip;

const TEST_TIMEOUT_MS = 60_000;

const EXPECTED_MIGRATION_IDS = Object.freeze(
  Array.from(
    { length: 11 },
    (_, index) => String(index + 1).padStart(8, "0")
  )
);

function requireDatabase(
  database: B4PostgresTestDatabase | undefined
): B4PostgresTestDatabase {
  if (database === undefined) {
    throw new Error(
      "The shared B4 PostgreSQL integration database was not initialized."
    );
  }

  return database;
}

function makeCanonicalEvent(
  tenantId: string,
  eventId: string,
  idempotencyKey: string
): {
  readonly serializedEnvelope: string;
  readonly immutableFingerprint: string;
} {
  const timestamp = new Date().toISOString();

  const envelope = {
    causation_id: null,
    correlation_id: randomUUID(),
    event_id: eventId,
    event_type: "core002.integration.probe",
    event_version: 1,
    idempotency_key: idempotencyKey,
    metadata: {},
    observed_at: timestamp,
    occurred_at: timestamp,
    ordering_key: null,
    payload: {
      marker: "postgres-integration"
    },
    producer_id: randomUUID(),
    schema_name: "homio.integration",
    schema_version: 1,
    sequence: null,
    tenant_id: tenantId,
    trace_context: null
  };

  const serializedEnvelope = JSON.stringify(envelope);

  const immutableFingerprint = createHash("sha256")
    .update(serializedEnvelope, "utf8")
    .digest("hex");

  return Object.freeze({
    serializedEnvelope,
    immutableFingerprint
  });
}

function makeContract(
  tenantId: string,
  eventId: string,
  eventFingerprint: string
): Core002OutboxContract {
  return Object.freeze({
    publicationId: randomUUID(),
    tenantId,
    eventId,
    eventFingerprint,
    createdAt: new Date(),
    state: "CREATED"
  });
}

postgresSuite(
  "CORE-002 actual PostgreSQL event and outbox persistence",
  () => {
    const tenantA = randomUUID();
    const tenantB = randomUUID();

    let database: B4PostgresTestDatabase | undefined;

    beforeAll(async () => {
      database = await createB4PostgresTestDatabase();

      const target = requireDatabase(database);

      expect(target.postgresServerVersion).toBeGreaterThanOrEqual(
        180004
      );

      expect(
        target.migrationHistory.map((migration) => migration.id)
      ).toEqual(EXPECTED_MIGRATION_IDS);

      expect(
        target.migrationHistory.every(
          (migration) =>
            /^[a-f0-9]{64}$/.test(migration.checksum)
        )
      ).toBe(true);
    }, TEST_TIMEOUT_MS);

    afterAll(async () => {
      if (database !== undefined) {
        await database.close();
        database = undefined;
      }
    }, TEST_TIMEOUT_MS);

    it(
      "enforces append, publication transitions, idempotency, tenant isolation and atomic rollback",
      async () => {
        const target = requireDatabase(database);
        const runtime = target.runtime;

        const eventId = randomUUID();
        const idempotencyKey = `integration-${randomUUID()}`;

        const event = makeCanonicalEvent(
          tenantA,
          eventId,
          idempotencyKey
        );

        const contract = makeContract(
          tenantA,
          eventId,
          event.immutableFingerprint
        );

        const inserted = await runtime.withTenantTransaction(
          { tenantId: tenantA },
          async (transaction) => {
            const repository =
              new PostgresCore002EventOutboxRepository(
                transaction
              );

            const created = await repository.appendEvent(event);

            await repository.stage(contract);
            await repository.commit(contract.publicationId);

            return created;
          }
        );

        expect(inserted).toBe(true);

        const pending = await runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).recoverUnpublished()
        );

        expect(pending).toHaveLength(1);
        expect(pending[0]?.publicationId).toBe(
          contract.publicationId
        );
        expect(pending[0]?.state).toBe("COMMITTED");

        await runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).markPublished(contract.publicationId)
        );

        const recoveredAfterPublish =
          await runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) =>
              new PostgresCore002EventOutboxRepository(
                transaction
              ).recoverUnpublished()
          );

        expect(recoveredAfterPublish).toHaveLength(0);

        const duplicate = await runtime.withTenantTransaction(
          { tenantId: tenantA },
          (transaction) =>
            new PostgresCore002EventOutboxRepository(
              transaction
            ).appendEvent(event)
        );

        expect(duplicate).toBe(false);

        const changedContent = makeCanonicalEvent(
          tenantA,
          eventId,
          idempotencyKey
        );

        await expect(
          runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) =>
              new PostgresCore002EventOutboxRepository(
                transaction
              ).appendEvent(changedContent)
          )
        ).rejects.toBeInstanceOf(Core002EventConflictError);

        const concurrentId = randomUUID();

        const concurrentEvent = makeCanonicalEvent(
          tenantA,
          concurrentId,
          `concurrent-${randomUUID()}`
        );

        const concurrentResults = await Promise.all([
          runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) =>
              new PostgresCore002EventOutboxRepository(
                transaction
              ).appendEvent(concurrentEvent)
          ),
          runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) =>
              new PostgresCore002EventOutboxRepository(
                transaction
              ).appendEvent(concurrentEvent)
          )
        ]);

        expect(
          concurrentResults.filter((value) => value === true)
        ).toHaveLength(1);

        expect(
          concurrentResults.filter((value) => value === false)
        ).toHaveLength(1);

        const rolledBackEventId = randomUUID();

        const rolledBackEvent = makeCanonicalEvent(
          tenantA,
          rolledBackEventId,
          `rollback-${randomUUID()}`
        );

        const rolledBackContract = makeContract(
          tenantA,
          rolledBackEventId,
          rolledBackEvent.immutableFingerprint
        );

        await expect(
          runtime.withTenantTransaction(
            { tenantId: tenantA },
            async (transaction) => {
              const repository =
                new PostgresCore002EventOutboxRepository(
                  transaction
                );

              await repository.appendEvent(rolledBackEvent);
              await repository.stage(rolledBackContract);
              await repository.commit(
                rolledBackContract.publicationId
              );

              throw new Error("intentional aggregate rollback");
            }
          )
        ).rejects.toThrow("intentional aggregate rollback");

        const rolledBackCount =
          await runtime.withTenantTransaction(
            { tenantId: tenantA },
            async (transaction) => {
              const result = await transaction.query<{
                count: number;
              }>(
                `
                  SELECT count(*)::integer AS count
                  FROM core002.events
                  WHERE tenant_id = $1
                    AND event_id = $2
                `,
                [tenantA, rolledBackEventId]
              );

              return Number(result.rows[0]?.count ?? 0);
            }
          );

        expect(rolledBackCount).toBe(0);

        const visibleToTenantB =
          await runtime.withTenantTransaction(
            { tenantId: tenantB },
            async (transaction) => {
              const result = await transaction.query<{
                count: number;
              }>(
                `
                  SELECT count(*)::integer AS count
                  FROM core002.events
                  WHERE tenant_id = $1
                `,
                [tenantA]
              );

              return Number(result.rows[0]?.count ?? 0);
            }
          );

        expect(visibleToTenantB).toBe(0);

        const noContext = await target.applicationPool.query<{
          count: number;
        }>(
          `
            SELECT count(*)::integer AS count
            FROM core002.events
          `
        );

        expect(
          Number(noContext.rows[0]?.count ?? 0)
        ).toBe(0);

        const invalidContextClient =
          await target.applicationPool.connect();

        try {
          for (const invalidTenantId of ["", "not-a-uuid"]) {
            await invalidContextClient.query("BEGIN");

            try {
              await invalidContextClient.query(
                "SELECT set_config('app.tenant_id', $1, true)",
                [invalidTenantId]
              );

              const invalidContextResult =
                await invalidContextClient.query<{
                  event_count: number;
                  outbox_count: number;
                }>(
                  `
                    SELECT
                      (
                        SELECT count(*)::integer
                        FROM core002.events
                      ) AS event_count,
                      (
                        SELECT count(*)::integer
                        FROM core002.outbox_publications
                      ) AS outbox_count
                  `
                );

              expect(
                Number(
                  invalidContextResult.rows[0]?.event_count ?? 0
                )
              ).toBe(0);

              expect(
                Number(
                  invalidContextResult.rows[0]?.outbox_count ?? 0
                )
              ).toBe(0);
            } finally {
              await invalidContextClient.query("ROLLBACK");
            }
          }
        } finally {
          invalidContextClient.release();
        }

        const crossTenantEvent = makeCanonicalEvent(
          tenantB,
          randomUUID(),
          `cross-tenant-${randomUUID()}`
        );

        const crossTenantEventId = (
          JSON.parse(crossTenantEvent.serializedEnvelope) as {
            event_id: string;
          }
        ).event_id;

        await expect(
          runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) =>
              new PostgresCore002EventOutboxRepository(
                transaction
              ).appendEvent(crossTenantEvent)
          )
        ).rejects.toThrow(
          /event tenant does not match the PostgreSQL transaction tenant/i
        );

        await expect(
          runtime.withTenantTransaction(
            { tenantId: tenantA },
            (transaction) =>
              transaction.query(
                `
                  INSERT INTO core002.events (
                    tenant_id,
                    event_id,
                    envelope,
                    immutable_fingerprint
                  )
                  VALUES ($1, $2, $3::jsonb, $4)
                `,
                [
                  tenantB,
                  crossTenantEventId,
                  crossTenantEvent.serializedEnvelope,
                  crossTenantEvent.immutableFingerprint
                ]
              )
          )
        ).rejects.toThrow();
      },
      TEST_TIMEOUT_MS
    );
  }
);
