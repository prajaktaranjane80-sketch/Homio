import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test, { after } from "node:test";
import ts from "typescript";
import { pathToFileURL } from "node:url";

const envNames = [
  "NODE_ENV",
  "HOMIO_APP_URL",
  "HOMIO_OIDC_ISSUER",
  "HOMIO_OIDC_CLIENT_ID",
  "HOMIO_SESSION_SECRET",
  "HOMIO_OIDC_CLIENT_SECRET",
];
const originalEnv = Object.fromEntries(
  envNames.map((name) => [name, process.env[name]]),
);

process.env.NODE_ENV = "test";
process.env.HOMIO_APP_URL = "https://homio.example.test";
process.env.HOMIO_OIDC_ISSUER = "https://issuer.example.test";
process.env.HOMIO_OIDC_CLIENT_ID = "homio-runtime-test-client";
process.env.HOMIO_SESSION_SECRET =
  "test-only-secret-that-is-at-least-thirty-two-bytes-long";
delete process.env.HOMIO_OIDC_CLIENT_SECRET;

const sourcePath = path.join(process.cwd(), "src/lib/auth/oidc.ts");
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "homio-auth-runtime-"));
const modulePath = path.join(tempDir, "oidc.mjs");

const source = fs.readFileSync(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
  },
  reportDiagnostics: true,
});
const syntaxErrors = (compiled.diagnostics ?? []).filter(
  (item) => item.category === ts.DiagnosticCategory.Error,
);
assert.equal(
  syntaxErrors.length,
  0,
  syntaxErrors.map((item) =>
    ts.flattenDiagnosticMessageText(item.messageText, "\n"),
  ).join("\n"),
);
fs.writeFileSync(modulePath, compiled.outputText, "utf8");

const auth = await import(pathToFileURL(modulePath).href);
const now = Math.floor(Date.now() / 1000);
const baseSession = {
  issuer: "https://issuer.example.test",
  sub: "provider-subject-123",
  email: "person@example.test",
  name: "HOMIO Runtime Test",
  emailVerified: true,
  issuedAt: now,
  expiresAt: now + auth.SESSION_TTL_SECONDS,
};

after(() => {
  fs.rmSync(tempDir, { recursive: true, force: true });
  for (const name of envNames) {
    if (originalEnv[name] === undefined) delete process.env[name];
    else process.env[name] = originalEnv[name];
  }
});

test("PKCE S256 matches the RFC 7636 known vector", () => {
  assert.equal(
    auth.pkceChallenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"),
    "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
  );
});

test("random tokens have the expected safe format and are not repeated", () => {
  const first = auth.randomToken(32);
  const second = auth.randomToken(32);
  assert.match(first, /^[A-Za-z0-9_-]+$/);
  assert.equal(first.length, 43);
  assert.notEqual(first, second);
});

test("state comparison handles equal, unequal, and different-length values", () => {
  assert.equal(auth.constantTimeEqual("state-token", "state-token"), true);
  assert.equal(auth.constantTimeEqual("state-token", "other-token"), false);
  assert.equal(auth.constantTimeEqual("short", "longer"), false);
});

test("return target cannot redirect to an external URL", () => {
  assert.equal(auth.safeReturnTo("/"), "/");
  assert.equal(auth.safeReturnTo("/my"), "/my");
  assert.equal(auth.safeReturnTo("https://attacker.example"), "/my");
  assert.equal(auth.safeReturnTo("//attacker.example"), "/my");
  assert.equal(auth.safeReturnTo(undefined), "/my");
});

test("configuration rejects a short session secret", () => {
  const previous = process.env.HOMIO_SESSION_SECRET;
  try {
    process.env.HOMIO_SESSION_SECRET = "short";
    assert.throws(() => auth.getAuthConfig(), auth.AuthConfigurationError);
  } finally {
    process.env.HOMIO_SESSION_SECRET = previous;
  }
});

test("production configuration rejects insecure HTTP URLs", () => {
  const previousNodeEnv = process.env.NODE_ENV;
  const previousAppUrl = process.env.HOMIO_APP_URL;
  try {
    process.env.NODE_ENV = "production";
    process.env.HOMIO_APP_URL = "http://localhost:3000";
    assert.throws(() => auth.getAuthConfig(), auth.AuthConfigurationError);
  } finally {
    process.env.NODE_ENV = previousNodeEnv;
    process.env.HOMIO_APP_URL = previousAppUrl;
  }
});

test("encrypted session cookie round-trips a valid session", () => {
  const cookie = auth.createSessionCookie(baseSession, auth.getAuthConfig());
  assert.equal(cookie.split(".").length, 3);
  assert.deepEqual(auth.readSessionCookie(cookie), baseSession);
});

test("session cookie rejects tampering, malformed data, and oversized values", () => {
  const cookie = auth.createSessionCookie(baseSession, auth.getAuthConfig());
  const parts = cookie.split(".");
  parts[0] = `${parts[0][0] === "A" ? "B" : "A"}${parts[0].slice(1)}`;
  assert.equal(auth.readSessionCookie(parts.join(".")), null);
  assert.equal(auth.readSessionCookie("not-a-session"), null);
  assert.equal(auth.readSessionCookie("x".repeat(3501)), null);
  assert.equal(auth.readSessionCookie(undefined), null);
});

test("session cookie rejects wrong secrets and issuer values", () => {
  const cookie = auth.createSessionCookie(baseSession, auth.getAuthConfig());
  const previousSecret = process.env.HOMIO_SESSION_SECRET;
  try {
    process.env.HOMIO_SESSION_SECRET =
      "another-test-only-secret-that-is-also-more-than-thirty-two-bytes";
    assert.equal(auth.readSessionCookie(cookie), null);
  } finally {
    process.env.HOMIO_SESSION_SECRET = previousSecret;
  }

  const wrongIssuer = auth.createSessionCookie(
    { ...baseSession, issuer: "https://other-issuer.example.test" },
    auth.getAuthConfig(),
  );
  assert.equal(auth.readSessionCookie(wrongIssuer), null);
});

test("session cookie rejects expired and future-issued sessions", () => {
  const config = auth.getAuthConfig();
  const expired = auth.createSessionCookie(
    { ...baseSession, issuedAt: now - 9000, expiresAt: now - 1 },
    config,
  );
  const futureIssued = auth.createSessionCookie(
    { ...baseSession, issuedAt: now + 120, expiresAt: now + 300 },
    config,
  );
  assert.equal(auth.readSessionCookie(expired), null);
  assert.equal(auth.readSessionCookie(futureIssued), null);
});