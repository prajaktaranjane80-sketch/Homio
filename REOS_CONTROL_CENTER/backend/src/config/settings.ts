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

export interface BackendSettings {
  readonly nodeEnv: NodeEnvironment;
  readonly host: string;
  readonly port: number;
  readonly logLevel: LogLevel;
  readonly requestTimeoutMs: number;
  readonly shutdownTimeoutMs: number;
}
