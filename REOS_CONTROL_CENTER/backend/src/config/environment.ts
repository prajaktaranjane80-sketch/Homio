import type {
  BackendSettings,
  LogLevel,
  NodeEnvironment
} from "./settings.js";

const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 3001;
const DEFAULT_LOG_LEVEL: LogLevel = "info";

const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;
const DEFAULT_SHUTDOWN_TIMEOUT_MS = 10_000;

const MIN_TIMEOUT_MS = 1_000;
const MAX_TIMEOUT_MS = 120_000;

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

export class ConfigurationError extends Error {
  public readonly issues: readonly string[];

  public constructor(issues: readonly string[]) {
    super(
      `Invalid backend runtime configuration: ${issues.join("; ")}`
    );

    this.name = "ConfigurationError";
    this.issues = Object.freeze([...issues]);
  }
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

  if (value.length === 0 || value !== rawValue) {
    issues.push(
      "HOMIO_BACKEND_HOST must be a non-empty host without surrounding whitespace"
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

  if (issues.length > 0) {
    throw new ConfigurationError(issues);
  }

  return Object.freeze({
    nodeEnv,
    host,
    port,
    logLevel,
    requestTimeoutMs,
    shutdownTimeoutMs
  });
}
