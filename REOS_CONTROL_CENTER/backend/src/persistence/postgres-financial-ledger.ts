
import type {
  PostgresRuntime,
  PostgresTenantContext
} from "./postgres.js";

export type FinancialLedgerRoundingMode =
  | "ROUND_CEILING"
  | "ROUND_DOWN"
  | "ROUND_FLOOR"
  | "ROUND_HALF_DOWN"
  | "ROUND_HALF_EVEN"
  | "ROUND_HALF_UP"
  | "ROUND_UP";

export interface FinancialLedgerPersistenceRecord {
  readonly entryId: string;
  readonly tenantId: string;
  readonly commissionId: string;
  readonly entryVersion: number;
  readonly transactionReference: string;
  readonly debitAccountId: string;
  readonly debitAccountType: string;
  readonly creditAccountId: string;
  readonly creditAccountType: string;
  readonly amount: string;
  readonly currencyCode: string;
  readonly currencyMinorUnit: number;
  readonly currencyRoundingMode: FinancialLedgerRoundingMode;
  readonly entryTimestamp: string;
  readonly sourceReference: string;
  readonly provenanceReference: string;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface FinancialLedgerIdentity {
  readonly entryId: string;
  readonly entryVersion: number;
}

interface FinancialLedgerRow extends Record<string, unknown> {
  readonly entry_id: string;
  readonly tenant_id: string;
  readonly commission_id: string;
  readonly entry_version: number;
  readonly transaction_reference: string;
  readonly debit_account_id: string;
  readonly debit_account_type: string;
  readonly credit_account_id: string;
  readonly credit_account_type: string;
  readonly amount: string;
  readonly currency_code: string;
  readonly currency_minor_unit: number;
  readonly currency_rounding_mode: FinancialLedgerRoundingMode;
  readonly entry_timestamp: Date | string;
  readonly source_reference: string;
  readonly provenance_reference: string;
  readonly metadata: Record<string, unknown>;
}

export class FinancialLedgerPersistenceError extends Error {
  public constructor(message: string, cause?: unknown) {
    super(message, { cause });
    this.name = "FinancialLedgerPersistenceError";
  }
}

export class FinancialLedgerPersistenceValidationError
  extends FinancialLedgerPersistenceError {
  public constructor(message: string) {
    super(message);
    this.name = "FinancialLedgerPersistenceValidationError";
  }
}

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const DECIMAL_PATTERN =
  /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;

const ROUNDING_MODES = new Set<FinancialLedgerRoundingMode>([
  "ROUND_CEILING",
  "ROUND_DOWN",
  "ROUND_FLOOR",
  "ROUND_HALF_DOWN",
  "ROUND_HALF_EVEN",
  "ROUND_HALF_UP",
  "ROUND_UP"
]);

const INSERT_SQL = `
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
  RETURNING
    entry_id,
    tenant_id,
    commission_id,
    entry_version,
    transaction_reference,
    debit_account_id,
    debit_account_type,
    credit_account_id,
    credit_account_type,
    amount::text AS amount,
    currency_code,
    currency_minor_unit,
    currency_rounding_mode,
    entry_timestamp,
    source_reference,
    provenance_reference,
    metadata
`;

const SELECT_SQL = `
  SELECT
    entry_id,
    tenant_id,
    commission_id,
    entry_version,
    transaction_reference,
    debit_account_id,
    debit_account_type,
    credit_account_id,
    credit_account_type,
    amount::text AS amount,
    currency_code,
    currency_minor_unit,
    currency_rounding_mode,
    entry_timestamp,
    source_reference,
    provenance_reference,
    metadata
  FROM core008.financial_ledger_entries
  WHERE entry_id = $1::text
    AND entry_version = $2::integer
`;

function requireText(value: unknown, field: string): string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.trim() !== value
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      `${field} must be a non-empty trimmed string.`
    );
  }

  return value;
}

function requirePositiveInteger(
  value: unknown,
  field: string
): number {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < 1
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      `${field} must be a positive safe integer.`
    );
  }

  return value;
}

function requireCurrencyMinorUnit(value: unknown): number {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < 0 ||
    value > 6
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "currencyMinorUnit must be an integer from 0 through 6."
    );
  }

  return value;
}

function requireExactDecimal(
  value: unknown,
  minorUnit: number
): string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > 1_100 ||
    !DECIMAL_PATTERN.test(value)
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "amount must be a finite decimal string; JavaScript numbers are forbidden."
    );
  }

  const unsigned = value.startsWith("-")
    ? value.slice(1)
    : value;

  const [whole = "", fraction = ""] = unsigned.split(".");

  if (whole.length > 1_000) {
    throw new FinancialLedgerPersistenceValidationError(
      "amount exceeds the supported PostgreSQL numeric integer width."
    );
  }

  if (
    fraction.length > minorUnit &&
    /[1-9]/.test(fraction.slice(minorUnit))
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "amount contains non-zero digits beyond the currency minor-unit scale."
    );
  }

  if (Number.isNaN(Number.parseInt(whole, 10)) && !/^0+$/.test(whole)) {
    throw new FinancialLedgerPersistenceValidationError(
      "amount has an invalid integer component."
    );
  }

  if (value.startsWith("-") || /^0(?:\.0+)?$/.test(value)) {
    throw new FinancialLedgerPersistenceValidationError(
      "financial ledger amount must be greater than zero."
    );
  }

  return value;
}

function requireTimestamp(value: unknown): string {
  if (
    typeof value !== "string" ||
    !/T.*(?:Z|[+-][0-9]{2}:[0-9]{2})$/i.test(value) ||
    !Number.isFinite(Date.parse(value))
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "entryTimestamp must be a valid ISO-8601 timestamp with an explicit timezone."
    );
  }

  return value;
}

function normalizeMetadata(
  value: unknown
): Readonly<Record<string, unknown>> {
  if (
    value === undefined ||
    value === null
  ) {
    return Object.freeze({});
  }

  if (
    typeof value !== "object" ||
    Array.isArray(value)
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "metadata must be a JSON object."
    );
  }

  let serialized: string | undefined;

  try {
    serialized = JSON.stringify(value);
  } catch (error) {
    throw new FinancialLedgerPersistenceValidationError(
      `metadata is not JSON serializable: ${error instanceof Error ? error.message : "unknown error"}`
    );
  }

  if (serialized === undefined) {
    throw new FinancialLedgerPersistenceValidationError(
      "metadata could not be serialized."
    );
  }

  const parsed: unknown = JSON.parse(serialized);

  if (
    typeof parsed !== "object" ||
    parsed === null ||
    Array.isArray(parsed)
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "metadata must serialize to a JSON object."
    );
  }

  return Object.freeze(parsed as Record<string, unknown>);
}

function normalizeRecord(
  context: PostgresTenantContext,
  input: FinancialLedgerPersistenceRecord
): FinancialLedgerPersistenceRecord {
  if (
    typeof input !== "object" ||
    input === null ||
    Array.isArray(input)
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "A financial ledger persistence record is required."
    );
  }

  const tenantId = requireText(input.tenantId, "tenantId");
  const trustedTenantId = requireText(
    context?.tenantId,
    "trusted tenant context"
  );

  if (
    !UUID_PATTERN.test(tenantId) ||
    !UUID_PATTERN.test(trustedTenantId)
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "Financial ledger tenant identifiers must be canonical UUIDs."
    );
  }

  if (tenantId.toLowerCase() !== trustedTenantId.toLowerCase()) {
    throw new FinancialLedgerPersistenceValidationError(
      "Financial ledger record tenant differs from trusted transaction context."
    );
  }

  const currencyMinorUnit = requireCurrencyMinorUnit(
    input.currencyMinorUnit
  );

  const currencyCode = requireText(
    input.currencyCode,
    "currencyCode"
  );

  if (!/^[A-Z]{3}$/.test(currencyCode)) {
    throw new FinancialLedgerPersistenceValidationError(
      "currencyCode must be three uppercase ASCII letters."
    );
  }

  const roundingMode = input.currencyRoundingMode;

  if (
    typeof roundingMode !== "string" ||
    !ROUNDING_MODES.has(roundingMode)
  ) {
    throw new FinancialLedgerPersistenceValidationError(
      "currencyRoundingMode is not an approved CORE-008 rounding mode."
    );
  }

  const debitAccountId = requireText(
    input.debitAccountId,
    "debitAccountId"
  );

  const creditAccountId = requireText(
    input.creditAccountId,
    "creditAccountId"
  );

  if (debitAccountId === creditAccountId) {
    throw new FinancialLedgerPersistenceValidationError(
      "Debit and credit accounts must differ."
    );
  }

  return Object.freeze({
    entryId: requireText(input.entryId, "entryId"),
    tenantId,
    commissionId: requireText(input.commissionId, "commissionId"),
    entryVersion: requirePositiveInteger(
      input.entryVersion,
      "entryVersion"
    ),
    transactionReference: requireText(
      input.transactionReference,
      "transactionReference"
    ),
    debitAccountId,
    debitAccountType: requireText(
      input.debitAccountType,
      "debitAccountType"
    ),
    creditAccountId,
    creditAccountType: requireText(
      input.creditAccountType,
      "creditAccountType"
    ),
    amount: requireExactDecimal(input.amount, currencyMinorUnit),
    currencyCode,
    currencyMinorUnit,
    currencyRoundingMode: roundingMode,
    entryTimestamp: requireTimestamp(input.entryTimestamp),
    sourceReference: requireText(
      input.sourceReference,
      "sourceReference"
    ),
    provenanceReference: requireText(
      input.provenanceReference,
      "provenanceReference"
    ),
    metadata: normalizeMetadata(input.metadata)
  });
}

function rowToRecord(
  row: FinancialLedgerRow
): FinancialLedgerPersistenceRecord {
  const timestamp = row.entry_timestamp instanceof Date
    ? row.entry_timestamp.toISOString()
    : String(row.entry_timestamp);

  return Object.freeze({
    entryId: row.entry_id,
    tenantId: row.tenant_id,
    commissionId: row.commission_id,
    entryVersion: Number(row.entry_version),
    transactionReference: row.transaction_reference,
    debitAccountId: row.debit_account_id,
    debitAccountType: row.debit_account_type,
    creditAccountId: row.credit_account_id,
    creditAccountType: row.credit_account_type,
    amount: row.amount,
    currencyCode: row.currency_code,
    currencyMinorUnit: Number(row.currency_minor_unit),
    currencyRoundingMode: row.currency_rounding_mode,
    entryTimestamp: timestamp,
    sourceReference: row.source_reference,
    provenanceReference: row.provenance_reference,
    metadata: normalizeMetadata(row.metadata)
  });
}

/**
 * CORE-008 financial ledger persistence adapter.
 *
 * This adapter is deliberately limited to persistence:
 * - CORE-008 remains the domain and financial lifecycle authority.
 * - PostgresRuntime remains the only PostgreSQL transaction owner.
 * - PostgreSQL constraints remain the durable uniqueness and append-only boundary.
 * - Amounts are decimal strings; JavaScript floating-point numbers are rejected.
 * - Every read and write uses an explicitly supplied trusted tenant context.
 */
export class PostgresFinancialLedgerRepository {
  public constructor(
    private readonly runtime: PostgresRuntime
  ) {
    if (
      typeof runtime !== "object" ||
      runtime === null ||
      typeof runtime.withTenantTransaction !== "function"
    ) {
      throw new TypeError(
        "The canonical PostgresRuntime is required."
      );
    }
  }

  public async append(
    context: PostgresTenantContext,
    input: FinancialLedgerPersistenceRecord
  ): Promise<FinancialLedgerPersistenceRecord> {
    const record = normalizeRecord(context, input);

    return this.runtime.withTenantTransaction(
      { tenantId: record.tenantId },
      async (transaction) => {
        const result = await transaction.query<FinancialLedgerRow>(
          INSERT_SQL,
          [
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
            JSON.stringify(record.metadata)
          ]
        );

        const row = result.rows[0];

        if (row === undefined) {
          throw new FinancialLedgerPersistenceError(
            "PostgreSQL did not return the inserted financial ledger entry."
          );
        }

        return rowToRecord(row);
      }
    );
  }

  public async get(
    context: PostgresTenantContext,
    identity: FinancialLedgerIdentity
  ): Promise<FinancialLedgerPersistenceRecord | null> {
    const tenantId = requireText(
      context?.tenantId,
      "trusted tenant context"
    );

    if (!UUID_PATTERN.test(tenantId)) {
      throw new FinancialLedgerPersistenceValidationError(
        "Financial ledger tenant identifier must be a canonical UUID."
      );
    }

    const entryId = requireText(identity?.entryId, "entryId");
    const entryVersion = requirePositiveInteger(
      identity?.entryVersion,
      "entryVersion"
    );

    return this.runtime.withTenantTransaction(
      { tenantId },
      async (transaction) => {
        const result = await transaction.query<FinancialLedgerRow>(
          SELECT_SQL,
          [entryId, entryVersion]
        );

        const row = result.rows[0];

        return row === undefined
          ? null
          : rowToRecord(row);
      },
      { readOnly: true }
    );
  }
}
