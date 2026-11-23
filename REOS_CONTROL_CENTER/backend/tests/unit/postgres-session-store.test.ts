import { createHash } from "node:crypto";

import {
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  PostgresSessionConflictError,
  PostgresSessionStore,
  PostgresSessionUnavailableError
} from "../../src/persistence/postgres-session-store.js";
import type { PostgresRuntime } from "../../src/persistence/postgres.js";
import {
  TEST_CONTEXT,
  TEST_PRINCIPAL
} from "../helpers/security-runtime.js";

interface QueryCall {
  readonly sql: string;
  readonly values: readonly unknown[] | undefined;
}

function createFixture(options: {
  readonly rows?: readonly { readonly session_id: string }[];
  readonly fail?: boolean;
} = {}) {
  const calls: QueryCall[] = [];

  const query = vi.fn(async (
    sql: string,
    values?: unknown[]
  ) => {
    calls.push({
      sql,
      values: values === undefined ? undefined : [...values]
    });

    if (options.fail === true) {
      throw new Error("database failure");
    }

    return {
      rows: options.rows ?? [
        { session_id: "77777777-7777-4777-8777-777777777777" }
      ],
      rowCount: options.rows?.length ?? 1
    };
  });

  const transaction = {
    tenantId: TEST_CONTEXT.tenantId,
    query
  };

  const withTenantTransaction = vi.fn(
    async (
      _context: unknown,
      work: (value: typeof transaction) => Promise<unknown>,
      _options?: unknown
    ) => work(transaction)
  );

  const postgres = {
    withTenantTransaction
  } as unknown as PostgresRuntime;

  return {
    store: new PostgresSessionStore(postgres),
    calls,
    query,
    withTenantTransaction
  };
}

function sha256(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

describe("PostgresSessionStore", () => {
  it("stores only issuer and token-ID digests with canonical account and authentication epoch", async () => {
    const fixture = createFixture();

    const sessionId = await fixture.store.establishSession({
      principal: TEST_PRINCIPAL,
      context: TEST_CONTEXT
    });

    expect(sessionId).toBe("77777777-7777-4777-8777-777777777777");
    expect(fixture.withTenantTransaction).toHaveBeenCalledTimes(1);
    expect(fixture.withTenantTransaction.mock.calls[0]?.[0]).toEqual({
      tenantId: TEST_CONTEXT.tenantId
    });

    const insertCall = fixture.calls[0];

    expect(insertCall?.sql).toContain(
      "INSERT INTO reos_infra.api_sessions"
    );

    expect(insertCall?.values?.[1]).toBe(TEST_CONTEXT.tenantId);
    expect(insertCall?.values?.[2]).toBe(TEST_CONTEXT.accountId);
    expect(insertCall?.values?.[3]).toBe(TEST_CONTEXT.identityId);
    expect(insertCall?.values?.[7]).toBe(TEST_CONTEXT.membershipRevision);
    expect(insertCall?.values?.[8]).toBe(sha256(TEST_PRINCIPAL.issuer));
    expect(insertCall?.values?.[9]).toBe(sha256(TEST_PRINCIPAL.tokenId));
    expect(insertCall?.values?.[10]).toBe(TEST_CONTEXT.authenticationEpoch);

    const serialized = JSON.stringify(insertCall?.values);

    expect(serialized).not.toContain(TEST_PRINCIPAL.issuer);
    expect(serialized).not.toContain(TEST_PRINCIPAL.tokenId);
    expect(serialized).not.toContain("test-bearer-token");
  });

  it("checks exact tenant, account, membership, token and authentication epoch", async () => {
    const fixture = createFixture();

    const active = await fixture.store.isSessionActive({
      principal: TEST_PRINCIPAL,
      context: TEST_CONTEXT
    });

    expect(active).toBe(true);
    expect(fixture.withTenantTransaction).toHaveBeenCalledTimes(1);
    expect(fixture.withTenantTransaction.mock.calls[0]?.[2]).toEqual({
      readOnly: true
    });

    const selectCall = fixture.calls[0];

    expect(selectCall?.sql).toContain(
      "AND authentication_epoch = $10"
    );
    expect(selectCall?.sql).toContain(
      "AND revoked_at IS NULL"
    );
    expect(selectCall?.values?.[9]).toBe(
      TEST_CONTEXT.authenticationEpoch
    );
    expect(selectCall?.values?.[2]).toBe(
      TEST_CONTEXT.identityId
    );
    expect(selectCall?.values?.[5]).toBe(
      TEST_CONTEXT.membershipId
    );
  });

  it("rejects a token principal without verified iat and exp", async () => {
    const fixture = createFixture();

    const {
      issuedAtEpochSeconds: _issuedAt,
      expiresAtEpochSeconds: _expiresAt,
      ...withoutTemporalClaims
    } = TEST_PRINCIPAL;

    await expect(
      fixture.store.establishSession({
        principal: withoutTemporalClaims,
        context: TEST_CONTEXT
      })
    ).rejects.toThrow(
      "Verified issuer, token ID, iat and exp claims are required."
    );

    expect(fixture.query).not.toHaveBeenCalled();
  });

  it("rejects an expired token before writing a session", async () => {
    const fixture = createFixture();

    const expiredPrincipal = {
      ...TEST_PRINCIPAL,
      issuedAtEpochSeconds: 1_600_000_000,
      expiresAtEpochSeconds: 1_600_000_030
    };

    await expect(
      fixture.store.establishSession({
        principal: expiredPrincipal,
        context: TEST_CONTEXT
      })
    ).rejects.toThrow(
      "An expired verified token cannot establish a session."
    );

    expect(fixture.query).not.toHaveBeenCalled();
  });

  it("rejects a context without a positive authentication epoch", async () => {
    const fixture = createFixture();

    await expect(
      fixture.store.establishSession({
        principal: TEST_PRINCIPAL,
        context: {
          ...TEST_CONTEXT,
          authenticationEpoch: 0
        }
      })
    ).rejects.toThrow(
      "A complete trusted CORE-001 account and tenant context is required."
    );

    expect(fixture.query).not.toHaveBeenCalled();
  });

  it("does not silently register a duplicate token session", async () => {
    const fixture = createFixture({
      rows: []
    });

    await expect(
      fixture.store.establishSession({
        principal: TEST_PRINCIPAL,
        context: TEST_CONTEXT
      })
    ).rejects.toBeInstanceOf(PostgresSessionConflictError);
  });

  it("revokes a specific session idempotently", async () => {
    const fixture = createFixture();

    const revoked = await fixture.store.revokeSession({
      principal: TEST_PRINCIPAL,
      context: TEST_CONTEXT,
      reasonCode: "USER_LOGOUT"
    });

    expect(revoked).toBe(true);
    expect(fixture.calls[0]?.sql).toContain(
      "UPDATE reos_infra.api_sessions"
    );
    expect(fixture.calls[0]?.values?.[4]).toBe("USER_LOGOUT");
  });

  it("revokes all active sessions for the canonical account", async () => {
    const fixture = createFixture({
      rows: [
        { session_id: "77777777-7777-4777-8777-777777777777" },
        { session_id: "88888888-8888-4888-8888-888888888888" }
      ]
    });

    const revokedCount = await fixture.store.revokeAccountSessions({
      context: TEST_CONTEXT,
      reasonCode: "ACCOUNT_EPOCH_ROTATED"
    });

    expect(revokedCount).toBe(2);
    expect(fixture.calls[0]?.sql).toContain(
      "AND revoked_at IS NULL"
    );
    expect(fixture.calls[0]?.values).toEqual([
      TEST_CONTEXT.tenantId,
      TEST_CONTEXT.accountId,
      "ACCOUNT_EPOCH_ROTATED"
    ]);
  });

  it("normalizes database errors without exposing driver details", async () => {
    const fixture = createFixture({
      fail: true
    });

    await expect(
      fixture.store.isSessionActive({
        principal: TEST_PRINCIPAL,
        context: TEST_CONTEXT
      })
    ).rejects.toBeInstanceOf(PostgresSessionUnavailableError);
  });
});
