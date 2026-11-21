
import { isIP } from "node:net";
import { URL } from "node:url";

import type {
  BackendSettings,
  LogLevel,
  NodeEnvironment,
  PostgresConnectionSettings,
  PostgresSslMode,
  RedisConnectionSettings
} from "./settings.js";

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 3001;
const DEFAULT_LOG_LEVEL: LogLevel = "info";

const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;
const DEFAULT_SHUTDOWN_TIMEOUT_MS = 10_000;
const DEFAULT_POSTGRES_POOL_MAX = 10;
const DEFAULT_POSTGRES_CONNECTION_TIMEOUT_MS = 5_000;
const DEFAULT_POSTGRES_IDLE_TIMEOUT_MS = 30_000;
const DEFAULT_POSTGRES_STATEMENT_TIMEOUT_MS = 15_000;
const DEFAULT_REDIS_CONNECT_TIMEOUT_MS = 5_000;

const MIN_TIMEOUT_MS = 1_000;
const MAX_TIMEOUT_MS = 120_000;
const MAX_POSTGRES_POOL_SIZE = 100;
const MAX_POSTGRES_IDLE_TIMEOUT_MS = 300_000;

const NODE_ENVIRONMENTS: readonly NodeEnvironment[] = [
  "development",
  "test",
  "production"
];

const LOG_LEVELS: readonly LogLevel[] = [
  "fatal",
  "error",
  "warn",
  "info",
  "debug",
  "trace",
  "silent"
];

const DNS_LABEL_PATTERN =
  /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/;

const POSTGRES_SSL_QUERY_PARAMETERS = new Set([
  "sslmode",
  "sslrootcert",
  "sslcert",
  "sslkey"
]);

export class ConfigurationError extends Error {
  public readonly issues: readonly string[];

  public constructor(issues: readonly string[]) {
    // Connection URLs, certificates and credentials must never enter
    // configuration error messages.
    super(
      `Invalid backend runtime configuration: ${issues.join("; ")}`
    );

    this.name = "ConfigurationError";
    this.issues = Object.freeze([...issues]);
  }
}

function isValidBindHost(value: string): boolean {
  if (isIP(value) !== 0) {
    return true;
  }

  if (/^\d+(?:\.\d+){3}$/.test(value)) {
    return false;
  }

  const hostname = value.endsWith(".")
    ? value.slice(0, -1)
    : value;

  if (
    hostname.length === 0 ||
    hostname.length > 253
  ) {
    return false;
  }

  return hostname
    .split(".")
    .every((label) =>
      label.length <= 63 &&
      DNS_LABEL_PATTERN.test(label)
    );
}

function readInteger(
  name: string,
  rawValue: string | undefined,
  fallback: number,
  minimum: number,
  maximum: number,
  issues: string[]
): number {
  if (rawValue === undefined) {
    return fallback;
  }

  if (!/^\d+$/.test(rawValue)) {
    issues.push(`${name} must be a valid integer`);
    return fallback;
  }

  const value = Number(rawValue);

  if (
    !Number.isSafeInteger(value) ||
    value < minimum ||
    value > maximum
  ) {
    issues.push(
      `${name} must be between ${minimum} and ${maximum}`
    );

    return fallback;
  }

  return value;
}

function readHost(
  rawValue: string | undefined,
  issues: string[]
): string {
  if (rawValue === undefined) {
    return DEFAULT_HOST;
  }

  const value = rawValue.trim();

  if (
    value.length === 0 ||
    value !== rawValue ||
    !isValidBindHost(value)
  ) {
    issues.push(
      "HOMIO_BACKEND_HOST must be a valid IP address or DNS hostname without whitespace, URL or path components"
    );

    return DEFAULT_HOST;
  }

  return value;
}

function readNodeEnvironment(
  rawValue: string | undefined,
  issues: string[]
): NodeEnvironment {
  const value = rawValue ?? "development";

  if (
    NODE_ENVIRONMENTS.includes(value as NodeEnvironment)
  ) {
    return value as NodeEnvironment;
  }

  issues.push(
    "NODE_ENV must be development, test or production"
  );

  return "development";
}

function readLogLevel(
  rawValue: string | undefined,
  issues: string[]
): LogLevel {
  const value = rawValue ?? DEFAULT_LOG_LEVEL;

  if (LOG_LEVELS.includes(value as LogLevel)) {
    return value as LogLevel;
  }

  issues.push(
    "HOMIO_LOG_LEVEL must be a supported log level"
  );

  return DEFAULT_LOG_LEVEL;
}

function containsControlCharacters(value: string): boolean {
  for (const character of value) {
    const codePoint = character.codePointAt(0);

    if (
      codePoint !== undefined &&
      (codePoint <= 0x1f ||
        (codePoint >= 0x7f && codePoint <= 0x9f))
    ) {
      return true;
    }
  }

  return false;
}

function readOptionalUrl(
  name: string,
  rawValue: string | undefined,
  allowedProtocols: readonly string[],
  issues: string[]
): URL | undefined {
  if (rawValue === undefined) {
    return undefined;
  }

  if (
    rawValue.length === 0 ||
    rawValue !== rawValue.trim() ||
    containsControlCharacters(rawValue)
  ) {
    issues.push(
      `${name} must be a valid URL without surrounding or control whitespace`
    );
    return undefined;
  }

  let parsed: URL;

  try {
    parsed = new URL(rawValue);
  } catch {
    issues.push(`${name} must be a valid URL`);
    return undefined;
  }

  if (!allowedProtocols.includes(parsed.protocol)) {
    issues.push(
      `${name} must use ${allowedProtocols.join(" or ")} protocol`
    );
    return undefined;
  }

  if (
    parsed.hostname.length === 0 ||
    parsed.hash.length > 0
  ) {
    issues.push(
      `${name} must contain a hostname and must not contain a fragment`
    );
    return undefined;
  }

  return parsed;
}

function readCertificate(
  name: string,
  rawValue: string | undefined,
  issues: string[]
): string | undefined {
  if (rawValue === undefined) {
    return undefined;
  }

  const normalized = rawValue.replace(/\r\n/g, "\n").trim();

  const certificatePattern =
    /-----BEGIN CERTIFICATE-----[\s\S]+?-----END CERTIFICATE-----/g;

  const blocks = normalized.match(certificatePattern);
  const remainder = normalized.replace(certificatePattern, "").trim();

  if (
    normalized.length === 0 ||
    blocks === null ||
    blocks.length === 0 ||
    remainder.length > 0
  ) {
    issues.push(
      `${name} must contain one or more complete PEM certificates`
    );
    return undefined;
  }

  return blocks.join("\n");
}

function readPostgresSettings(
  env: NodeJS.ProcessEnv,
  nodeEnv: NodeEnvironment,
  issues: string[]
): PostgresConnectionSettings | undefined {
  const rawUrl = env.HOMIO_POSTGRES_URL;

  if (rawUrl === undefined && nodeEnv !== "production") {
    return undefined;
  }

  if (rawUrl === undefined) {
    issues.push("HOMIO_POSTGRES_URL is required in production");
    return undefined;
  }

  const parsed = readOptionalUrl(
    "HOMIO_POSTGRES_URL",
    rawUrl,
    ["postgres:", "postgresql:"],
    issues
  );

  if (parsed === undefined) {
    return undefined;
  }

  if (parsed.pathname.length < 2 || parsed.pathname === "/") {
    issues.push(
      "HOMIO_POSTGRES_URL must select a database name"
    );
  }

  if (nodeEnv === "production" && parsed.username.length === 0) {
    issues.push(
      "HOMIO_POSTGRES_URL must specify a dedicated database username in production"
    );
  }

  if (nodeEnv === "production" && parsed.password.length === 0) {
    issues.push(
      "HOMIO_POSTGRES_URL must specify a database password in production"
    );
  }

  for (const parameter of parsed.searchParams.keys()) {
    if (POSTGRES_SSL_QUERY_PARAMETERS.has(parameter.toLowerCase())) {
      issues.push(
        `HOMIO_POSTGRES_URL must not contain ${parameter}; configure TLS through HOMIO_POSTGRES_SSL_MODE and HOMIO_POSTGRES_CA_CERT`
      );
    } else {
      issues.push(
        "HOMIO_POSTGRES_URL query parameters are not accepted; use explicit HOMIO_POSTGRES_* settings"
      );
    }
  }

  const defaultSslMode: PostgresSslMode =
    nodeEnv === "production" ? "verify-full" : "disable";

  const rawSslMode = env.HOMIO_POSTGRES_SSL_MODE ?? defaultSslMode;
  let sslMode: PostgresSslMode = defaultSslMode;

  if (rawSslMode === "disable" || rawSslMode === "verify-full") {
    sslMode = rawSslMode;
  } else {
    issues.push(
      "HOMIO_POSTGRES_SSL_MODE must be disable or verify-full"
    );
  }

  if (nodeEnv === "production" && sslMode !== "verify-full") {
    issues.push(
      "HOMIO_POSTGRES_SSL_MODE must be verify-full in production"
    );
  }

  const caCertificate = readCertificate(
    "HOMIO_POSTGRES_CA_CERT",
    env.HOMIO_POSTGRES_CA_CERT,
    issues
  );

  const poolMax = readInteger(
    "HOMIO_POSTGRES_POOL_MAX",
    env.HOMIO_POSTGRES_POOL_MAX,
    DEFAULT_POSTGRES_POOL_MAX,
    1,
    MAX_POSTGRES_POOL_SIZE,
    issues
  );

  const connectionTimeoutMs = readInteger(
    "HOMIO_POSTGRES_CONNECTION_TIMEOUT_MS",
    env.HOMIO_POSTGRES_CONNECTION_TIMEOUT_MS,
    DEFAULT_POSTGRES_CONNECTION_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    issues
  );

  const idleTimeoutMs = readInteger(
    "HOMIO_POSTGRES_IDLE_TIMEOUT_MS",
    env.HOMIO_POSTGRES_IDLE_TIMEOUT_MS,
    DEFAULT_POSTGRES_IDLE_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
    MAX_POSTGRES_IDLE_TIMEOUT_MS,
    issues
  );

  const statementTimeoutMs = readInteger(
    "HOMIO_POSTGRES_STATEMENT_TIMEOUT_MS",
    env.HOMIO_POSTGRES_STATEMENT_TIMEOUT_MS,
    DEFAULT_POSTGRES_STATEMENT_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    issues
  );

  return Object.freeze({
    connectionString: rawUrl,
    sslMode,
    ...(caCertificate === undefined ? {} : { caCertificate }),
    poolMax,
    connectionTimeoutMs,
    idleTimeoutMs,
    statementTimeoutMs
  });
}

function readRedisSettings(
  env: NodeJS.ProcessEnv,
  nodeEnv: NodeEnvironment,
  issues: string[]
): RedisConnectionSettings | undefined {
  const rawUrl = env.HOMIO_REDIS_URL;

  if (rawUrl === undefined && nodeEnv !== "production") {
    return undefined;
  }

  if (rawUrl === undefined) {
    issues.push("HOMIO_REDIS_URL is required in production");
    return undefined;
  }

  const parsed = readOptionalUrl(
    "HOMIO_REDIS_URL",
    rawUrl,
    ["redis:", "rediss:"],
    issues
  );

  if (parsed === undefined) {
    return undefined;
  }

  if (nodeEnv === "production" && parsed.protocol !== "rediss:") {
    issues.push(
      "HOMIO_REDIS_URL must use rediss:// TLS in production"
    );
  }

  if (nodeEnv === "production" && parsed.password.length === 0) {
    issues.push(
      "HOMIO_REDIS_URL must specify an ACL password in production"
    );
  }

  if (parsed.search.length > 0) {
    issues.push(
      "HOMIO_REDIS_URL query parameters are not accepted; configure connection behavior through explicit HOMIO_REDIS_* settings"
    );
  }

  if (
    parsed.pathname.length > 1 &&
    !/^\/[0-9]+$/.test(parsed.pathname)
  ) {
    issues.push(
      "HOMIO_REDIS_URL database path must be a non-negative integer"
    );
  }

  if (
    parsed.pathname.length > 1 &&
    !Number.isSafeInteger(Number(parsed.pathname.slice(1)))
  ) {
    issues.push(
      "HOMIO_REDIS_URL database index must be a safe integer"
    );
  }

  const caCertificate = readCertificate(
    "HOMIO_REDIS_CA_CERT",
    env.HOMIO_REDIS_CA_CERT,
    issues
  );

  const connectTimeoutMs = readInteger(
    "HOMIO_REDIS_CONNECT_TIMEOUT_MS",
    env.HOMIO_REDIS_CONNECT_TIMEOUT_MS,
    DEFAULT_REDIS_CONNECT_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    issues
  );

  return Object.freeze({
    url: rawUrl,
    ...(caCertificate === undefined ? {} : { caCertificate }),
    connectTimeoutMs
  });
}

export function loadSettings(
  env: NodeJS.ProcessEnv = process.env
): BackendSettings {
  const issues: string[] = [];

  const nodeEnv = readNodeEnvironment(
    env.NODE_ENV,
    issues
  );

  const host = readHost(
    env.HOMIO_BACKEND_HOST,
    issues
  );

  const port = readInteger(
    "HOMIO_BACKEND_PORT",
    env.HOMIO_BACKEND_PORT,
    DEFAULT_PORT,
    1,
    65_535,
    issues
  );

  const logLevel = readLogLevel(
    env.HOMIO_LOG_LEVEL,
    issues
  );

  const requestTimeoutMs = readInteger(
    "HOMIO_REQUEST_TIMEOUT_MS",
    env.HOMIO_REQUEST_TIMEOUT_MS,
    DEFAULT_REQUEST_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    issues
  );

  const shutdownTimeoutMs = readInteger(
    "HOMIO_SHUTDOWN_TIMEOUT_MS",
    env.HOMIO_SHUTDOWN_TIMEOUT_MS,
    DEFAULT_SHUTDOWN_TIMEOUT_MS,
    MIN_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    issues
  );

  const postgres = readPostgresSettings(env, nodeEnv, issues);
  const redis = readRedisSettings(env, nodeEnv, issues);

  if (issues.length > 0) {
    throw new ConfigurationError(issues);
  }

  const common = {
    host,
    port,
    logLevel,
    requestTimeoutMs,
    shutdownTimeoutMs
  };

  if (nodeEnv === "production") {
    if (postgres === undefined || redis === undefined) {
      throw new ConfigurationError([
        "HOMIO_POSTGRES_URL and HOMIO_REDIS_URL are required in production"
      ]);
    }

    return Object.freeze({
      ...common,
      nodeEnv,
      postgres,
      redis
    });
  }

  return Object.freeze({
    ...common,
    nodeEnv,
    ...(postgres === undefined ? {} : { postgres }),
    ...(redis === undefined ? {} : { redis })
  });
}
