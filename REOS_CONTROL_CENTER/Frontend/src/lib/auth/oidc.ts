import {
  createCipheriv,
  createDecipheriv,
  createHash,
  createPublicKey,
  randomBytes,
  timingSafeEqual,
  verify as verifySignature,
} from "node:crypto";

export const SESSION_COOKIE = "homio_session";
export const SESSION_TTL_SECONDS = 8 * 60 * 60;
export const AUTH_COOKIE_PATH = "/api/auth/callback";
export const AUTH_TRANSIENT_COOKIE_NAMES = [
  "homio_auth_state",
  "homio_auth_nonce",
  "homio_auth_verifier",
  "homio_auth_return_to",
  "homio_auth_intent",
] as const;

export class AuthConfigurationError extends Error {
  constructor() {
    super("Authentication is not configured.");
    this.name = "AuthConfigurationError";
  }
}

export class AuthFlowError extends Error {
  constructor() {
    super("Authentication could not be completed.");
    this.name = "AuthFlowError";
  }
}

export type AuthConfig = Readonly<{
  issuer: string;
  clientId: string;
  clientSecret?: string;
  appUrl: string;
  sessionSecret: string;
  secureCookies: boolean;
}>;

export type AuthenticatedSession = Readonly<{
  issuer: string;
  sub: string;
  email?: string;
  name?: string;
  emailVerified: boolean;
  issuedAt: number;
  expiresAt: number;
}>;

type OidcDiscovery = {
  issuer?: unknown;
  authorization_endpoint?: unknown;
  token_endpoint?: unknown;
  jwks_uri?: unknown;
  response_types_supported?: unknown;
  code_challenge_methods_supported?: unknown;
};

type TrustedOidcDiscovery = OidcDiscovery & {
  authorization_endpoint: string;
  token_endpoint: string;
  jwks_uri: string;
};

type OidcJwk = JsonWebKey & {
  kid?: unknown;
  use?: unknown;
  alg?: unknown;
  key_ops?: unknown;
  kty?: unknown;
  crv?: unknown;
  n?: unknown;
  e?: unknown;
  x?: unknown;
  y?: unknown;
};

type OidcClaims = {
  iss?: unknown;
  aud?: unknown;
  sub?: unknown;
  exp?: unknown;
  iat?: unknown;
  nbf?: unknown;
  nonce?: unknown;
  azp?: unknown;
  email?: unknown;
  email_verified?: unknown;
  name?: unknown;
};

let discoveryCache: {
  issuer: string;
  expiresAt: number;
  value: TrustedOidcDiscovery;
} | undefined;

let jwksCache: {
  url: string;
  expiresAt: number;
  keys: OidcJwk[];
} | undefined;

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (!value || value.trim() !== value || !value.trim()) {
    throw new AuthConfigurationError();
  }
  return value;
}

function parseHttpsUrl(raw: string): string {
  let value: URL;
  try {
    value = new URL(raw);
  } catch {
    throw new AuthConfigurationError();
  }
  if (
    value.protocol !== "https:" ||
    !value.hostname ||
    value.username ||
    value.password ||
    value.search ||
    value.hash
  ) {
    throw new AuthConfigurationError();
  }
  // Preserve the exact issuer identifier; URL#toString normalizes host-only
  // issuers with a trailing slash, which can break exact OIDC issuer matching.
  return raw;
}

export function getAuthConfig(): AuthConfig {
  const issuer = parseHttpsUrl(requiredEnvironment("HOMIO_OIDC_ISSUER"));
  const clientId = requiredEnvironment("HOMIO_OIDC_CLIENT_ID");
  const appUrlRaw = requiredEnvironment("HOMIO_APP_URL");
  const sessionSecret = requiredEnvironment("HOMIO_SESSION_SECRET");

  let appUrl: URL;
  try {
    appUrl = new URL(appUrlRaw);
  } catch {
    throw new AuthConfigurationError();
  }

  const localHost = ["localhost", "127.0.0.1", "::1"].includes(
    appUrl.hostname.toLowerCase(),
  );
  const isLocalHttp = appUrl.protocol === "http:" && localHost;

  if (
    appUrl.username ||
    appUrl.password ||
    appUrl.pathname !== "/" ||
    appUrl.search ||
    appUrl.hash ||
    (appUrl.protocol !== "https:" && !isLocalHttp) ||
    (process.env.NODE_ENV === "production" && appUrl.protocol !== "https:") ||
    clientId.length > 512 ||
    Buffer.byteLength(sessionSecret, "utf8") < 32
  ) {
    throw new AuthConfigurationError();
  }

  const clientSecret = process.env.HOMIO_OIDC_CLIENT_SECRET;
  if (clientSecret !== undefined && (!clientSecret || clientSecret.trim() !== clientSecret)) {
    throw new AuthConfigurationError();
  }

  return {
    issuer,
    clientId,
    clientSecret,
    appUrl: appUrl.origin,
    sessionSecret,
    secureCookies: appUrl.protocol === "https:",
  };
}

export function isAuthConfigured(): boolean {
  try {
    getAuthConfig();
    return true;
  } catch {
    return false;
  }
}

function trustedEndpoint(raw: unknown): string {
  if (typeof raw !== "string" || raw.length > 2048) {
    throw new AuthFlowError();
  }
  let endpoint: URL;
  try {
    endpoint = new URL(raw);
  } catch {
    throw new AuthFlowError();
  }
  if (
    endpoint.protocol !== "https:" ||
    !endpoint.hostname ||
    endpoint.username ||
    endpoint.password ||
    endpoint.hash
  ) {
    throw new AuthFlowError();
  }
  return endpoint.toString();
}

async function getJson(
  url: string,
  init?: RequestInit,
): Promise<Record<string, unknown>> {
  try {
    const headers = new Headers(init?.headers);
    headers.set("Accept", "application/json");
    const response = await fetch(url, {
      ...init,
      headers,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      throw new AuthFlowError();
    }
    const value: unknown = await response.json();
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new AuthFlowError();
    }
    return value as Record<string, unknown>;
  } catch {
    throw new AuthFlowError();
  }
}

export async function getOidcDiscovery(
  config: AuthConfig = getAuthConfig(),
): Promise<TrustedOidcDiscovery> {
  if (
    discoveryCache &&
    discoveryCache.issuer === config.issuer &&
    discoveryCache.expiresAt > Date.now()
  ) {
    return discoveryCache.value;
  }

  const base = config.issuer.endsWith("/")
    ? config.issuer
    : `${config.issuer}/`;
  const metadataUrl = new URL(".well-known/openid-configuration", base).toString();
  const raw = (await getJson(metadataUrl)) as OidcDiscovery;

  if (raw.issuer !== config.issuer) {
    throw new AuthFlowError();
  }

  const authorization_endpoint = trustedEndpoint(raw.authorization_endpoint);
  const token_endpoint = trustedEndpoint(raw.token_endpoint);
  const jwks_uri = trustedEndpoint(raw.jwks_uri);

  if (
    !Array.isArray(raw.response_types_supported) ||
    !raw.response_types_supported.includes("code") ||
    !Array.isArray(raw.code_challenge_methods_supported) ||
    !raw.code_challenge_methods_supported.includes("S256")
  ) {
    throw new AuthFlowError();
  }

  const value = { ...raw, authorization_endpoint, token_endpoint, jwks_uri };
  discoveryCache = {
    issuer: config.issuer,
    expiresAt: Date.now() + 5 * 60 * 1000,
    value,
  };
  return value;
}

export function randomToken(bytes = 32): string {
  return randomBytes(bytes).toString("base64url");
}

export function pkceChallenge(verifier: string): string {
  return createHash("sha256").update(verifier, "ascii").digest("base64url");
}

export function constantTimeEqual(left: string, right: string): boolean {
  const a = Buffer.from(left, "utf8");
  const b = Buffer.from(right, "utf8");
  return a.length === b.length && timingSafeEqual(a, b);
}


export function safeReturnTo(value: string | undefined | null): string {
  if (value === "/" || value === "/my") {
    return value;
  }

  if (
    typeof value === "string" &&
    /^\/transaction\/[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value)
  ) {
    return value;
  }

  return "/my";
}


async function getJwks(url: string): Promise<OidcJwk[]> {
  if (jwksCache && jwksCache.url === url && jwksCache.expiresAt > Date.now()) {
    return jwksCache.keys;
  }
  const response = await getJson(url);
  if (!Array.isArray(response.keys) || response.keys.length > 100) {
    throw new AuthFlowError();
  }
  const keys = response.keys.filter(
    (key): key is OidcJwk => !!key && typeof key === "object" && !Array.isArray(key),
  );
  jwksCache = { url, expiresAt: Date.now() + 5 * 60 * 1000, keys };
  return keys;
}

function publicKeyFor(jwk: OidcJwk, algorithm: string) {
  if (algorithm === "RS256") {
    if (jwk.kty !== "RSA" || typeof jwk.n !== "string" || typeof jwk.e !== "string") {
      throw new AuthFlowError();
    }
    return createPublicKey({
      key: { kty: "RSA", n: jwk.n, e: jwk.e },
      format: "jwk",
    });
  }
  if (
    algorithm === "ES256" &&
    jwk.kty === "EC" &&
    jwk.crv === "P-256" &&
    typeof jwk.x === "string" &&
    typeof jwk.y === "string"
  ) {
    return createPublicKey({
      key: { kty: "EC", crv: "P-256", x: jwk.x, y: jwk.y },
      format: "jwk",
    });
  }
  throw new AuthFlowError();
}

async function verifyIdToken(
  token: string,
  config: AuthConfig,
  nonce: string,
): Promise<Omit<AuthenticatedSession, "issuedAt" | "expiresAt">> {
  if (typeof token !== "string" || token.length > 16384) {
    throw new AuthFlowError();
  }
  const parts = token.split(".");
  if (parts.length !== 3 || !parts[2]) {
    throw new AuthFlowError();
  }
  const header = decodeJwtJson(parts[0]);
  const claims = decodeJwtJson(parts[1]) as OidcClaims;
  const algorithm = header.alg;
  const kid = header.kid;

  if (
    (algorithm !== "RS256" && algorithm !== "ES256") ||
    typeof kid !== "string" ||
    !kid ||
    kid.length > 255 ||
    header.crit !== undefined ||
    (header.typ !== undefined && header.typ !== "JWT")
  ) {
    throw new AuthFlowError();
  }

  const discovery = await getOidcDiscovery(config);
  const keys = await getJwks(discovery.jwks_uri);
  const jwk = keys.find(
    (candidate) =>
      candidate.kid === kid &&
      (candidate.use === undefined || candidate.use === "sig") &&
      (candidate.alg === undefined || candidate.alg === algorithm) &&
      (!Array.isArray(candidate.key_ops) || candidate.key_ops.includes("verify")),
  );
  if (!jwk) {
    throw new AuthFlowError();
  }

  let signature: Buffer;
  try {
    signature = Buffer.from(parts[2], "base64url");
  } catch {
    throw new AuthFlowError();
  }
  const signingInput = Buffer.from(`${parts[0]}.${parts[1]}`, "ascii");
  const publicKey = publicKeyFor(jwk, algorithm);
  const keyInput = algorithm === "ES256"
    ? { key: publicKey, dsaEncoding: "ieee-p1363" as const }
    : publicKey;

  let validSignature = false;
  try {
    validSignature = verifySignature(
      algorithm === "RS256" ? "RSA-SHA256" : "sha256",
      signingInput,
      keyInput,
      signature,
    );
  } catch {
    throw new AuthFlowError();
  }
  if (!validSignature) {
    throw new AuthFlowError();
  }

  const now = Math.floor(Date.now() / 1000);
  const audience = claims.aud;
  const audiences = typeof audience === "string"
    ? [audience]
    : Array.isArray(audience) && audience.every((entry) => typeof entry === "string")
      ? audience
      : [];

  if (
    claims.iss !== config.issuer ||
    !audiences.includes(config.clientId) ||
    (audiences.length > 1 && claims.azp !== config.clientId) ||
    (claims.azp !== undefined && claims.azp !== config.clientId) ||
    typeof claims.sub !== "string" ||
    !claims.sub.trim() ||
    claims.sub.length > 255 ||
    typeof claims.exp !== "number" ||
    claims.exp <= now - 60 ||
    typeof claims.iat !== "number" ||
    claims.iat > now + 60 ||
    (claims.nbf !== undefined &&
      (typeof claims.nbf !== "number" || claims.nbf > now + 60)) ||
    typeof claims.nonce !== "string" ||
    !constantTimeEqual(claims.nonce, nonce)
  ) {
    throw new AuthFlowError();
  }

  const email = typeof claims.email === "string" && claims.email.trim().length <= 254
    ? claims.email.trim()
    : undefined;
  const name = typeof claims.name === "string" && claims.name.trim()
    ? claims.name.trim().slice(0, 120)
    : undefined;

  return {
    issuer: config.issuer,
    sub: claims.sub,
    email,
    name,
    emailVerified: claims.email_verified === true,
  };
}

function formEncode(value: string): string {
  return new URLSearchParams({ value }).toString().slice("value=".length);
}

export async function exchangeAuthorizationCode(
  code: string,
  verifier: string,
  nonce: string,
): Promise<AuthenticatedSession> {
  if (!code || code.length > 4096 || !verifier || verifier.length > 128 || !nonce) {
    throw new AuthFlowError();
  }
  const config = getAuthConfig();
  const discovery = await getOidcDiscovery(config);
  const redirectUri = `${config.appUrl}/api/auth/callback`;
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri,
    code_verifier: verifier,
  });
  const headers = new Headers({ "Content-Type": "application/x-www-form-urlencoded" });

  if (config.clientSecret) {
    const credentials = `${formEncode(config.clientId)}:${formEncode(config.clientSecret)}`;
    headers.set("Authorization", `Basic ${Buffer.from(credentials, "ascii").toString("base64")}`);
  } else {
    body.set("client_id", config.clientId);
  }

  const response = await getJson(discovery.token_endpoint, {
    method: "POST",
    headers,
    body: body.toString(),
  });
  if (typeof response.id_token !== "string") {
    throw new AuthFlowError();
  }

  const identity = await verifyIdToken(response.id_token, config, nonce);
  const issuedAt = Math.floor(Date.now() / 1000);
  return {
    ...identity,
    issuedAt,
    expiresAt: issuedAt + SESSION_TTL_SECONDS,
  };
}

export function createSessionCookie(
  session: AuthenticatedSession,
  config: AuthConfig = getAuthConfig(),
): string {
  const iv = randomBytes(12);
  const key = createHash("sha256").update(config.sessionSecret, "utf8").digest();
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  cipher.setAAD(Buffer.from("homio-session-v1", "ascii"));
  const encrypted = Buffer.concat([
    cipher.update(JSON.stringify(session), "utf8"),
    cipher.final(),
  ]);
  const tag = cipher.getAuthTag();
  return [iv, encrypted, tag].map((part) => part.toString("base64url")).join(".");
}

export function readSessionCookie(value: string | undefined): AuthenticatedSession | null {
  if (!value || value.length > 3500) {
    return null;
  }
  try {
    const config = getAuthConfig();
    const parts = value.split(".");
    if (parts.length !== 3) {
      return null;
    }
    const [ivPart, encryptedPart, tagPart] = parts;
    const iv = Buffer.from(ivPart, "base64url");
    const encrypted = Buffer.from(encryptedPart, "base64url");
    const tag = Buffer.from(tagPart, "base64url");
    if (iv.length !== 12 || tag.length !== 16) {
      return null;
    }
    const key = createHash("sha256").update(config.sessionSecret, "utf8").digest();
    const decipher = createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAAD(Buffer.from("homio-session-v1", "ascii"));
    decipher.setAuthTag(tag);
    const plain = Buffer.concat([decipher.update(encrypted), decipher.final()]).toString("utf8");
    const session: unknown = JSON.parse(plain);
    if (!session || typeof session !== "object" || Array.isArray(session)) {
      return null;
    }
    const valueRecord = session as Record<string, unknown>;
    const now = Math.floor(Date.now() / 1000);
    if (
      valueRecord.issuer !== config.issuer ||
      typeof valueRecord.sub !== "string" ||
      !valueRecord.sub ||
      typeof valueRecord.issuedAt !== "number" ||
      valueRecord.issuedAt > now + 60 ||
      typeof valueRecord.expiresAt !== "number" ||
      valueRecord.expiresAt <= now ||
      valueRecord.expiresAt - valueRecord.issuedAt > SESSION_TTL_SECONDS ||
      typeof valueRecord.emailVerified !== "boolean" ||
      (valueRecord.email !== undefined && typeof valueRecord.email !== "string") ||
      (valueRecord.name !== undefined && typeof valueRecord.name !== "string")
    ) {
      return null;
    }
    return valueRecord as unknown as AuthenticatedSession;
  } catch {
    return null;
  }
}
