import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import {
  AUTH_COOKIE_PATH,
  AUTH_TRANSIENT_COOKIE_NAMES,
  SESSION_COOKIE,
  SESSION_TTL_SECONDS,
  constantTimeEqual,
  createSessionCookie,
  exchangeAuthorizationCode,
  getAuthConfig,
  safeReturnTo,
} from "@/lib/auth/oidc";

export const runtime = "nodejs";

function clearTransientCookies(response: NextResponse, secure: boolean) {
  for (const name of AUTH_TRANSIENT_COOKIE_NAMES) {
    response.cookies.set(name, "", {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: AUTH_COOKIE_PATH,
      maxAge: 0,
    });
  }
}

export async function GET(request: NextRequest) {
  let config: ReturnType<typeof getAuthConfig> | undefined;
  let intent: "login" | "signup" = "login";

  try {
    config = getAuthConfig();
    const cookieStore = await cookies();
    intent = cookieStore.get("homio_auth_intent")?.value === "signup"
      ? "signup"
      : "login";

    const returnedState = request.nextUrl.searchParams.get("state") ?? "";
    const storedState = cookieStore.get("homio_auth_state")?.value ?? "";
    if (!returnedState || !storedState || !constantTimeEqual(returnedState, storedState)) {
      throw new Error("Invalid authentication response.");
    }

    if (request.nextUrl.searchParams.has("error")) {
      throw new Error("Authentication was not completed.");
    }

    const code = request.nextUrl.searchParams.get("code") ?? "";
    const nonce = cookieStore.get("homio_auth_nonce")?.value ?? "";
    const verifier = cookieStore.get("homio_auth_verifier")?.value ?? "";
    const returnTo = safeReturnTo(cookieStore.get("homio_auth_return_to")?.value);

    if (!code || !nonce || !verifier) {
      throw new Error("Authentication response is incomplete.");
    }

    const session = await exchangeAuthorizationCode(code, verifier, nonce);
    const sessionCookie = createSessionCookie(session, config);
    const response = NextResponse.redirect(new URL(returnTo, config.appUrl));
    response.headers.set("Cache-Control", "no-store");
    response.headers.set("Referrer-Policy", "no-referrer");
    response.cookies.set(SESSION_COOKIE, sessionCookie, {
      httpOnly: true,
      secure: config.secureCookies,
      sameSite: "lax",
      path: "/",
      maxAge: SESSION_TTL_SECONDS,
    });
    clearTransientCookies(response, config.secureCookies);
    return response;
  } catch {
    if (!config) {
      return NextResponse.json(
        { error: "authentication_unavailable", message: "Sign-in is not available." },
        { status: 503, headers: { "Cache-Control": "no-store" } },
      );
    }

    const destination = intent === "signup" ? "/signup" : "/login";
    const response = NextResponse.redirect(
      new URL(`${destination}?error=authentication-failed`, config.appUrl),
    );
    response.headers.set("Cache-Control", "no-store");
    clearTransientCookies(response, config.secureCookies);
    return response;
  }
}