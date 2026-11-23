declare module "pg" {
  export interface QueryResult<Row = Record<string, unknown>> {
    readonly rows: Row[];
    readonly rowCount: number | null;
  }

  export interface PoolConfig {
    readonly connectionString?: string | undefined;
    readonly max?: number | undefined;
    readonly connectionTimeoutMillis?: number | undefined;
    readonly idleTimeoutMillis?: number | undefined;
  }

  export interface PoolClient {
    query<Row = Record<string, unknown>>(
      text: string,
      values?: readonly unknown[]
    ): Promise<QueryResult<Row>>;

    release(error?: Error | boolean): void;
  }

  export class Pool {
    constructor(config?: PoolConfig);

    query<Row = Record<string, unknown>>(
      text: string,
      values?: readonly unknown[]
    ): Promise<QueryResult<Row>>;

    connect(): Promise<PoolClient>;

    end(): Promise<void>;
  }
}
