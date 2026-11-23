import { createHash } from "node:crypto";

import type {
  PostgresTransaction
} from "./postgres.js";

export type Core002PublicationState =
  | "CREATED"
  | "COMMITTED"
  | "PUBLISHED"
  | "RECOVERABLE"
  | "FAILED";

export interface Core002OutboxContract {
  readonly publicationId: string;
  readonly eventId: string;
  readonly tenantId: string;
  readonly eventFingerprint: string;
  readonly createdAt: Date | string;
  readonly state: Core002PublicationState;
}

export interface AppendCanonicalEventInput {
  readonly serializedEnvelope: string;
  readonly immutableFingerprint: string;
}

interface CanonicalEnvelopeIdentity {
  readonly eventId: string;
  readonly tenantId: string;
  readonly idempotencyKey: string | null;
}

interface PublicationRow {
  readonly publication_id: unknown;
  readonly tenant_id: unknown;
  readonly event_id: unknown;
  readonly event_fingerprint: unknown;
  readonly created_at: unknown;
  readonly state: unknown;
}

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const SHA256_PATTERN = /^[a-f0-9]{64}$/;

const STATES = new Set<Core002PublicationState>([
  "CREATED",
  "COMMITTED",
  "PUBLISHED",
  "RECOVERABLE",
  "FAILED"
]);

export class Core002EventValidationError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = "Core002EventValidationError";
  }
}

export class Core002EventConflictError extends Error {
  public constructor() {
    super(
      "The CORE-002 event identity or idempotency key conflicts with persisted history."
    );
    this.name = "Core002EventConflictError";
  }
}

export class Core002PublicationConflictError extends Error {
  public constructor() {
    super(
      "The CORE-002 publication cannot make the requested state transition."
    );
    this.name = "Core002PublicationConflictError";
  }
}

function asRecord(
  value: unknown
): Record<string, unknown> | null {
  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    return null;
  }

  return value as Record<string, unknown>;
}

function normalizeUuid(
  value: unknown,
  field: string
): string {
  if (
    typeof value !== "string" ||
    !UUID_PATTERN.test(value)
  ) {
    throw new Core002EventValidationError(
      `${field} must be a canonical UUID.`
    );
  }

  return value.toLowerCase();
}

function containsControlCharacters(value: string): boolean {
  for (const character of value) {
    const codePoint = character.codePointAt(0);

    if (
      codePoint !== undefined &&
      (
        codePoint <= 0x1f ||
        (codePoint >= 0x7f && codePoint <= 0x9f)
      )
    ) {
      return true;
    }
  }

  return false;
}

function requireText(
  value: unknown,
  field: string,
  maximum: number
): string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > maximum ||
    value.trim() !== value ||
    containsControlCharacters(value)
  ) {
    throw new Core002EventValidationError(
      `${field} is invalid.`
    );
  }

  return value;
}

function requireTimestamp(
  value: unknown,
  field: string
): number {
  if (
    typeof value !== "string" ||
    !/(?:Z|[+-][0-9]{2}:[0-9]{2})$/.test(value)
  ) {
    throw new Core002EventValidationError(
      `${field} must be timezone-aware.`
    );
  }

  const timestamp = Date.parse(value);

  if (!Number.isFinite(timestamp)) {
    throw new Core002EventValidationError(
      `${field} is invalid.`
    );
  }

  return timestamp;
}

function requireObject(
  value: unknown,
  field: string
): Record<string, unknown> {
  const record = asRecord(value);

  if (record === null) {
    throw new Core002EventValidationError(
      `${field} must be a JSON object.`
    );
  }

  return record;
}

function validateCanonicalEnvelope(
  serializedEnvelope: string,
  immutableFingerprint: string
): CanonicalEnvelopeIdentity {
  if (
    typeof serializedEnvelope !== "string" ||
    serializedEnvelope.length === 0 ||
    Buffer.byteLength(serializedEnvelope, "utf8") > 1_048_576
  ) {
    throw new Core002EventValidationError(
      "The serialized CORE-002 event is empty or exceeds the 1 MiB limit."
    );
  }

  if (!SHA256_PATTERN.test(immutableFingerprint)) {
    throw new Core002EventValidationError(
      "The CORE-002 immutable fingerprint must be SHA-256."
    );
  }

  let decoded: unknown;

  try {
    decoded = JSON.parse(serializedEnvelope) as unknown;
  } catch {
    throw new Core002EventValidationError(
      "The CORE-002 event envelope is not valid JSON."
    );
  }

  const envelope = requireObject(
    decoded,
    "event envelope"
  );

  const eventId = normalizeUuid(
    envelope.event_id,
    "event_id"
  );

  const tenantId = normalizeUuid(
    envelope.tenant_id,
    "tenant_id"
  );

  normalizeUuid(envelope.producer_id, "producer_id");
  normalizeUuid(envelope.correlation_id, "correlation_id");

  if (envelope.causation_id !== null) {
    normalizeUuid(envelope.causation_id, "causation_id");
  }

  requireText(envelope.event_type, "event_type", 200);
  requireText(envelope.schema_name, "schema_name", 200);

  for (const field of ["schema_version", "event_version"]) {
    const value = envelope[field];

    if (
      typeof value !== "number" ||
      !Number.isSafeInteger(value) ||
      value < 1
    ) {
      throw new Core002EventValidationError(
        `${field} must be a positive integer.`
      );
    }
  }

  const occurredAt = requireTimestamp(
    envelope.occurred_at,
    "occurred_at"
  );

  const observedAt = requireTimestamp(
    envelope.observed_at,
    "observed_at"
  );

  if (observedAt < occurredAt) {
    throw new Core002EventValidationError(
      "observed_at cannot be earlier than occurred_at."
    );
  }

  requireObject(envelope.payload, "payload");
  requireObject(envelope.metadata, "metadata");

  if (envelope.trace_context !== null) {
    requireObject(
      envelope.trace_context,
      "trace_context"
    );
  }

  const orderingKey = envelope.ordering_key;

  if (orderingKey !== null) {
    requireText(orderingKey, "ordering_key", 255);
  }

  const sequence = envelope.sequence;

  if (
    sequence !== null &&
    (
      typeof sequence !== "number" ||
      !Number.isSafeInteger(sequence) ||
      sequence < 0
    )
  ) {
    throw new Core002EventValidationError(
      "sequence must be a non-negative integer or null."
    );
  }

  if (sequence !== null && orderingKey === null) {
    throw new Core002EventValidationError(
      "sequence requires ordering_key."
    );
  }

  let idempotencyKey: string | null = null;

  if (envelope.idempotency_key !== null) {
    idempotencyKey = requireText(
      envelope.idempotency_key,
      "idempotency_key",
      255
    );
  }

  const actualFingerprint = createHash("sha256")
    .update(serializedEnvelope, "utf8")
    .digest("hex");

  if (actualFingerprint !== immutableFingerprint) {
    throw new Core002EventValidationError(
      "The supplied fingerprint does not match the canonical serialized event."
    );
  }

  return Object.freeze({
    eventId,
    tenantId,
    idempotencyKey
  });
}

function normalizeContract(
  contract: Core002OutboxContract,
  transactionTenantId: string
): {
  publicationId: string;
  eventId: string;
  tenantId: string;
  fingerprint: string;
  createdAt: string;
} {
  if (
    typeof contract !== "object" ||
    contract === null ||
    contract.state !== "CREATED"
  ) {
    throw new Core002EventValidationError(
      "A new CORE-002 outbox publication must begin in CREATED state."
    );
  }

  const publicationId = normalizeUuid(
    contract.publicationId,
    "publication_id"
  );

  const eventId = normalizeUuid(
    contract.eventId,
    "event_id"
  );

  const tenantId = normalizeUuid(
    contract.tenantId,
    "tenant_id"
  );

  if (
    tenantId !== transactionTenantId.toLowerCase()
  ) {
    throw new Core002EventValidationError(
      "The outbox publication tenant does not match its PostgreSQL transaction."
    );
  }

  if (!SHA256_PATTERN.test(contract.eventFingerprint)) {
    throw new Core002EventValidationError(
      "The outbox event fingerprint must be SHA-256."
    );
  }

  const createdAt = contract.createdAt instanceof Date
    ? contract.createdAt
    : new Date(contract.createdAt);

  if (!Number.isFinite(createdAt.getTime())) {
    throw new Core002EventValidationError(
      "The outbox creation timestamp is invalid."
    );
  }

  return {
    publicationId,
    eventId,
    tenantId,
    fingerprint: contract.eventFingerprint,
    createdAt: createdAt.toISOString()
  };
}

/**
 * CORE-002 PostgreSQL adapter.
 *
 * It receives the existing aggregate transaction. It never acquires a pool,
 * starts a transaction, commits PostgreSQL or creates another event engine.
 * The aggregate owner must append the event, stage the publication and mark
 * it COMMITTED inside the same PostgresTransaction.
 */
export class PostgresCore002EventOutboxRepository {
  private readonly transaction: PostgresTransaction;
  private readonly tenantId: string;

  public constructor(transaction: PostgresTransaction) {
    if (
      typeof transaction !== "object" ||
      transaction === null ||
      typeof transaction.query !== "function"
    ) {
      throw new TypeError(
        "The canonical PostgreSQL transaction is required."
      );
    }

    this.tenantId = normalizeUuid(
      transaction.tenantId,
      "transaction.tenantId"
    );

    this.transaction = transaction;
  }

  /**
   * Persists the immutable CORE-002 envelope.
   *
   * Returns true when inserted, false when an identical event already exists.
   * A reused event ID or idempotency key with different content is rejected.
   */
  public async appendEvent(
    input: AppendCanonicalEventInput
  ): Promise<boolean> {
    const identity = validateCanonicalEnvelope(
      input.serializedEnvelope,
      input.immutableFingerprint
    );

    if (identity.tenantId !== this.tenantId) {
      throw new Core002EventValidationError(
        "The event tenant does not match the PostgreSQL transaction tenant."
      );
    }

    const inserted = await this.transaction.query(
      `
        INSERT INTO core002.events (
          tenant_id,
          event_id,
          envelope,
          immutable_fingerprint
        )
        VALUES ($1, $2, $3::jsonb, $4)
        ON CONFLICT DO NOTHING
        RETURNING event_id
      `,
      [
        this.tenantId,
        identity.eventId,
        input.serializedEnvelope,
        input.immutableFingerprint
      ]
    );

    if (inserted.rows.length === 1) {
      return true;
    }

    const existing = await this.transaction.query<{
      event_id: string;
      immutable_fingerprint: string;
    }>(
      `
        SELECT
          event_id::text AS event_id,
          immutable_fingerprint
        FROM core002.events
        WHERE tenant_id = $1
          AND (
            event_id = $2
            OR (
              $3::text IS NOT NULL
              AND envelope->>'idempotency_key' = $3
            )
          )
        LIMIT 2
      `,
      [
        this.tenantId,
        identity.eventId,
        identity.idempotencyKey
      ]
    );

    const row = existing.rows[0];

    if (
      existing.rows.length !== 1 ||
      row === undefined ||
      row.event_id.toLowerCase() !== identity.eventId ||
      row.immutable_fingerprint !== input.immutableFingerprint
    ) {
      throw new Core002EventConflictError();
    }

    return false;
  }

  /**
   * Stages a publication for an event already appended in this transaction.
   * The foreign key binds the publication to the exact immutable fingerprint.
   */
  public async stage(
    contract: Core002OutboxContract
  ): Promise<void> {
    const normalized = normalizeContract(
      contract,
      this.tenantId
    );

    const event = await this.transaction.query<{
      immutable_fingerprint: string;
    }>(
      `
        SELECT immutable_fingerprint
        FROM core002.events
        WHERE tenant_id = $1
          AND event_id = $2
      `,
      [
        normalized.tenantId,
        normalized.eventId
      ]
    );

    if (
      event.rows.length !== 1 ||
      event.rows[0]?.immutable_fingerprint !== normalized.fingerprint
    ) {
      throw new Core002EventConflictError();
    }

    const inserted = await this.transaction.query(
      `
        INSERT INTO core002.outbox_publications (
          tenant_id,
          publication_id,
          event_id,
          event_fingerprint,
          created_at,
          state
        )
        VALUES ($1, $2, $3, $4, $5::timestamptz, 'CREATED')
        ON CONFLICT DO NOTHING
        RETURNING publication_id
      `,
      [
        normalized.tenantId,
        normalized.publicationId,
        normalized.eventId,
        normalized.fingerprint,
        normalized.createdAt
      ]
    );

    if (inserted.rows.length === 1) {
      return;
    }

    const existing = await this.readPublication(
      normalized.publicationId
    );

    if (
      existing === null ||
      existing.tenant_id !== normalized.tenantId ||
      existing.event_id !== normalized.eventId ||
      existing.event_fingerprint !== normalized.fingerprint
    ) {
      throw new Core002PublicationConflictError();
    }
  }

  /**
   * Marks the staged publication COMMITTED within the aggregate transaction.
   * This method does not execute PostgreSQL COMMIT.
   */
  public async commit(
    publicationId: string
  ): Promise<void> {
    await this.transition(
      publicationId,
      "COMMITTED",
      ["CREATED"]
    );
  }

  public async markPublished(
    publicationId: string
  ): Promise<void> {
    await this.transition(
      publicationId,
      "PUBLISHED",
      ["COMMITTED", "RECOVERABLE"]
    );
  }

  public async markRecoverable(
    publicationId: string
  ): Promise<void> {
    await this.transition(
      publicationId,
      "RECOVERABLE",
      ["COMMITTED"]
    );
  }

  public async markFailed(
    publicationId: string
  ): Promise<void> {
    await this.transition(
      publicationId,
      "FAILED",
      ["CREATED", "COMMITTED", "RECOVERABLE"]
    );
  }

  public async recoverUnpublished(): Promise<
    readonly Core002OutboxContract[]
  > {
    const result = await this.transaction.query<PublicationRow>(
      `
        SELECT
          publication_id::text AS publication_id,
          tenant_id::text AS tenant_id,
          event_id::text AS event_id,
          event_fingerprint,
          created_at,
          state
        FROM core002.outbox_publications
        WHERE tenant_id = $1
          AND state IN ('COMMITTED', 'RECOVERABLE')
        ORDER BY created_at ASC, publication_id ASC
      `,
      [this.tenantId]
    );

    return Object.freeze(
      result.rows.map((row) => this.toContract(row))
    );
  }

  private async transition(
    publicationId: string,
    target: Core002PublicationState,
    allowed: readonly Core002PublicationState[]
  ): Promise<void> {
    const id = normalizeUuid(
      publicationId,
      "publication_id"
    );

    const allowedStates = [...allowed];

    const updated = await this.transaction.query(
      `
        UPDATE core002.outbox_publications
        SET state = $3
        WHERE tenant_id = $1
          AND publication_id = $2
          AND state = ANY($4::text[])
        RETURNING publication_id
      `,
      [
        this.tenantId,
        id,
        target,
        allowedStates
      ]
    );

    if (updated.rows.length === 1) {
      return;
    }

    const existing = await this.readPublication(id);

    if (existing?.state === target) {
      return;
    }

    throw new Core002PublicationConflictError();
  }

  private async readPublication(
    publicationId: string
  ): Promise<PublicationRow | null> {
    const result = await this.transaction.query<PublicationRow>(
      `
        SELECT
          publication_id::text AS publication_id,
          tenant_id::text AS tenant_id,
          event_id::text AS event_id,
          event_fingerprint,
          created_at,
          state
        FROM core002.outbox_publications
        WHERE tenant_id = $1
          AND publication_id = $2
      `,
      [
        this.tenantId,
        publicationId
      ]
    );

    return result.rows[0] ?? null;
  }

  private toContract(
    row: PublicationRow
  ): Core002OutboxContract {
    if (
      typeof row.publication_id !== "string" ||
      typeof row.tenant_id !== "string" ||
      typeof row.event_id !== "string" ||
      typeof row.event_fingerprint !== "string" ||
      !(row.created_at instanceof Date) ||
      typeof row.state !== "string" ||
      !STATES.has(row.state as Core002PublicationState)
    ) {
      throw new Core002EventValidationError(
        "The persisted CORE-002 outbox row is malformed."
      );
    }

    return Object.freeze({
      publicationId: row.publication_id,
      tenantId: row.tenant_id,
      eventId: row.event_id,
      eventFingerprint: row.event_fingerprint,
      createdAt: row.created_at,
      state: row.state as Core002PublicationState
    });
  }
}
