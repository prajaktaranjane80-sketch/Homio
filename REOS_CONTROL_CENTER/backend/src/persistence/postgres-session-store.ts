import { createHash, randomUUID } from "node:crypto";

import type {
  TrustedRequestContext,
  VerifiedExternalPrincipal
} from "../security/contracts.js";
import type { PostgresRuntime } from "./postgres.js";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const REASON_CODE_PATTERN = /^[A-Z][A-Z0-9_]{0,63}$/;

type VerifiedSessionPrincipal = Pick<
  VerifiedExternalPrincipal,
  "issuer" | "tokenId"
> & {
  readonly issuedAtEpochSeconds: number;
  readonly expiresAtEpochSeconds: number;
};

export class PostgresSessionUnavailableError extends Error {
  public constructor(cause?: unknown) {
    super(
      "The durable API session store is unavailable.",
      cause === undefined ? undefined : { cause }
    );
    this.name = "PostgresSessionUnavailableError";
  }
}

export class PostgresSessionConflictError extends Error {
  public constructor() {
    super("The verified token session is already registered.");
    this.name = "PostgresSessionConflictError";
  }
}

export interface EstablishPostgresSessionInput {
  readonly principal: VerifiedExternalPrincipal;
  readonly context: TrustedRequestContext;
}

export class PostgresSessionStore {
  private readonly postgres: PostgresRuntime;

  public constructor(postgres: PostgresRuntime) {
    if (
      typeof postgres !== "object" ||
      postgres === null ||
      typeof postgres.withTenantTransaction !== "function"
    ) {
      throw new TypeError("The canonical PostgresRuntime is required.");
    }

    this.postgres = postgres;
  }

  public async establishSession(
    input: EstablishPostgresSessionInput
  ): Promise<string> {
    const context = validateTrustedContext(input?.context);
    const principal = validatePrincipal(input?.principal);
    const issuedAt = epochSecondsToTimestamp(
      principal.issuedAtEpochSeconds
    );
    const expiresAt = epochSecondsToTimestamp(
      principal.expiresAtEpochSeconds
    );

    if (
      principal.expiresAtEpochSeconds <=
      Math.floor(Date.now() / 1_000)
    ) {
      throw new TypeError(
        "An expired verified token cannot establish a session."
      );
    }

    const sessionId = randomUUID();

    try {
      const inserted = await this.postgres.withTenantTransaction(
        { tenantId: context.tenantId },
        (transaction) => transaction.query<{ session_id: string }>(
          `INSERT INTO reos_infra.api_sessions (
             session_id,
             tenant_id,
             account_id,
             identity_id,
             tenant_revision,
             organization_id,
             membership_id,
             membership_revision,
             issuer_digest,
             token_id_digest,
             authentication_epoch,
             issued_at,
             expires_at
           )
           VALUES (
             $1, $2, $3, $4, $5, $6, $7, $8,
             $9, $10, $11, $12, $13
           )
           ON CONFLICT (tenant_id, issuer_digest, token_id_digest)
           DO NOTHING
           RETURNING session_id`,
          [
            sessionId,
            context.tenantId,
            context.accountId,
            context.identityId,
            context.tenantRevision,
            context.organizationId,
            context.membershipId,
            context.membershipRevision,
            digest(principal.issuer),
            digest(principal.tokenId),
            context.authenticationEpoch,
            issuedAt,
            expiresAt
          ]
        )
      );

      if (inserted.rows.length !== 1) {
        throw new PostgresSessionConflictError();
      }

      return inserted.rows[0]?.session_id ?? sessionId;
    } catch (error) {
      if (error instanceof PostgresSessionConflictError) {
        throw error;
      }

      throw new PostgresSessionUnavailableError(error);
    }
  }

  public async isSessionActive(input: {
    readonly principal: VerifiedExternalPrincipal;
    readonly context: TrustedRequestContext;
  }): Promise<boolean> {
    const context = validateTrustedContext(input?.context);
    const principal = validatePrincipal(input?.principal);

    try {
      const result = await this.postgres.withTenantTransaction(
        { tenantId: context.tenantId },
        (transaction) => transaction.query<{ session_id: string }>(
          `SELECT session_id
             FROM reos_infra.api_sessions
            WHERE tenant_id = $1
              AND account_id = $2
              AND identity_id = $3
              AND tenant_revision = $4
              AND organization_id = $5
              AND membership_id = $6
              AND membership_revision = $7
              AND issuer_digest = $8
              AND token_id_digest = $9
              AND authentication_epoch = $10
              AND issued_at = $11
              AND expires_at = $12
              AND issued_at <= clock_timestamp()
              AND expires_at > clock_timestamp()
              AND revoked_at IS NULL
            LIMIT 1`,
          [
            context.tenantId,
            context.accountId,
            context.identityId,
            context.tenantRevision,
            context.organizationId,
            context.membershipId,
            context.membershipRevision,
            digest(principal.issuer),
            digest(principal.tokenId),
            context.authenticationEpoch,
            epochSecondsToTimestamp(principal.issuedAtEpochSeconds),
            epochSecondsToTimestamp(principal.expiresAtEpochSeconds)
          ]
        ),
        { readOnly: true }
      );

      return result.rows.length === 1;
    } catch (error) {
      throw new PostgresSessionUnavailableError(error);
    }
  }

  public async revokeSession(input: {
    readonly principal: VerifiedExternalPrincipal;
    readonly context: TrustedRequestContext;
    readonly reasonCode: string;
  }): Promise<boolean> {
    const context = validateTrustedContext(input?.context);
    const principal = validatePrincipal(input?.principal);
    const reasonCode = validateReasonCode(input?.reasonCode);

    try {
      const result = await this.postgres.withTenantTransaction(
        { tenantId: context.tenantId },
        (transaction) => transaction.query<{ session_id: string }>(
          `UPDATE reos_infra.api_sessions
              SET revoked_at = COALESCE(revoked_at, clock_timestamp()),
                  revocation_reason_code =
                    COALESCE(revocation_reason_code, $5)
            WHERE tenant_id = $1
              AND account_id = $2
              AND issuer_digest = $3
              AND token_id_digest = $4
          RETURNING session_id`,
          [
            context.tenantId,
            context.accountId,
            digest(principal.issuer),
            digest(principal.tokenId),
            reasonCode
          ]
        )
      );

      return result.rows.length === 1;
    } catch (error) {
      throw new PostgresSessionUnavailableError(error);
    }
  }

  public async revokeAccountSessions(input: {
    readonly context: TrustedRequestContext;
    readonly reasonCode: string;
  }): Promise<number> {
    const context = validateTrustedContext(input?.context);
    const reasonCode = validateReasonCode(input?.reasonCode);

    try {
      const result = await this.postgres.withTenantTransaction(
        { tenantId: context.tenantId },
        (transaction) => transaction.query<{ session_id: string }>(
          `UPDATE reos_infra.api_sessions
              SET revoked_at = clock_timestamp(),
                  revocation_reason_code = $3
            WHERE tenant_id = $1
              AND account_id = $2
              AND revoked_at IS NULL
          RETURNING session_id`,
          [
            context.tenantId,
            context.accountId,
            reasonCode
          ]
        )
      );

      return result.rows.length;
    } catch (error) {
      throw new PostgresSessionUnavailableError(error);
    }
  }
}

function validateTrustedContext(
  value: TrustedRequestContext | undefined
): TrustedRequestContext {
  if (typeof value !== "object" || value === null) {
    throw new TypeError(
      "A complete trusted CORE-001 account and tenant context is required."
    );
  }

  /*
   * Capture every field exactly once before validation or an asynchronous
   * transaction boundary. The frozen snapshot prevents caller mutation,
   * including mutation between validation and query execution.
   */
  const snapshot = Object.freeze({
    identityId: value.identityId,
    accountId: value.accountId,
    authenticationEpoch: value.authenticationEpoch,
    tenantId: value.tenantId,
    tenantRevision: value.tenantRevision,
    organizationId: value.organizationId,
    membershipId: value.membershipId,
    membershipRevision: value.membershipRevision
  });

  if (
    !isUuid(snapshot.identityId) ||
    !isUuid(snapshot.accountId) ||
    !isUuid(snapshot.tenantId) ||
    !isUuid(snapshot.organizationId) ||
    !isUuid(snapshot.membershipId) ||
    !isPositiveInteger(snapshot.tenantRevision) ||
    !isPositiveInteger(snapshot.membershipRevision) ||
    !isPositiveInteger(snapshot.authenticationEpoch)
  ) {
    throw new TypeError(
      "A complete trusted CORE-001 account and tenant context is required."
    );
  }

  return snapshot;
}

function validatePrincipal(
  value: VerifiedExternalPrincipal | undefined
): VerifiedSessionPrincipal {
  const candidate = value as
    | (VerifiedExternalPrincipal & Record<string, unknown>)
    | undefined;

  if (
    typeof candidate !== "object" ||
    candidate === null
  ) {
    throw new TypeError(
      "Verified issuer, token ID, iat and exp claims are required."
    );
  }

  /*
   * Retain only the verified token fields used by durable session identity.
   * These primitive values are captured before any asynchronous operation.
   */
  const issuer: unknown = candidate.issuer;
  const tokenId: unknown = candidate.tokenId;
  const issuedAtEpochSeconds: unknown =
    candidate.issuedAtEpochSeconds;
  const expiresAtEpochSeconds: unknown =
    candidate.expiresAtEpochSeconds;

  if (
    typeof issuer !== "string" ||
    issuer.length === 0 ||
    issuer.length > 2048 ||
    issuer.trim() !== issuer ||
    typeof tokenId !== "string" ||
    tokenId.length === 0 ||
    tokenId.length > 255 ||
    tokenId.trim() !== tokenId ||
    !isPositiveInteger(issuedAtEpochSeconds) ||
    !isPositiveInteger(expiresAtEpochSeconds) ||
    expiresAtEpochSeconds <= issuedAtEpochSeconds
  ) {
    throw new TypeError(
      "Verified issuer, token ID, iat and exp claims are required."
    );
  }

  let parsedIssuer: URL;

  try {
    parsedIssuer = new URL(issuer);
  } catch {
    throw new TypeError("The verified token issuer is invalid.");
  }

  if (
    parsedIssuer.protocol !== "https:" ||
    parsedIssuer.username !== "" ||
    parsedIssuer.password !== "" ||
    parsedIssuer.search !== "" ||
    parsedIssuer.hash !== ""
  ) {
    throw new TypeError("The verified token issuer is invalid.");
  }

  return Object.freeze({
    issuer,
    tokenId,
    issuedAtEpochSeconds,
    expiresAtEpochSeconds
  });
}

function epochSecondsToTimestamp(value: number): string {
  if (
    !Number.isSafeInteger(value) ||
    value <= 0 ||
    value > 8_640_000_000_000
  ) {
    throw new TypeError("Verified token time is outside the supported range.");
  }

  return new Date(value * 1_000).toISOString();
}

function validateReasonCode(value: unknown): string {
  if (
    typeof value !== "string" ||
    !REASON_CODE_PATTERN.test(value)
  ) {
    throw new TypeError("A stable uppercase session reason code is required.");
  }

  return value;
}

function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}

function isPositiveInteger(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isSafeInteger(value) &&
    value > 0
  );
}

function digest(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}
