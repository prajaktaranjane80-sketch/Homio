import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  SESSION_COOKIE,
  readSessionCookie,
} from "@/lib/auth/oidc";

export const metadata = {
  title: "My HOMIO",
  robots: { index: false, follow: false },
};

export const dynamic = "force-dynamic";

export default async function MyHomioAccountPage() {
  const cookieStore = await cookies();
  const session = readSessionCookie(cookieStore.get(SESSION_COOKIE)?.value);

  if (!session) {
    redirect("/login?returnTo=%2Fmy");
  }

  return (
    <main className="homio-container" style={{ paddingBlock: "clamp(2rem, 6vw, 5rem)" }}>
      <section
        aria-labelledby="my-homio-heading"
        style={{
          maxWidth: "760px",
          marginInline: "auto",
          border: "1px solid var(--homio-border)",
          borderRadius: "var(--radius-xl)",
          padding: "clamp(1.25rem, 4vw, 2.5rem)",
          background: "var(--homio-surface)",
        }}
      >
        <span style={{ color: "var(--homio-accent)", fontWeight: 800, letterSpacing: "0.12em", fontSize: "var(--text-xs)" }}>
          MY HOMIO Â· PRIVATE ACCOUNT
        </span>
        <h1 id="my-homio-heading" style={{ marginBlock: "var(--space-3)", fontSize: "clamp(2rem, 5vw, 3rem)" }}>
          {session.name ? `Welcome, ${session.name}` : "Your HOMIO account"}
        </h1>
        <p style={{ color: "var(--homio-text-soft)", lineHeight: 1.7 }}>
          You are signed in through your configured identity provider.
        </p>
        {session.email ? <p><strong>Email:</strong> {session.email}</p> : null}
        <p style={{ color: "var(--homio-text-soft)", fontSize: "var(--text-sm)" }}>
          Email verification: {session.emailVerified ? "verified by the identity provider" : "not confirmed by the identity provider"}.
        </p>
        <div style={{ marginTop: "var(--space-6)" }}>
          <h2>Property journey</h2>
          <p style={{ color: "var(--homio-text-soft)", lineHeight: 1.7 }}>
            Your authenticated account is active. Saved properties, synced searches,
            comparisons, visits and conversations will appear here after their authorized
            persistence services are connected; this page does not invent or locally fake that data.
          </p>
        </div>
        <form action="/api/auth/logout" method="post" style={{ marginTop: "var(--space-6)" }}>
          <button type="submit" style={{ minHeight: 44, paddingInline: "1.25rem", borderRadius: "999px", border: "1px solid var(--homio-border)", background: "var(--homio-surface)", fontWeight: 700, cursor: "pointer" }}>
            Sign out of HOMIO
          </button>
        </form>
      </section>
    </main>
  );
}