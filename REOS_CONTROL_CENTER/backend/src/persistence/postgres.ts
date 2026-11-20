import { assertTransactionQueryAllowed } from "./postgres-query-policy.js";

export { PostgresTransactionQueryPolicyError } from "./postgres-query-policy.js";

/**
 * Single PostgreSQL connection and transaction owner for B4.
 *
 * This adapter deliberately receives the canonical node-postgres Pool from
 * the composition root. It does not create a second driver, ORM, repository
 * registry or business schema.
 */
export interface PostgresQueryResult {
  readonly rows: readonly unknown[];
  readonly rowCount: number | null;
}

export interface PostgresDriverClient {
  query(text: string, values?: unknown[]): Promise<PostgresQueryResult>;
  release(error?: Error | boolean): void;
}

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

export interface PostgresTransaction {
  readonly tenantId: string;
  readonly readOnly: boolean;
  /**
   * Execute one application-owned statement. Keep SQL static and pass every
   * caller-controlled value through bind parameters. The runtime denies
   * transaction/session control, DDL, direct tenant-context mutation and
   * multiple statements; approved database RLS remains mandatory.
   */
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
 * Rejects the login role if it, or any role whose privileges it can inherit
 * or assume with SET ROLE, is a superuser, bypasses RLS, or owns application
 * tables.
 *
 * Checking only current_user is insufficient: role memberships can otherwise
 * provide an RLS bypass even when the login role itself looks safe.
 *
 * PostgreSQL 16+ supports the USAGE and SET membership tests used here.
 * HOMIO's backend master specifies PostgreSQL 18.4+ as its target.
 *
 * FORCE ROW LEVEL SECURITY alone is not sufficient. Permissive policies are
 * combined with OR, so a broad permissive policy can otherwise widen access.
 * Every tenant table must also have an applicable restrictive FOR ALL policy
 * whose USING and WITH CHECK expressions both match the transaction-local
 * app.tenant_id equality.
 *
 * PostgreSQL's pg_get_expr() deparser emits parentheses around function calls
 * and casts. Those parentheses are significant and must be preserved.
 * Whitespace is normalized only; a small explicit allow-list recognizes the
 * supported deparser forms. Unknown policy expressions fail closed.
 */
export const POSTGRES_RUNTIME_ROLE_SAFETY_SQL = `
WITH effective_roles AS (
  SELECT
    candidate.oid,
    candidate.rolsuper,
    candidate.rolbypassrls
  FROM pg_roles AS candidate
  WHERE candidate.rolname = session_user
     OR pg_has_role(session_user, candidate.oid, 'USAGE')
     OR pg_has_role(session_user, candidate.oid, 'SET')
), tenant_policy_roles AS (
  SELECT candidate.oid
  FROM pg_roles AS candidate
  WHERE candidate.rolname = session_user
     OR pg_has_role(session_user, candidate.oid, 'USAGE')
), tenant_tables AS (
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
)
SELECT
  CASE
    WHEN current_user = session_user THEN session_user
    ELSE ''
  END AS role_name,
  COALESCE(
    (SELECT bool_or(rolsuper) FROM effective_roles),
    true
  ) AS is_superuser,
  COALESCE(
    (SELECT bool_or(rolbypassrls) FROM effective_roles),
    true
  ) AS bypasses_row_security,
  EXISTS (
    SELECT 1
    FROM pg_class AS relation
    JOIN pg_namespace AS namespace
      ON namespace.oid = relation.relnamespace
    WHERE relation.relowner IN (SELECT oid FROM effective_roles)
      AND relation.relkind IN ('r', 'p')
      AND namespace.nspname <> 'information_schema'
      AND namespace.nspname NOT LIKE 'pg!_%' ESCAPE '!'
  ) AS owns_application_tables,
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
  ) AS tenant_tables_force_rls,
  NOT EXISTS (
    SELECT 1
    FROM tenant_tables AS tenant_table
    WHERE NOT EXISTS (
      SELECT 1
      FROM pg_policy AS policy
      WHERE policy.polrelid = tenant_table.oid
        AND policy.polpermissive = false
        AND policy.polcmd = '*'
        AND (
          policy.polroles @> ARRAY[0::oid]
          OR policy.polroles && ARRAY(
            SELECT tenant_policy_roles.oid
            FROM tenant_policy_roles
          )
        )
        AND policy.polqual IS NOT NULL
        AND policy.polwithcheck IS NOT NULL
        AND pg_catalog.regexp_replace(
          pg_catalog.lower(
            pg_catalog.pg_get_expr(policy.polqual, policy.polrelid)
          ),
          '[[:space:]]',
          '',
          'g'
        ) IN (
          '(tenant_id=(current_setting(''app.tenant_id''::text,true))::uuid)',
          'tenant_id=(current_setting(''app.tenant_id''::text,true))::uuid',
          '(tenant_id=current_setting(''app.tenant_id''::text,true)::uuid)',
          'tenant_id=current_setting(''app.tenant_id''::text,true)::uuid',
          '(tenant_id=current_setting(''app.tenant_id''::text,true))',
          'tenant_id=current_setting(''app.tenant_id''::text,true)'
        )
        AND pg_catalog.regexp_replace(
          pg_catalog.lower(
            pg_catalog.pg_get_expr(policy.polwithcheck, policy.polrelid)
          ),
          '[[:space:]]',
          '',
          'g'
        ) IN (
          '(tenant_id=(current_setting(''app.tenant_id''::text,true))::uuid)',
          'tenant_id=(current_setting(''app.tenant_id''::text,true))::uuid',
          '(tenant_id=current_setting(''app.tenant_id''::text,true)::uuid)',
          'tenant_id=current_setting(''app.tenant_id''::text,true)::uuid',
          '(tenant_id=current_setting(''app.tenant_id''::text,true))',
          'tenant_id=current_setting(''app.tenant_id''::text,true)'
        )
    )
  ) AS tenant_tables_have_tenant_restrictive_guard
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
  | "TENANT_TABLES_RLS_NOT_FORCED"
  | "TENANT_RLS_POLICY_GUARD_MISSING_OR_UNSAFE";

export class PostgresRuntimeRoleError extends Error {
  public readonly code: PostgresRuntimeRoleErrorCode;

  public constructor(code: PostgresRuntimeRoleErrorCode, cause?: unknown) {
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

function normalizeIsolationLevel(value: unknown): PostgresIsolationLevel {
  if (
    value === "READ COMMITTED" ||
    value === "REPEATABLE READ" ||
    value === "SERIALIZABLE"
  ) {
    return value;
  }
  throw new TypeError("Unsupported PostgreSQL transaction isolation level.");
}

function normalizeReadOnly(value: unknown): boolean {
  if (value === undefined) return false;
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

function normalizeQueryValues(value: unknown): readonly unknown[] | undefined {
  if (value === undefined) return undefined;
  if (!Array.isArray(value)) {
    throw new TypeError("PostgreSQL query values must be an array.");
  }
  return [...value];
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

/** Owns one Pool; every tenant transaction uses one checked-out client. */
export class PostgresRuntime {
  private readonly pool: PostgresDriverPool;
  private closePromise: Promise<void> | undefined;
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
   * Explicit operational check.
   *
   * This checks the connection acquired by this call. A successful result
   * must never be reused as proof for another pooled connection.
   */
  public async verifyRuntimeRoleSafety(): Promise<void> {
    if (this.closed) throw new PostgresRuntimeClosedError();

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

  /**
   * Each checked-out connection is a separate security boundary.
   *
   * Do not cache this result on PostgresRuntime:
   * - pooled clients can carry different session state;
   * - a previously released client may have changed session role;
   * - a transient role-check failure must not poison all future attempts.
   *
   * Verification therefore runs on the exact client that will execute the
   * transaction, before BEGIN or tenant-scoped SQL is issued.
   */
  private ensureRuntimeRoleSafety(
    client: PostgresDriverClient
  ): Promise<void> {
    return this.checkRuntimeRole(client);
  }

  private async checkRuntimeRole(client: PostgresDriverClient): Promise<void> {
    let rows: readonly unknown[];

    try {
      const result = await client.query(POSTGRES_RUNTIME_ROLE_SAFETY_SQL);
      rows = result.rows;
    } catch (cause) {
      throw new PostgresRuntimeRoleError("ROLE_CHECK_UNAVAILABLE", cause);
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
      typeof role.tenant_tables_force_rls !== "boolean" ||
      typeof role.tenant_tables_have_tenant_restrictive_guard !== "boolean"
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
      throw new PostgresRuntimeRoleError("TENANT_TABLES_RLS_NOT_FORCED");
    }

    if (!role.tenant_tables_have_tenant_restrictive_guard) {
      throw new PostgresRuntimeRoleError(
        "TENANT_RLS_POLICY_GUARD_MISSING_OR_UNSAFE"
      );
    }
  }

  public async withTenantTransaction<Result>(
    context: PostgresTenantContext,
    work: (transaction: PostgresTransaction) => Promise<Result>,
    options: PostgresTransactionOptions = {}
  ): Promise<Result> {
    if (this.closed) throw new PostgresRuntimeClosedError();

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
        rawValues?: readonly unknown[]
      ): Promise<PostgresQuery<Row>> => {
        if (!transactionHandleActive) {
          throw new PostgresTransactionClosedError();
        }

        let text: string | undefined;
        let values: readonly unknown[] | undefined;
        let validationError: unknown;
        let hasValidationError = false;

        try {
          text = normalizeQueryText(rawText);
          assertTransactionQueryAllowed(text);
          values = normalizeQueryValues(rawValues);
        } catch (error) {
          validationError = error;
          hasValidationError = true;
        }

        const operation = queryQueue.then(async () => {
          if (hasQueryError) {
            throw firstQueryError;
          }

          if (hasValidationError) {
            throw validationError;
          }

          const result = await client.query(
            text as string,
            values === undefined ? undefined : [...values]
          );

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

      await client.query(beginStatement(isolationLevel, readOnly));
      transactionActive = true;

      await client.query(TENANT_SETTING_SQL, [tenantId]);

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
          throw new PostgresTransactionRollbackError(error, rollbackError);
        }
      } else if (!transactionActive && !commitAttempted) {
        releaseError = toError(error);
      }

      throw error;
    } finally {
      transactionHandleActive = false;
      client.release(releaseError);
    }
  }

  public close(): Promise<void> {
    if (this.closePromise === undefined) {
      this.closed = true;
      this.closePromise = Promise.resolve().then(() => this.pool.end());
    }

    return this.closePromise;
  }
}

export { normalizeTenantId as normalizePostgresTenantId };
