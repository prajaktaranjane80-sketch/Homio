/**
 * Single PostgreSQL connection and transaction owner for B4.
 *
 * This module is deliberately structural: a real node-postgres Pool is
 * injected by the composition root. It does not create a second driver,
 * ORM, repository registry or business schema.
 */

export interface PostgresQueryResult {
  readonly rows: readonly unknown[];
  readonly rowCount: number | null;
}

/** The subset of node-postgres PoolClient used by the persistence boundary. */
export interface PostgresDriverClient {
  query(
    text: string,
    values?: unknown[]
  ): Promise<PostgresQueryResult>;
  release(error?: Error | boolean): void;
}

/** The subset of node-postgres Pool owned by this runtime. */
export interface PostgresDriverPool {
  connect(): Promise<PostgresDriverClient>;
  end(): Promise<void>;
}

export interface PostgresTenantContext {
  readonly tenantId: string;
}

export type PostgresIsolationLevel =
  | "READ COMMITTED"
  | "REPEATABLE READ"
  | "SERIALIZABLE";

export interface PostgresTransactionOptions {
  readonly isolationLevel?: PostgresIsolationLevel;
  readonly readOnly?: boolean;
}

export interface PostgresQuery<Row extends Record<string, unknown>> {
  readonly rows: readonly Row[];
  readonly rowCount: number | null;
}

/** A transaction handle that cannot expose or release its underlying client. */
export interface PostgresTransaction {
  readonly tenantId: string;
  readonly readOnly: boolean;
  query<Row extends Record<string, unknown> = Record<string, unknown>>(
    text: string,
    values?: readonly unknown[]
  ): Promise<PostgresQuery<Row>>;
}

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const DEFAULT_ISOLATION_LEVEL: PostgresIsolationLevel = "READ COMMITTED";
const TENANT_SETTING_SQL =
  "SELECT set_config('app.tenant_id', $1, true) AS tenant_id";

/**
 * Runtime-role verification runs against PostgreSQL's catalogs, not an
 * application table. It rejects privileged/table-owner roles and requires
 * FORCE RLS on every permanent user table carrying tenant_id.
 */
export const POSTGRES_RUNTIME_ROLE_SAFETY_SQL = `
WITH tenant_tables AS (
  SELECT DISTINCT
    relation.oid,
    relation.relrowsecurity,
    relation.relforcerowsecurity
  FROM pg_class AS relation
  JOIN pg_namespace AS namespace
    ON namespace.oid = relation.relnamespace
  JOIN pg_attribute AS attribute
    ON attribute.attrelid = relation.oid
  WHERE relation.relkind IN ('r', 'p')
    AND namespace.nspname <> 'information_schema'
    AND namespace.nspname NOT LIKE 'pg!_%' ESCAPE '!'
    AND attribute.attname = 'tenant_id'
    AND attribute.attnum > 0
    AND attribute.attisdropped = false
), owned_application_tables AS (
  SELECT 1
  FROM pg_class AS relation
  JOIN pg_namespace AS namespace
    ON namespace.oid = relation.relnamespace
  WHERE relation.relowner = (
    SELECT oid
    FROM pg_roles
    WHERE rolname = current_user
  )
    AND relation.relkind IN ('r', 'p')
    AND namespace.nspname <> 'information_schema'
    AND namespace.nspname NOT LIKE 'pg!_%' ESCAPE '!'
  LIMIT 1
)
SELECT
  current_user AS role_name,
  role.rolsuper AS is_superuser,
  role.rolbypassrls AS bypasses_row_security,
  EXISTS (SELECT 1 FROM owned_application_tables) AS owns_application_tables,
  (SELECT count(*)::integer FROM tenant_tables) AS tenant_table_count,
  COALESCE(
    (
      SELECT bool_and(
        tenant_tables.relrowsecurity
        AND tenant_tables.relforcerowsecurity
      )
      FROM tenant_tables
    ),
    false
  ) AS tenant_tables_force_rls
FROM pg_roles AS role
WHERE role.rolname = current_user
`.trim();

export class PostgresRuntimeClosedError extends Error {
  public constructor() {
    super("PostgreSQL runtime is closed.");
    this.name = "PostgresRuntimeClosedError";
  }
}

export class PostgresTenantContextError extends Error {
  public constructor() {
    super("A canonical UUID tenant context is required.");
    this.name = "PostgresTenantContextError";
  }
}

export type PostgresRuntimeRoleErrorCode =
  | "ROLE_CHECK_UNAVAILABLE"
  | "INVALID_ROLE_RESULT"
  | "SUPERUSER_ROLE"
  | "BYPASS_RLS_ROLE"
  | "OWNS_APPLICATION_TABLES"
  | "TENANT_TABLES_MISSING"
  | "TENANT_TABLES_RLS_NOT_FORCED";

export class PostgresRuntimeRoleError extends Error {
  public readonly code: PostgresRuntimeRoleErrorCode;

  public constructor(
    code: PostgresRuntimeRoleErrorCode,
    cause?: unknown
  ) {
    super(
      "PostgreSQL application role does not satisfy the tenant isolation boundary.",
      cause === undefined ? undefined : { cause }
    );
    this.name = "PostgresRuntimeRoleError";
    this.code = code;
  }
}

export class PostgresTransactionClosedError extends Error {
  public constructor() {
    super("The PostgreSQL transaction callback has already completed.");
    this.name = "PostgresTransactionClosedError";
  }
}

export class PostgresTransactionOutcomeUnknownError extends Error {
  public constructor(cause: unknown) {
    super(
      "The PostgreSQL commit outcome is unknown; automatic retry is forbidden.",
      { cause }
    );
    this.name = "PostgresTransactionOutcomeUnknownError";
  }
}

export class PostgresTransactionRollbackError extends Error {
  public readonly originalError: unknown;
  public readonly rollbackError: unknown;

  public constructor(originalError: unknown, rollbackError: unknown) {
    super(
      "The PostgreSQL transaction failed and its rollback also failed.",
      { cause: originalError }
    );
    this.name = "PostgresTransactionRollbackError";
    this.originalError = originalError;
    this.rollbackError = rollbackError;
  }
}

function normalizeTenantId(value: unknown): string {
  if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
    throw new PostgresTenantContextError();
  }

  return value.toLowerCase();
}

function normalizeIsolationLevel(
  value: unknown
): PostgresIsolationLevel {
  if (
    value === "READ COMMITTED" ||
    value === "REPEATABLE READ" ||
    value === "SERIALIZABLE"
  ) {
    return value;
  }

  throw new TypeError(
    "Unsupported PostgreSQL transaction isolation level."
  );
}

function normalizeReadOnly(value: unknown): boolean {
  if (value === undefined) {
    return false;
  }

  if (typeof value !== "boolean") {
    throw new TypeError("PostgreSQL readOnly option must be boolean.");
  }

  return value;
}

function normalizeQueryText(value: unknown): string {
  if (
    typeof value !== "string" ||
    value.trim().length === 0 ||
    value.includes("\0")
  ) {
    throw new TypeError("PostgreSQL query text is invalid.");
  }

  return value;
}

function toError(value: unknown): Error {
  return value instanceof Error
    ? value
    : new Error("PostgreSQL operation failed.", { cause: value });
}

function beginStatement(
  isolationLevel: PostgresIsolationLevel,
  readOnly: boolean
): string {
  return readOnly
    ? `BEGIN ISOLATION LEVEL ${isolationLevel} READ ONLY`
    : `BEGIN ISOLATION LEVEL ${isolationLevel}`;
}

/**
 * Owns exactly one node-postgres Pool and every transaction run through it.
 * Transaction-bound work always uses one checked-out client and transaction-
 * local tenant context, so a pooled connection cannot leak a tenant to its
 * next borrower.
 */
export class PostgresRuntime {
  private readonly pool: PostgresDriverPool;
  private closePromise: Promise<void> | undefined;
  private roleVerificationPromise: Promise<void> | undefined;
  private closed = false;

  public constructor(pool: PostgresDriverPool) {
    if (
      typeof pool !== "object" ||
      pool === null ||
      typeof pool.connect !== "function" ||
      typeof pool.end !== "function"
    ) {
      throw new TypeError("A valid node-postgres Pool is required.");
    }

    this.pool = pool;
  }

  /**
   * Explicit startup hook. The first tenant transaction performs the same
   * verification automatically if the composition root does not call this.
   */
  public async verifyRuntimeRoleSafety(): Promise<void> {
    if (this.closed) {
      throw new PostgresRuntimeClosedError();
    }

    const client = await this.pool.connect();
    let releaseError: Error | undefined;

    try {
      await this.ensureRuntimeRoleSafety(client);
    } catch (error) {
      releaseError = toError(error);
      throw error;
    } finally {
      client.release(releaseError);
    }
  }

  private ensureRuntimeRoleSafety(
    client: PostgresDriverClient
  ): Promise<void> {
    if (this.roleVerificationPromise === undefined) {
      this.roleVerificationPromise = this.checkRuntimeRole(client);
    }

    return this.roleVerificationPromise;
  }

  private async checkRuntimeRole(
    client: PostgresDriverClient
  ): Promise<void> {
    let rows: readonly unknown[];

    try {
      const result = await client.query(
        POSTGRES_RUNTIME_ROLE_SAFETY_SQL
      );
      rows = result.rows;
    } catch (cause) {
      throw new PostgresRuntimeRoleError(
        "ROLE_CHECK_UNAVAILABLE",
        cause
      );
    }

    const candidate = rows[0];

    if (
      rows.length !== 1 ||
      typeof candidate !== "object" ||
      candidate === null ||
      Array.isArray(candidate)
    ) {
      throw new PostgresRuntimeRoleError("INVALID_ROLE_RESULT");
    }

    const role = candidate as Record<string, unknown>;

    if (
      typeof role.role_name !== "string" ||
      role.role_name.trim().length === 0 ||
      typeof role.is_superuser !== "boolean" ||
      typeof role.bypasses_row_security !== "boolean" ||
      typeof role.owns_application_tables !== "boolean" ||
      typeof role.tenant_table_count !== "number" ||
      !Number.isSafeInteger(role.tenant_table_count) ||
      typeof role.tenant_tables_force_rls !== "boolean"
    ) {
      throw new PostgresRuntimeRoleError("INVALID_ROLE_RESULT");
    }

    if (role.is_superuser) {
      throw new PostgresRuntimeRoleError("SUPERUSER_ROLE");
    }

    if (role.bypasses_row_security) {
      throw new PostgresRuntimeRoleError("BYPASS_RLS_ROLE");
    }

    if (role.owns_application_tables) {
      throw new PostgresRuntimeRoleError("OWNS_APPLICATION_TABLES");
    }

    if (role.tenant_table_count < 1) {
      throw new PostgresRuntimeRoleError("TENANT_TABLES_MISSING");
    }

    if (!role.tenant_tables_force_rls) {
      throw new PostgresRuntimeRoleError(
        "TENANT_TABLES_RLS_NOT_FORCED"
      );
    }
  }

  /**
   * Execute tenant-scoped work on one PostgreSQL client.
   *
   * The runtime never retries a transaction. In particular, a failed COMMIT
   * is reported as an unknown outcome and its connection is destroyed rather
   * than returned to the pool or replayed automatically.
   */
  public async withTenantTransaction<Result>(
    context: PostgresTenantContext,
    work: (transaction: PostgresTransaction) => Promise<Result>,
    options: PostgresTransactionOptions = {}
  ): Promise<Result> {
    if (this.closed) {
      throw new PostgresRuntimeClosedError();
    }

    if (typeof work !== "function") {
      throw new TypeError("PostgreSQL transaction work must be a function.");
    }

    const tenantId = normalizeTenantId(context?.tenantId);
    const isolationLevel = normalizeIsolationLevel(
      options.isolationLevel ?? DEFAULT_ISOLATION_LEVEL
    );
    const readOnly = normalizeReadOnly(options.readOnly);
    const client = await this.pool.connect();

    let transactionActive = false;
    let commitAttempted = false;
    let transactionHandleActive = true;
    let releaseError: Error | undefined;
    let firstQueryError: unknown;
    let hasQueryError = false;
    let queryQueue: Promise<void> = Promise.resolve();

    const transaction: PostgresTransaction = Object.freeze({
      tenantId,
      readOnly,
      query: async <Row extends Record<string, unknown>>(
        rawText: string,
        values?: readonly unknown[]
      ): Promise<PostgresQuery<Row>> => {
        if (!transactionHandleActive) {
          throw new PostgresTransactionClosedError();
        }

        const text = normalizeQueryText(rawText);
        const parameters = values === undefined ? undefined : [...values];
        const operation = queryQueue.then(async () => {
          const result = await client.query(text, parameters);
          return {
            rows: result.rows as readonly Row[],
            rowCount: result.rowCount
          };
        });

        queryQueue = operation.then(
          () => undefined,
          (error: unknown) => {
            if (!hasQueryError) {
              firstQueryError = error;
              hasQueryError = true;
            }
          }
        );

        return operation;
      }
    });

    try {
      await this.ensureRuntimeRoleSafety(client);

      await client.query(
        beginStatement(isolationLevel, readOnly)
      );
      transactionActive = true;

      await client.query(
        TENANT_SETTING_SQL,
        [tenantId]
      );

      const result = await work(transaction);
      transactionHandleActive = false;
      await queryQueue;

      if (hasQueryError) {
        throw firstQueryError;
      }

      commitAttempted = true;

      try {
        await client.query("COMMIT");
      } catch (error) {
        releaseError = toError(error);
        throw new PostgresTransactionOutcomeUnknownError(error);
      }

      transactionActive = false;
      return result;
    } catch (error) {
      transactionHandleActive = false;
      await queryQueue;

      if (transactionActive && !commitAttempted) {
        try {
          await client.query("ROLLBACK");
          transactionActive = false;
        } catch (rollbackError) {
          releaseError = toError(rollbackError);
          throw new PostgresTransactionRollbackError(
            error,
            rollbackError
          );
        }
      } else if (!transactionActive && !commitAttempted) {
        // A failed BEGIN leaves connection state uncertain. Destroy the
        // client rather than returning a potentially unusable connection.
        releaseError = toError(error);
      }

      throw error;
    } finally {
      transactionHandleActive = false;
      client.release(releaseError);
    }
  }

  /** Close the owned pool exactly once. Repeated calls share one operation. */
  public close(): Promise<void> {
    if (this.closePromise === undefined) {
      this.closed = true;
      this.closePromise = Promise.resolve().then(() => this.pool.end());
    }

    return this.closePromise;
  }
}

export { normalizeTenantId as normalizePostgresTenantId };
