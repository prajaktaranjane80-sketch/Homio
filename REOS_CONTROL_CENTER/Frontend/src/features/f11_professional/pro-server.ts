
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  SESSION_COOKIE,
  readSessionCookie,
} from "@/lib/auth/oidc";

import type { ProIdentity } from "./pro.types";

/**
 * Requires a valid signed-in HOMIO session for the preview routes.
 *
 * IMPORTANT:
 * A valid HOMIO session does not prove that the user holds a
 * professional role. The current F11 workspace displays no business
 * records until server-side role and record authorization are connected.
 */
export async function requireSignedInProPreview(
  returnTo: string,
): Promise<ProIdentity> {
  const cookieStore = await cookies();

  const session = readSessionCookie(
    cookieStore.get(SESSION_COOKIE)?.value,
  );

  if (!session) {
    redirect(`/login?returnTo=${encodeURIComponent(returnTo)}`);
  }

  return {
    displayName:
      session.name?.trim() ||
      session.email?.trim() ||
      "HOMIO member",
    email: session.email,
    emailVerified: session.emailVerified,
  };
}
