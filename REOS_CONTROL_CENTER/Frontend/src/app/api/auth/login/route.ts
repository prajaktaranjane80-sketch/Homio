import { NextResponse, type NextRequest } from "next/server";

import {
  AUTH_COOKIE_PATH,
  AuthConfigurationError,
  getAuthConfig,
  getOidcDiscovery,
  pkceChallenge,
  randomToken,
  safeReturnTo,
} from "@/lib/auth/oidc";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  let config: ReturnType<typeof getAuthConfig> | undefined;
  let intent: "login" | "signup" = request.nextUrl.searchParams.get("intent") === "signup"
    ? "signup"
    : "login";

  try {
    config = getAuthConfig();
    const discovery = await getOidcDiscovery(config);
    const returnTo = safeReturnTo(request.nextUrl.searchParams.get("returnTo"));
    const state = randomToken(32);
    const nonce = randomToken(32);
    const verifier = randomToken(48);
    const authorizationUrl = new URL(discovery.authorization_endpoint);

    authorizationUrl.searchParams.set("response_type", "code");
    authorizationUrl.searchParams.set("client_id", config.clientId);
    authorizationUrl.searchParams.set(
      "redirect_uri",
      `${config.appUrl}/api/auth/callback`,
    );
    authorizationUrl.searchParams.set("scope", "openid profile email");
    authorizationUrl.searchParams.set("state", state);
    authorizationUrl.searchParams.set("nonce", nonce);
    authorizationUrl.searchParams.set("code_challenge", pkceChallenge(verifier));
    authorizationUrl.searchParams.set("code_challenge_method", "S256");

    // Signup is provider-specific; some providers support the screen_hint extension.
    if (intent === "signup") {
      authorizationUrl.searchParams.set("screen_hint", "signup");
    }

    const response = NextResponse.redirect(authorizationUrl);
    response.headers.set("Cache-Control", "no-store");
    response.headers.set("Referrer-Policy", "no-referrer");

    const cookieOptions = {
      httpOnly: true,
      secure: config.secureCookies,
      sameSite: "lax" as const,
      path: AUTH_COOKIE_PATH,
      maxAge: 600,
    };
    response.cookies.set("homio_auth_state", state, cookieOptions);
    response.cookies.set("homio_auth_nonce", nonce, cookieOptions);
    response.cookies.set("homio_auth_verifier", verifier, cookieOptions);
    response.cookies.set("homio_auth_return_to", returnTo, cookieOptions);
    response.cookies.set("homio_auth_intent", intent, cookieOptions);
    return response;
  } catch (error) {
    if (config) {
      const destination = intent === "signup" ? "/signup" : "/login";
      const response = NextResponse.redirect(
        new URL(`${destination}?error=provider-unavailable`, config.appUrl),
      );
      response.headers.set("Cache-Control", "no-store");
      return response;
    }
    const status = error instanceof AuthConfigurationError ? 503 : 502;
    return NextResponse.json(
      {
        error: error instanceof AuthConfigurationError
          ? "authentication_not_configured"
          : "identity_provider_unavailable",
        message: error instanceof AuthConfigurationError
          ? "HOMIO sign-in is not configured for this deployment."
          : "The identity provider could not start sign-in. Please try again later.",
      },
      { status, headers: { "Cache-Control": "no-store" } },
    );
  }
}