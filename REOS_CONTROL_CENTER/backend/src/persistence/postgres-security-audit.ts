import { randomUUID } from "node:crypto";

import type { SecurityAuditEvent } from "../security/contracts.js";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const REASON_CODE_PATTERN = /^[A-Z][A-Z0-9_]{0,63}$/;
const OPERATION_PATTERN = /^[a-z][a-z0-9_.:-]{0,63}$/;

const EVENT_TYPES = new Set<SecurityAuditEvent["eventType"]>([
  "API_ACCESS_ALLOWED",
  "API_ACCESS_DENIED",
  "API_RATE_LIMITED",
  "API_MUTATION_REAUTHORIZED"
]);

export interface PostgresSecurityAuditQueryResult {
  readonly rowCount: number | null;
}

export interface PostgresSecurityAuditQueryPort {
  query(
    text: string,
    values?: unknown[]
  ): Promise<PostgresSecurityAuditQueryResult>;
}

export class PostgresSecurityAuditUnavailableError extends Error {
  public constructor(cause?: unknown) {
    super(
      "The append-only API security audit store is unavailable.",
      cause === undefined ? undefined : { cause }
    );
    this.name = "PostgresSecurityAuditUnavailableError";
  }
}

export class PostgresSecurityAuditStore {
  private readonly pool: PostgresSecurityAuditQueryPort;

  public constructor(pool: PostgresSecurityAuditQueryPort) {
    if (
      typeof pool !== "object" ||
      pool === null ||
      typeof pool.query !== "function"
    ) {
      throw new TypeError("The canonical PostgreSQL pool query port is required.");
    }

    this.pool = pool;
  }

  public async record(event: SecurityAuditEvent): Promise<void> {
    const normalized = validateAuditEvent(event);

    try {
      const result = await this.pool.query(
        `INSERT INTO reos_infra.security_audit_events (
           event_id,
           event_type,
           request_id,
           occurred_at,
           reason_code,
           operation,
           actor_identity_reference,
           tenant_reference
         )
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [
          randomUUID(),
          normalized.eventType,
          normalized.requestId,
          normalized.occurredAt,
          normalized.reasonCode,
          normalized.operation,
          normalized.actorIdentityId,
          normalized.tenantId
        ]
      );

      if (result.rowCount !== 1) {
        throw new Error("The audit insert did not affect exactly one row.");
      }
    } catch (error) {
      throw new PostgresSecurityAuditUnavailableError(error);
    }
  }
}

function validateAuditEvent(
  value: SecurityAuditEvent
): {
  readonly eventType: SecurityAuditEvent["eventType"];
  readonly requestId: string;
  readonly occurredAt: string;
  readonly reasonCode: string;
  readonly operation: string | null;
  readonly actorIdentityId: string | null;
  readonly tenantId: string | null;
} {
  if (
    typeof value !== "object" ||
    value === null ||
    !EVENT_TYPES.has(value.eventType) ||
    !isUuid(value.requestId) ||
    typeof value.reasonCode !== "string" ||
    !REASON_CODE_PATTERN.test(value.reasonCode)
  ) {
    throw new TypeError("The API security audit event is invalid.");
  }

  const occurredAt = normalizeTimestamp(value.occurredAt);
  const operation = value.operation ?? null;
  const actorIdentityId = value.actorIdentityId ?? null;
  const tenantId = value.tenantId ?? null;

  if (
    operation !== null &&
    (
      typeof operation !== "string" ||
      !OPERATION_PATTERN.test(operation)
    )
  ) {
    throw new TypeError("The API security audit operation is invalid.");
  }

  if (
    actorIdentityId !== null &&
    !isUuid(actorIdentityId)
  ) {
    throw new TypeError("The API security audit actor reference is invalid.");
  }

  if (
    tenantId !== null &&
    !isUuid(tenantId)
  ) {
    throw new TypeError("The API security audit tenant reference is invalid.");
  }

  return Object.freeze({
    eventType: value.eventType,
    requestId: value.requestId.toLowerCase(),
    occurredAt,
    reasonCode: value.reasonCode,
    operation,
    actorIdentityId:
      actorIdentityId === null ? null : actorIdentityId.toLowerCase(),
    tenantId: tenantId === null ? null : tenantId.toLowerCase()
  });
}

function normalizeTimestamp(value: unknown): string {
  if (
    typeof value !== "string" ||
    !/(?:Z|[+-][0-9]{2}:[0-9]{2})$/.test(value) ||
    !Number.isFinite(Date.parse(value))
  ) {
    throw new TypeError(
      "The API security audit timestamp must be timezone-aware."
    );
  }

  return new Date(value).toISOString();
}

function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}
