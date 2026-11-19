/**
 * Internal SQL policy for the canonical PostgreSQL transaction owner.
 *
 * This is a lexical safety boundary, not a PostgreSQL grammar parser and not
 * a substitute for approved row-level security policies. Repository SQL must
 * remain application-owned and static; caller data belongs in bind values.
 */
const ALLOWED_TRANSACTION_COMMANDS = new Set([
  "SELECT",
  "WITH",
  "INSERT",
  "UPDATE",
  "DELETE",
  "MERGE",
  "VALUES",
  "TABLE"
]);

const FORBIDDEN_SESSION_FUNCTIONS = new Set([
  "set_config",
  "pg_advisory_lock",
  "pg_advisory_lock_shared",
  "pg_try_advisory_lock",
  "pg_try_advisory_lock_shared",
  "pg_advisory_unlock",
  "pg_advisory_unlock_shared",
  "pg_advisory_unlock_all",
  "pg_advisory_xact_lock",
  "pg_advisory_xact_lock_shared",
  "pg_try_advisory_xact_lock",
  "pg_try_advisory_xact_lock_shared"
]);

export type PostgresTransactionQueryPolicyErrorCode =
  | "INVALID_SQL"
  | "MULTIPLE_STATEMENTS"
  | "STATEMENT_NOT_ALLOWED"
  | "TENANT_CONTEXT_MUTATION"
  | "SESSION_STATE_MUTATION";

/** SQL rejected before it can reach the checked-out PostgreSQL client. */
export class PostgresTransactionQueryPolicyError extends Error {
  public readonly code: PostgresTransactionQueryPolicyErrorCode;

  public constructor(code: PostgresTransactionQueryPolicyErrorCode) {
    super("PostgreSQL transaction query violates the transaction-owner SQL policy.");
    this.name = "PostgresTransactionQueryPolicyError";
    this.code = code;
  }
}

interface SqlToken {
  readonly kind: "identifier" | "quoted_identifier" | "symbol";
  readonly value: string;
}

function isIdentifierStart(character: string): boolean {
  const code = character.charCodeAt(0);
  return (
    (code >= 65 && code <= 90) ||
    (code >= 97 && code <= 122) ||
    code === 95 ||
    code >= 128
  );
}

function isIdentifierPart(character: string): boolean {
  const code = character.charCodeAt(0);
  return (
    isIdentifierStart(character) ||
    (code >= 48 && code <= 57) ||
    code === 36
  );
}

function skipSingleQuotedString(
  sql: string,
  start: number,
  backslashEscapes: boolean
): number {
  let cursor = start + 1;

  while (cursor < sql.length) {
    const character = sql[cursor];

    if (backslashEscapes && character === "\\") {
      cursor += 2;
      continue;
    }

    if (character === "'") {
      if (sql[cursor + 1] === "'") {
        cursor += 2;
        continue;
      }
      return cursor + 1;
    }

    cursor += 1;
  }

  throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
}

function skipQuotedIdentifier(sql: string, start: number): number {
  let cursor = start + 1;

  while (cursor < sql.length) {
    if (sql[cursor] === '"') {
      if (sql[cursor + 1] === '"') {
        cursor += 2;
        continue;
      }
      return cursor + 1;
    }
    cursor += 1;
  }

  throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
}

function isDollarTagPart(character: string): boolean {
  const code = character.charCodeAt(0);
  return (
    isIdentifierStart(character) ||
    (code >= 48 && code <= 57)
  );
}

function readDollarQuoteDelimiter(
  sql: string,
  start: number
): string | undefined {
  if (sql[start] !== "$") return undefined;
  if (start > 0 && isIdentifierPart(sql[start - 1] ?? "")) {
    return undefined;
  }

  let cursor = start + 1;

  if (sql[cursor] === "$") {
    return "$$";
  }

  if (!isIdentifierStart(sql[cursor] ?? "")) {
    return undefined;
  }

  cursor += 1;
  while (cursor < sql.length && isDollarTagPart(sql[cursor] ?? "")) {
    cursor += 1;
  }

  return sql[cursor] === "$" ? sql.slice(start, cursor + 1) : undefined;
}

/**
 * Tokenizes enough PostgreSQL lexical structure to enforce the transaction
 * boundary without pretending to parse PostgreSQL grammar. Literals,
 * identifiers, nested comments and dollar-quoted bodies are skipped safely;
 * any second statement is rejected.
 */
function tokenizeTransactionSql(sql: string): readonly SqlToken[] {
  const tokens: SqlToken[] = [];
  let cursor = 0;
  let statementTerminated = false;

  const ensureStatementOpen = (): void => {
    if (statementTerminated) {
      throw new PostgresTransactionQueryPolicyError("MULTIPLE_STATEMENTS");
    }
  };

  while (cursor < sql.length) {
    const character = sql[cursor] ?? "";
    const next = sql[cursor + 1] ?? "";

    if (character === " " || character === "\t" || character === "\n" || character === "\r" || character === "\f") {
      cursor += 1;
      continue;
    }

    if (character === "-" && next === "-") {
      cursor += 2;
      while (cursor < sql.length && sql[cursor] !== "\n" && sql[cursor] !== "\r") {
        cursor += 1;
      }
      continue;
    }

    if (character === "/" && next === "*") {
      cursor += 2;
      let depth = 1;

      while (cursor < sql.length && depth > 0) {
        const current = sql[cursor] ?? "";
        const following = sql[cursor + 1] ?? "";

        if (current === "/" && following === "*") {
          depth += 1;
          cursor += 2;
        } else if (current === "*" && following === "/") {
          depth -= 1;
          cursor += 2;
        } else {
          cursor += 1;
        }
      }

      if (depth !== 0) {
        throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
      }
      continue;
    }

    if (character === ";") {
      if (statementTerminated) {
        throw new PostgresTransactionQueryPolicyError("MULTIPLE_STATEMENTS");
      }
      statementTerminated = true;
      cursor += 1;
      continue;
    }

    if (character === "'") {
      ensureStatementOpen();
      const previous = sql[cursor - 1] ?? "";
      const beforePrevious = sql[cursor - 2] ?? "";
      const escapePrefix =
        (previous === "e" || previous === "E") &&
        !isIdentifierPart(beforePrevious);
      cursor = skipSingleQuotedString(sql, cursor, escapePrefix);
      continue;
    }

    if (character === '"') {
      ensureStatementOpen();
      const unicodeIdentifierPrefix = sql.slice(
        Math.max(0, cursor - 2),
        cursor
      ).toUpperCase();
      if (unicodeIdentifierPrefix === "U&") {
        // Reject U& identifiers rather than risk alternate UESCAPE spellings
        // bypassing protected function-name checks. Ordinary quoted names
        // remain supported.
        throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
      }
      const start = cursor + 1;
      cursor = skipQuotedIdentifier(sql, cursor);
      const value = sql
        .slice(start, cursor - 1)
        .replaceAll('""', '"')
        .toLowerCase();
      if (value.includes("\\")) {
        throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
      }
      tokens.push({ kind: "quoted_identifier", value });
      continue;
    }

    const dollarDelimiter = readDollarQuoteDelimiter(sql, cursor);
    if (dollarDelimiter !== undefined) {
      ensureStatementOpen();
      const bodyStart = cursor + dollarDelimiter.length;
      const closingIndex = sql.indexOf(dollarDelimiter, bodyStart);

      if (closingIndex < 0) {
        throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
      }

      cursor = closingIndex + dollarDelimiter.length;
      continue;
    }

    if (isIdentifierStart(character)) {
      ensureStatementOpen();
      const start = cursor;
      cursor += 1;

      while (cursor < sql.length && isIdentifierPart(sql[cursor] ?? "")) {
        cursor += 1;
      }

      tokens.push({
        kind: "identifier",
        value: sql.slice(start, cursor).toLowerCase()
      });
      continue;
    }

    ensureStatementOpen();
    tokens.push({ kind: "symbol", value: character });
    cursor += 1;
  }

  if (tokens.length === 0) {
    throw new PostgresTransactionQueryPolicyError("INVALID_SQL");
  }

  return tokens;
}

export function assertTransactionQueryAllowed(sql: string): void {
  const tokens = tokenizeTransactionSql(sql);
  // Reject protected names wherever they occur as SQL identifiers, not only
  // when followed by a literal opening parenthesis. This conservative rule
  // also closes parenthesized/quoted function-name spellings.
  const identifiers = tokens
    .filter((token) => token.kind !== "symbol")
    .map((token) => token.value);

  if (identifiers.includes("set_config")) {
    throw new PostgresTransactionQueryPolicyError("TENANT_CONTEXT_MUTATION");
  }

  if (identifiers.some((value) => FORBIDDEN_SESSION_FUNCTIONS.has(value))) {
    throw new PostgresTransactionQueryPolicyError("SESSION_STATE_MUTATION");
  }

  const first = tokens[0];
  if (
    first === undefined ||
    first.kind !== "identifier" ||
    !ALLOWED_TRANSACTION_COMMANDS.has(first.value.toUpperCase())
  ) {
    throw new PostgresTransactionQueryPolicyError("STATEMENT_NOT_ALLOWED");
  }

  // SELECT INTO creates a table and belongs to the separately governed
  // migration/schema owner, not an application transaction callback.
  if (
    first.value.toUpperCase() === "SELECT" &&
    tokens.some(
      (token) => token.kind === "identifier" && token.value === "into"
    )
  ) {
    throw new PostgresTransactionQueryPolicyError("STATEMENT_NOT_ALLOWED");
  }
}
