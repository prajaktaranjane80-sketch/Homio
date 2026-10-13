import Link from "next/link";

import { isAuthConfigured } from "@/lib/auth/oidc";

import styles from "./AuthPanel.module.css";

type AuthPanelProps = Readonly<{
  mode: "login" | "signup";
  error?: string;
  status?: string;
}>;

const ERROR_MESSAGES: Record<string, string> = {
  "authentication-failed":
    "Sign-in was not completed. Please try again. No account changes were made by HOMIO.",
  "provider-unavailable":
    "HOMIO could not reach the configured identity provider. Please try again later.",
};

export default function AuthPanel({ mode, error, status }: AuthPanelProps) {
  const isSignup = mode === "signup";
  const configured = isAuthConfigured();

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="auth-heading">
        <span className={styles.eyebrow}>MY HOMIO Â· SECURE ACCOUNT</span>
        <h1 id="auth-heading">
          {isSignup ? "Create your HOMIO account" : "Welcome back to HOMIO"}
        </h1>
        <p className={styles.intro}>
          {isSignup
            ? "Create your account through HOMIO's configured identity provider. HOMIO never asks this page to collect your provider password."
            : "Sign in securely to open your personal HOMIO account and property journey."}
        </p>

        {error && ERROR_MESSAGES[error] ? (
          <p className={styles.status} role="status">{ERROR_MESSAGES[error]}</p>
        ) : null}
        {status === "signed-out" ? (
          <p className={styles.status} role="status">You have signed out of this HOMIO session.</p>
        ) : null}

        {configured ? (
          <div className={styles.actions}>
            <form action="/api/auth/login" method="get">
              <input type="hidden" name="intent" value={mode} />
              <input type="hidden" name="returnTo" value="/my" />
              <button className={styles.primary} type="submit">
                {isSignup ? "Continue to create account" : "Continue with secure sign-in"}
              </button>
            </form>
          </div>
        ) : (
          <p className={styles.status} role="status">
            Account sign-in is not enabled in this deployment yet. The operator must configure
            HOMIO_OIDC_ISSUER, HOMIO_OIDC_CLIENT_ID, HOMIO_APP_URL and a private
            HOMIO_SESSION_SECRET in the deployment environment. No demo login is available.
          </p>
        )}

        <div className={styles.links}>
          {isSignup ? (
            <Link href="/login">Already have an account? Sign in</Link>
          ) : (
            <Link href="/signup">Create an account</Link>
          )}
          <Link href="/">Back to HOMIO</Link>
        </div>
      </section>
    </main>
  );
}