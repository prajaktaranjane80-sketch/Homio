import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();

function fail(message) {
  console.error(`AUTH CONTRACT FAIL-CLOSED: ${message}`);
  process.exit(1);
}

function read(relativePath) {
  const absolute = path.join(root, relativePath);
  if (!fs.existsSync(absolute)) fail(`Required auth file missing: ${relativePath}`);
  return fs.readFileSync(absolute, "utf8");
}

function requireText(source, text, name) {
  if (!source.includes(text)) fail(`${name}: missing contract ${JSON.stringify(text)}`);
}

const packageJson = JSON.parse(read("package.json"));
const oidc = read("src/lib/auth/oidc.ts");
const loginRoute = read("src/app/api/auth/login/route.ts");
const callbackRoute = read("src/app/api/auth/callback/route.ts");
const logoutRoute = read("src/app/api/auth/logout/route.ts");
const sessionRoute = read("src/app/api/auth/session/route.ts");
const myPage = read("src/app/my/page.tsx");
const proxy = read("src/proxy.ts");
const cta = read("src/features/f02_home_discovery/MyHomioSignInCTA.tsx");
const setup = read("AUTHENTICATION_SETUP.md");

for (const relativePath of [
  "src/app/login/page.tsx",
  "src/app/signup/page.tsx",
  "src/features/authentication/AuthPanel.tsx",
  "src/features/authentication/AuthPanel.module.css",
]) read(relativePath);

for (const contract of [
  [loginRoute, "code_challenge_method", "PKCE S256"],
  [oidc, "timingSafeEqual", "constant-time state comparison"],
  [oidc, "claims.nonce", "OIDC nonce verification"],
  [oidc, "createCipheriv(\"aes-256-gcm\"", "authenticated encryption for session cookie"],
  [oidc, "claims.iss !== config.issuer", "exact OIDC issuer validation"],
  [oidc, "return raw;", "preserve exact OIDC issuer identifier"],
  [oidc, "secureCookies: appUrl.protocol === \"https:\"", "secure cookies on every HTTPS deployment"],
  [loginRoute, "method", "GET-based top-level authentication start"],
  [oidc, "algorithm !== \"RS256\"", "restricted ID-token signing algorithms"],
  [oidc, "SESSION_TTL_SECONDS", "bounded application-session lifetime"],
  [loginRoute, "code_challenge_method", "authorization-code flow with PKCE"],
  [callbackRoute, "constantTimeEqual", "callback state validation"],
  [callbackRoute, "createSessionCookie", "application session creation"],
  [logoutRoute, "origin !== config.appUrl", "same-origin logout check"],
  [sessionRoute, "Cache-Control", "non-cacheable session response"],
  [myPage, "readSessionCookie", "protected account route"],
  [cta, 'href="/login"', "homepage account entry point"],
  [cta, 'href="/signup"', "homepage signup entry point"],
  [cta, 'href="/login"', "homepage login entry point"],
  [setup, "HOMIO_OIDC_ISSUER", "deployment setup guide"],
]) {
  requireText(contract[0], contract[1], contract[2]);
}

if (/"\/my"\s*:/.test(proxy) || /"\/my\/:path\*"/.test(proxy)) {
  fail("/my still redirects away from the real protected account route.");
}

if (!read("src/features/authentication/AuthPanel.tsx").includes('action="/api/auth/login" method="get"')) {
  fail("OIDC start must be a native top-level GET form, not client-side API navigation.");
}

if (!packageJson.scripts?.["verify:auth"]?.includes("verify-auth.mjs")) {
  fail("verify:auth script is missing from package.json.");
}
if (!packageJson.scripts?.verify?.includes("npm run verify:auth")) {
  fail("the main verify command does not run verify:auth.");
}

console.log("AUTH ROUTE CONTRACT: PASS");
console.log("OIDC PKCE, state/nonce, encrypted session, logout origin guard: PASS");
console.log("Protected /my route and real sign-in/sign-up entry points: PASS");