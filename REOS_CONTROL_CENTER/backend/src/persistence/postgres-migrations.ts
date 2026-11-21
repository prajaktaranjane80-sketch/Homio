import { createHash } from "node:crypto";

import type {
  PostgresDriverClient,
  PostgresDriverPool
} from "./postgres.js";

export interface PostgresMigration {
  readonly id: string;
  readonly name: string;
  readonly sql: string;
}

export interface ValidatedPostgresMigration extends PostgresMigration {
  readonly checksum: string;
}

export interface PostgresMigrationReport {
  readonly appliedCount: number;
  readonly latestMigrationId: string;
  readonly latestChecksum: string;
}

export type PostgresMigrationErrorCode =
  | "INVALID_MANIFEST"
  | "CONNECTION_UNAVAILABLE"
  | "MIGRATION_ROLE_UNAVAILABLE"
  | "MIGRATION_ROLE_MISMATCH"
  | "MIGRATION_SERVER_VERSION_UNSUPPORTED"
  | "MIGRATION_LOCK_UNAVAILABLE"
  | "MIGRATION_LOCK_RELEASE_FAILED"
  | "MIGRATION_METADATA_INVALID"
  | "MIGRATION_METADATA_READ_FAILED"
  | "MIGRATION_HISTORY_READ_FAILED"
  | "MIGRATION_HISTORY_CORRUPT"
  | "MIGRATION_HISTORY_DRIFT"
  | "MIGRATION_EXECUTION_FAILED"
  | "MIGRATION_OUTCOME_UNKNOWN"
  | "MIGRATION_ROLLBACK_FAILED";

export class PostgresMigrationError extends Error {
  public readonly code: PostgresMigrationErrorCode;
  public readonly migrationId?: string;

  public constructor(
    code: PostgresMigrationErrorCode,
    message: string,
    options: {
      readonly cause?: unknown;
      readonly migrationId?: string;
    } = {}
  ) {
    super(
      message,
      options.cause === undefined ? undefined : { cause: options.cause }
    );

    this.name = "PostgresMigrationError";
    this.code = code;

    if (options.migrationId !== undefined) {
      this.migrationId = options.migrationId;
    }
  }
}

const MIGRATION_ID_PATTERN = /^[0-9]{8}$/;
const MIGRATION_NAME_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const SHA256_PATTERN = /^[a-f0-9]{64}$/;

const MIGRATION_LOCK_NAMESPACE = 0x484f4d49;
const MIGRATION_LOCK_RESOURCE = 1;
const MINIMUM_POSTGRES_SERVER_VERSION_NUM = 180004;

export interface PostgresMigrationRunnerOptions {
  readonly migrationRole: string;
  readonly applicationRole: string;
}

const EXPECTED_MIGRATION_CHECK_EXPRESSIONS: ReadonlySet<string> =
  new Set([
    "migration_id~'^[0-9]{8}$'",
    "migration_name~'^[a-z][a-z0-9]*(-[a-z0-9]+)*$'",
    "checksum~'^[a-f0-9]{64}$'"
  ]);

export const POSTGRES_MIGRATION_RUNTIME_SQL = `
SELECT
  session_user::text AS session_user,
  current_user::text AS current_user,
  current_setting('server_version_num')::integer AS server_version_num
`.trim();

export const POSTGRES_MIGRATION_LOCK_SQL =
  "SELECT pg_try_advisory_lock($1, $2) AS acquired";

export const POSTGRES_MIGRATION_UNLOCK_SQL =
  "SELECT pg_advisory_unlock($1, $2) AS unlocked";

/**
 * The infrastructure ledger must be pre-provisioned by the approved schema owner
 * and is owned by the dedicated migration role. This runner never creates it.
 * The API role must not be able to read, modify, truncate or maintain it,
 * and must not be able to create objects in its schema.
 *
 * $1 is the configured API role and is always passed as a bound parameter.
 */
export const POSTGRES_MIGRATION_VERIFY_SQL = `
SELECT
  pg_get_userbyid(namespace.nspowner) AS schema_owner,
  pg_get_userbyid(relation.relowner) AS table_owner,

  ARRAY(
    SELECT
      column_name::text || ':' ||
      data_type::text || ':' ||
      is_nullable::text
    FROM information_schema.columns
    WHERE table_schema = 'reos_infra'
      AND table_name = 'schema_migrations'
    ORDER BY ordinal_position
  ) AS columns,

  (
    SELECT pg_get_constraintdef(constraint_row.oid)
    FROM pg_constraint AS constraint_row
    WHERE constraint_row.conrelid = relation.oid
      AND constraint_row.contype = 'p'
  ) AS primary_key,

  (
    SELECT pg_get_constraintdef(constraint_row.oid)
    FROM pg_constraint AS constraint_row
    WHERE constraint_row.conrelid = relation.oid
      AND constraint_row.contype = 'u'
  ) AS unique_key,

  ARRAY(
    SELECT pg_get_expr(
      constraint_row.conbin,
      constraint_row.conrelid
    )
    FROM pg_constraint AS constraint_row
    WHERE constraint_row.conrelid = relation.oid
      AND constraint_row.contype = 'c'
    ORDER BY 1
  ) AS check_expressions,

  COALESCE(
    (
      SELECT BOOL_AND(constraint_row.convalidated)
      FROM pg_constraint AS constraint_row
      WHERE constraint_row.conrelid = relation.oid
        AND constraint_row.contype = 'c'
    ),
    false
  ) AS check_constraints_validated,

  (
    SELECT column_default
    FROM information_schema.columns
    WHERE table_schema = 'reos_infra'
      AND table_name = 'schema_migrations'
      AND column_name = 'applied_at'
  ) AS applied_at_default,

  (
    has_table_privilege($1::name, relation.oid, 'SELECT')
    OR has_table_privilege($1::name, relation.oid, 'INSERT')
    OR has_table_privilege($1::name, relation.oid, 'UPDATE')
    OR has_table_privilege($1::name, relation.oid, 'DELETE')
    OR has_table_privilege($1::name, relation.oid, 'TRUNCATE')
    OR has_table_privilege($1::name, relation.oid, 'REFERENCES')
    OR has_table_privilege($1::name, relation.oid, 'TRIGGER')
    OR has_table_privilege($1::name, relation.oid, 'MAINTAIN')
  ) AS application_role_has_table_privileges,

  has_schema_privilege(
    $1::name,
    namespace.oid,
    'CREATE'
  ) AS application_role_can_create_in_schema,

  relation.relrowsecurity AS row_security_enabled

FROM pg_namespace AS namespace
JOIN pg_class AS relation
  ON relation.relnamespace = namespace.oid
WHERE namespace.nspname = 'reos_infra'
  AND relation.relname = 'schema_migrations'
  AND relation.relkind = 'r'
`.trim();

export const POSTGRES_MIGRATION_HISTORY_SQL = `
SELECT migration_id, migration_name, checksum
FROM reos_infra.schema_migrations
ORDER BY migration_id ASC
`.trim();

export const POSTGRES_MIGRATION_INSERT_SQL = `
INSERT INTO reos_infra.schema_migrations (
  migration_id,
  migration_name,
  checksum
)
VALUES ($1, $2, $3)
`.trim();

function validateRunnerOptions(
  options: PostgresMigrationRunnerOptions
): PostgresMigrationRunnerOptions {
  if (
    typeof options !== "object" ||
    options === null ||
    typeof options.migrationRole !== "string" ||
    options.migrationRole.length === 0 ||
    options.migrationRole !== options.migrationRole.trim() ||
    typeof options.applicationRole !== "string" ||
    options.applicationRole.length === 0 ||
    options.applicationRole !== options.applicationRole.trim() ||
    options.migrationRole === options.applicationRole
  ) {
    throw new TypeError(
      "A dedicated migration role distinct from the API role is required."
    );
  }

  return Object.freeze({
    migrationRole: options.migrationRole,
    applicationRole: options.applicationRole
  });
}

function checksumSql(sql: string): string {
  return createHash("sha256").update(sql, "utf8").digest("hex");
}

export function validatePostgresMigrationManifest(
  migrations: readonly PostgresMigration[]
): readonly ValidatedPostgresMigration[] {
  if (!Array.isArray(migrations) || migrations.length === 0) {
    throw new PostgresMigrationError(
      "INVALID_MANIFEST",
      "At least one reviewed PostgreSQL migration is required."
    );
  }

  const seenIds = new Set<string>();
  const seenNames = new Set<string>();
  const validated: ValidatedPostgresMigration[] = [];
  let previousId = "";

  for (const migration of migrations) {
    if (
      typeof migration !== "object" ||
      migration === null ||
      typeof migration.id !== "string" ||
      !MIGRATION_ID_PATTERN.test(migration.id) ||
      migration.id === "00000000" ||
      typeof migration.name !== "string" ||
      migration.name.length > 96 ||
      !MIGRATION_NAME_PATTERN.test(migration.name) ||
      typeof migration.sql !== "string" ||
      migration.sql.trim().length === 0
    ) {
      throw new PostgresMigrationError(
        "INVALID_MANIFEST",
        "A migration has an invalid ID, name or empty SQL body."
      );
    }

    if (seenIds.has(migration.id) || seenNames.has(migration.name)) {
      throw new PostgresMigrationError(
        "INVALID_MANIFEST",
        "Migration IDs and names must both be unique."
      );
    }

    if (previousId !== "" && migration.id <= previousId) {
      throw new PostgresMigrationError(
        "INVALID_MANIFEST",
        "Migrations must already be in strictly increasing ID order."
      );
    }

    const normalized = Object.freeze({
      id: migration.id,
      name: migration.name,
      sql: migration.sql,
      checksum: checksumSql(migration.sql)
    });

    validated.push(normalized);
    seenIds.add(migration.id);
    seenNames.add(migration.name);
    previousId = migration.id;
  }

  return Object.freeze(validated);
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
}

function asError(value: unknown): Error {
  return value instanceof Error
    ? value
    : new Error("Unknown PostgreSQL migration failure.", { cause: value });
}

/**
 * pg_get_expr() returns SQL expressions. Remove only syntactic parentheses
 * and whitespace outside string literals. Parentheses inside regex patterns
 * must be preserved because they are part of the approved constraint.
 */
function normalizeCheckExpression(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const source = value.toLowerCase();
  let normalized = "";
  let insideString = false;

  for (let index = 0; index < source.length; index += 1) {
    const character = source.charAt(index);

    if (character === "'") {
      normalized += character;

      if (insideString && source.charAt(index + 1) === "'") {
        normalized += source.charAt(index + 1);
        index += 1;
      } else {
        insideString = !insideString;
      }

      continue;
    }

    if (
      !insideString &&
      (
        character === "(" ||
        character === ")" ||
        /\s/.test(character)
      )
    ) {
      continue;
    }

    normalized += character;
  }

  return normalized.replace(
    /::(?:pg_catalog\.)?text\b/g,
    ""
  );
}

function verifyMigrationMetadata(
  rows: readonly unknown[],
  migrationRole: string,
  applicationRole: string
): void {
  const candidate = rows.length === 1 ? rows[0] : null;
  const row = asRecord(candidate);
  const columns = row?.columns;
  const checkExpressions = row?.check_expressions;

  const normalizedChecks = Array.isArray(checkExpressions)
    ? checkExpressions.map(normalizeCheckExpression)
    : [];

  const checksMatch =
    normalizedChecks.length === EXPECTED_MIGRATION_CHECK_EXPRESSIONS.size &&
    normalizedChecks.every((value): value is string =>
      value !== null &&
      EXPECTED_MIGRATION_CHECK_EXPRESSIONS.has(value)
    ) &&
    new Set(normalizedChecks).size ===
      EXPECTED_MIGRATION_CHECK_EXPRESSIONS.size;

  const expectedColumns = [
    "migration_id:text:NO",
    "migration_name:text:NO",
    "checksum:text:NO",
    "applied_at:timestamp with time zone:NO"
  ];

  if (
    row === null ||
    row.schema_owner !== migrationRole ||
    row.table_owner !== migrationRole ||
    !Array.isArray(columns) ||
    columns.length !== expectedColumns.length ||
    !columns.every(
      (value: unknown, index: number) =>
        value === expectedColumns[index]
    ) ||
    row.primary_key !== "PRIMARY KEY (migration_id)" ||
    row.unique_key !== "UNIQUE (migration_name)" ||
    !checksMatch ||
    row.check_constraints_validated !== true ||
    row.applied_at_default !== "clock_timestamp()" ||
    row.application_role_has_table_privileges !== false ||
    row.application_role_can_create_in_schema !== false ||
    row.row_security_enabled !== false
  ) {
    throw new PostgresMigrationError(
      "MIGRATION_METADATA_INVALID",
      `The pre-provisioned migration ledger does not match the required ownership, integrity and least-privilege contract for ${migrationRole} and ${applicationRole}.`
    );
  }
}

function readHistoryRows(rows: readonly unknown[]): readonly {
  readonly migrationId: string;
  readonly migrationName: string;
  readonly checksum: string;
}[] {
  const seenNames = new Set<string>();

  const history = rows.map((value) => {
    const row = asRecord(value);

    if (
      row === null ||
      typeof row.migration_id !== "string" ||
      typeof row.migration_name !== "string" ||
      typeof row.checksum !== "string" ||
      !MIGRATION_ID_PATTERN.test(row.migration_id) ||
      !MIGRATION_NAME_PATTERN.test(row.migration_name) ||
      !SHA256_PATTERN.test(row.checksum)
    ) {
      throw new PostgresMigrationError(
        "MIGRATION_HISTORY_CORRUPT",
        "The PostgreSQL migration history contains an invalid row."
      );
    }

    if (seenNames.has(row.migration_name)) {
      throw new PostgresMigrationError(
        "MIGRATION_HISTORY_CORRUPT",
        "The PostgreSQL migration history contains a duplicate migration name."
      );
    }

    seenNames.add(row.migration_name);

    return Object.freeze({
      migrationId: row.migration_id,
      migrationName: row.migration_name,
      checksum: row.checksum
    });
  });

  for (let index = 1; index < history.length; index += 1) {
    const previous = history[index - 1];
    const current = history[index];

    if (
      previous === undefined ||
      current === undefined ||
      current.migrationId <= previous.migrationId
    ) {
      throw new PostgresMigrationError(
        "MIGRATION_HISTORY_CORRUPT",
        "The PostgreSQL migration history is not strictly ordered."
      );
    }
  }

  return Object.freeze(history);
}

function assertHistoryIsManifestPrefix(
  history: readonly {
    readonly migrationId: string;
    readonly migrationName: string;
    readonly checksum: string;
  }[],
  manifest: readonly ValidatedPostgresMigration[]
): void {
  if (history.length > manifest.length) {
    throw new PostgresMigrationError(
      "MIGRATION_HISTORY_DRIFT",
      "Applied migrations are missing from the current immutable manifest."
    );
  }

  for (let index = 0; index < history.length; index += 1) {
    const applied = history[index];
    const expected = manifest[index];

    if (applied === undefined || expected === undefined) {
      throw new PostgresMigrationError(
        "MIGRATION_HISTORY_CORRUPT",
        "Migration history does not map to the current manifest."
      );
    }

    if (
      applied.migrationId !== expected.id ||
      applied.migrationName !== expected.name ||
      applied.checksum !== expected.checksum
    ) {
      throw new PostgresMigrationError(
        "MIGRATION_HISTORY_DRIFT",
        "An applied migration was removed, renamed, reordered or modified.",
        { migrationId: expected.id }
      );
    }
  }
}

function verifyMigrationRuntime(
  rows: readonly unknown[],
  options: PostgresMigrationRunnerOptions
): void {
  const row = asRecord(rows[0]);

  if (
    row === null ||
    typeof row.session_user !== "string" ||
    typeof row.current_user !== "string" ||
    typeof row.server_version_num !== "number" ||
    !Number.isSafeInteger(row.server_version_num)
  ) {
    throw new PostgresMigrationError(
      "MIGRATION_ROLE_UNAVAILABLE",
      "PostgreSQL did not return a valid migration-role/runtime identity."
    );
  }

  if (
    row.session_user !== options.migrationRole ||
    row.current_user !== options.migrationRole ||
    row.session_user === options.applicationRole
  ) {
    throw new PostgresMigrationError(
      "MIGRATION_ROLE_MISMATCH",
      "The migration connection is not authenticated as the configured dedicated migration role."
    );
  }

  if (row.server_version_num < MINIMUM_POSTGRES_SERVER_VERSION_NUM) {
    throw new PostgresMigrationError(
      "MIGRATION_SERVER_VERSION_UNSUPPORTED",
      "The migration target must be PostgreSQL 18.4 or newer."
    );
  }
}

function readBooleanRow(
  rows: readonly unknown[],
  field: "acquired" | "unlocked"
): boolean {
  const row = asRecord(rows[0]);

  if (row === null || typeof row[field] !== "boolean") {
    throw new PostgresMigrationError(
      field === "acquired"
        ? "MIGRATION_LOCK_UNAVAILABLE"
        : "MIGRATION_LOCK_RELEASE_FAILED",
      `PostgreSQL advisory-lock response did not contain ${field}.`
    );
  }

  return row[field] as boolean;
}

async function applyOneMigration(
  client: PostgresDriverClient,
  migration: ValidatedPostgresMigration
): Promise<void> {
  let transactionStarted = false;

  try {
    await client.query("BEGIN");
    transactionStarted = true;

    await client.query(migration.sql);
    await client.query(POSTGRES_MIGRATION_INSERT_SQL, [
      migration.id,
      migration.name,
      migration.checksum
    ]);

    try {
      await client.query("COMMIT");
      transactionStarted = false;
    } catch (error) {
      throw new PostgresMigrationError(
        "MIGRATION_OUTCOME_UNKNOWN",
        `PostgreSQL commit outcome is unknown for migration ${migration.id}; do not retry automatically.`,
        { cause: error, migrationId: migration.id }
      );
    }
  } catch (error) {
    if (
      error instanceof PostgresMigrationError &&
      error.code === "MIGRATION_OUTCOME_UNKNOWN"
    ) {
      throw error;
    }

    if (transactionStarted) {
      try {
        await client.query("ROLLBACK");
      } catch (rollbackError) {
        throw new PostgresMigrationError(
          "MIGRATION_ROLLBACK_FAILED",
          `Migration ${migration.id} failed and rollback also failed; the connection must be destroyed.`,
          {
            cause: new AggregateError(
              [asError(error), asError(rollbackError)],
              "Migration and rollback both failed."
            ),
            migrationId: migration.id
          }
        );
      }
    }

    throw new PostgresMigrationError(
      "MIGRATION_EXECUTION_FAILED",
      `PostgreSQL migration ${migration.id} failed; no automatic retry was attempted.`,
      { cause: error, migrationId: migration.id }
    );
  }
}

/**
 * One B4 migration executor. It reuses the existing driver pool contract,
 * advisory lock and single application transaction owner.
 */
export class PostgresMigrationRunner {
  private readonly pool: PostgresDriverPool;
  private readonly options: PostgresMigrationRunnerOptions;

  public constructor(
    pool: PostgresDriverPool,
    options: PostgresMigrationRunnerOptions
  ) {
    if (
      typeof pool !== "object" ||
      pool === null ||
      typeof pool.connect !== "function"
    ) {
      throw new TypeError("A PostgreSQL migration pool is required.");
    }

    this.pool = pool;
    this.options = validateRunnerOptions(options);
  }

  public async migrate(
    migrations: readonly PostgresMigration[]
  ): Promise<PostgresMigrationReport> {
    const manifest = validatePostgresMigrationManifest(migrations);
    let client: PostgresDriverClient;

    try {
      client = await this.pool.connect();
    } catch (error) {
      throw new PostgresMigrationError(
        "CONNECTION_UNAVAILABLE",
        "The dedicated PostgreSQL migration connection is unavailable.",
        { cause: error }
      );
    }

    let lockAcquired = false;
    let releaseError: Error | undefined;
    let failure: unknown;
    let report: PostgresMigrationReport | undefined;

    try {
      try {
        const runtimeResult = await client.query(
          POSTGRES_MIGRATION_RUNTIME_SQL
        );
        verifyMigrationRuntime(runtimeResult.rows, this.options);
      } catch (error) {
        releaseError = asError(error);

        if (
          error instanceof PostgresMigrationError &&
          error.code === "MIGRATION_SERVER_VERSION_UNSUPPORTED"
        ) {
          releaseError = undefined;
          throw error;
        }

        throw new PostgresMigrationError(
          error instanceof PostgresMigrationError &&
            error.code === "MIGRATION_ROLE_MISMATCH"
            ? "MIGRATION_ROLE_MISMATCH"
            : "MIGRATION_ROLE_UNAVAILABLE",
          "The configured dedicated PostgreSQL migration role could not be verified; no DDL was attempted.",
          { cause: error }
        );
      }

      try {
        const lockResult = await client.query(POSTGRES_MIGRATION_LOCK_SQL, [
          MIGRATION_LOCK_NAMESPACE,
          MIGRATION_LOCK_RESOURCE
        ]);

        lockAcquired = readBooleanRow(lockResult.rows, "acquired");
      } catch (error) {
        releaseError = asError(error);

        throw new PostgresMigrationError(
          "MIGRATION_LOCK_UNAVAILABLE",
          "PostgreSQL migration-lock acquisition could not be confirmed; the connection was marked for destruction.",
          { cause: error }
        );
      }

      if (!lockAcquired) {
        throw new PostgresMigrationError(
          "MIGRATION_LOCK_UNAVAILABLE",
          "Another PostgreSQL migration runner currently owns the migration lock."
        );
      }

      try {
        const metadataResult = await client.query(
          POSTGRES_MIGRATION_VERIFY_SQL,
          [this.options.applicationRole]
        );

        verifyMigrationMetadata(
          metadataResult.rows,
          this.options.migrationRole,
          this.options.applicationRole
        );
      } catch (error) {
        if (
          error instanceof PostgresMigrationError &&
          error.code === "MIGRATION_METADATA_INVALID"
        ) {
          throw error;
        }

        releaseError = asError(error);

        throw new PostgresMigrationError(
          "MIGRATION_METADATA_READ_FAILED",
          "The pre-provisioned migration ledger could not be queried; no schema or table was created.",
          { cause: error }
        );
      }

      let historyRows: readonly unknown[];

      try {
        const historyResult = await client.query(
          POSTGRES_MIGRATION_HISTORY_SQL
        );

        historyRows = historyResult.rows;
      } catch (error) {
        releaseError = asError(error);

        throw new PostgresMigrationError(
          "MIGRATION_HISTORY_READ_FAILED",
          "The migration history could not be read and verified.",
          { cause: error }
        );
      }

      const history = readHistoryRows(historyRows);
      assertHistoryIsManifestPrefix(history, manifest);

      let appliedCount = 0;

      for (let index = history.length; index < manifest.length; index += 1) {
        const migration = manifest[index];

        if (migration === undefined) {
          throw new PostgresMigrationError(
            "INVALID_MANIFEST",
            "Migration manifest changed while execution was in progress."
          );
        }

        try {
          await applyOneMigration(client, migration);
        } catch (error) {
          if (
            error instanceof PostgresMigrationError &&
            (
              error.code === "MIGRATION_OUTCOME_UNKNOWN" ||
              error.code === "MIGRATION_ROLLBACK_FAILED"
            )
          ) {
            releaseError = error;
          }

          throw error;
        }

        appliedCount += 1;
      }

      const latest = manifest[manifest.length - 1];

      if (latest === undefined) {
        throw new PostgresMigrationError(
          "INVALID_MANIFEST",
          "A validated migration manifest unexpectedly became empty."
        );
      }

      report = Object.freeze({
        appliedCount,
        latestMigrationId: latest.id,
        latestChecksum: latest.checksum
      });
    } catch (error) {
      failure = error;
    } finally {
      if (lockAcquired) {
        try {
          const unlockResult = await client.query(
            POSTGRES_MIGRATION_UNLOCK_SQL,
            [MIGRATION_LOCK_NAMESPACE, MIGRATION_LOCK_RESOURCE]
          );

          if (!readBooleanRow(unlockResult.rows, "unlocked")) {
            const unlockError = new PostgresMigrationError(
              "MIGRATION_LOCK_RELEASE_FAILED",
              "The PostgreSQL migration advisory lock could not be released; the connection must be destroyed.",
              {
                cause: new Error(
                  "The PostgreSQL migration advisory lock was not held at release time."
                )
              }
            );

            releaseError ??= unlockError;

            if (failure === undefined) {
              failure = unlockError;
            }
          }
        } catch (error) {
          const unlockError = new PostgresMigrationError(
            "MIGRATION_LOCK_RELEASE_FAILED",
            "The PostgreSQL migration advisory lock could not be released; the connection must be destroyed.",
            { cause: error }
          );

          releaseError ??= unlockError;

          if (failure === undefined) {
            failure = unlockError;
          }
        }
      }

      try {
        client.release(releaseError);
      } catch (error) {
        if (failure === undefined) {
          failure = new PostgresMigrationError(
            "MIGRATION_LOCK_RELEASE_FAILED",
            "The PostgreSQL migration connection could not be released cleanly.",
            { cause: error }
          );
        }
      }
    }

    if (failure !== undefined) {
      throw failure;
    }

    if (report === undefined) {
      throw new PostgresMigrationError(
        "MIGRATION_HISTORY_CORRUPT",
        "The migration runner ended without a verified report."
      );
    }

    return report;
  }
}

export { checksumSql as postgresMigrationChecksum };
