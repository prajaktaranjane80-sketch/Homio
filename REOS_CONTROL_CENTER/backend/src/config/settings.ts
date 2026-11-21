
export type NodeEnvironment =
  | "development"
  | "test"
  | "production";

export type LogLevel =
  | "fatal"
  | "error"
  | "warn"
  | "info"
  | "debug"
  | "trace"
  | "silent";

export type PostgresSslMode = "disable" | "verify-full";

export interface PostgresConnectionSettings {
  readonly connectionString: string;
  readonly sslMode: PostgresSslMode;
  readonly caCertificate?: string;
  readonly poolMax: number;
  readonly connectionTimeoutMs: number;
  readonly idleTimeoutMs: number;
  readonly statementTimeoutMs: number;
}

export interface RedisConnectionSettings {
  readonly url: string;
  readonly caCertificate?: string;
  readonly connectTimeoutMs: number;
}

interface BackendCommonSettings {
  readonly host: string;
  readonly port: number;
  readonly logLevel: LogLevel;
  readonly requestTimeoutMs: number;
  readonly shutdownTimeoutMs: number;
}

/**
 * Production settings cannot be represented without both infrastructure
 * endpoints. Development and test may omit them so pure HTTP/security tests
 * remain isolated from external services.
 */
export type BackendSettings = BackendCommonSettings & (
  | {
      readonly nodeEnv: "production";
      readonly postgres: PostgresConnectionSettings;
      readonly redis: RedisConnectionSettings;
    }
  | {
      readonly nodeEnv: "development" | "test";
      readonly postgres?: PostgresConnectionSettings;
      readonly redis?: RedisConnectionSettings;
    }
);
