import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE, getAuthConfig } from "@/lib/auth/oidc";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const config = getAuthConfig();
    const origin = request.headers.get("origin");
    if (!origin || origin !== config.appUrl) {
      return NextResponse.json(
        { error: "invalid_origin" },
        { status: 403, headers: { "Cache-Control": "no-store" } },
      );
    }

    const response = NextResponse.redirect(
      new URL("/login?status=signed-out", config.appUrl),
      303,
    );
    response.headers.set("Cache-Control", "no-store");
    response.cookies.set(SESSION_COOKIE, "", {
      httpOnly: true,
      secure: config.secureCookies,
      sameSite: "lax",
      path: "/",
      maxAge: 0,
    });
    return response;
  } catch {
    return NextResponse.json(
      { error: "authentication_not_configured" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}