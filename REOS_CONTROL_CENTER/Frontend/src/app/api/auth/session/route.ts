import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SESSION_COOKIE, readSessionCookie } from "@/lib/auth/oidc";

export const runtime = "nodejs";

export async function GET() {
  const cookieStore = await cookies();
  const session = readSessionCookie(cookieStore.get(SESSION_COOKIE)?.value);
  const response = NextResponse.json(
    session
      ? {
          authenticated: true,
          user: {
            name: session.name ?? null,
            email: session.email ?? null,
            emailVerified: session.emailVerified,
          },
          expiresAt: session.expiresAt,
        }
      : { authenticated: false, user: null },
  );
  response.headers.set("Cache-Control", "no-store, private");
  response.headers.set("Vary", "Cookie");
  return response;
}