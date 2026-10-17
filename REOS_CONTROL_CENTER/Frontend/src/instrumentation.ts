import { inspectProductionConfiguration } from "./features/f13_production/ProductionGuards";

export async function register(): Promise<void> {
  if (
    process.env.NODE_ENV !== "production" ||
    process.env.NEXT_RUNTIME === "edge"
  ) {
    return;
  }

  const sessionSecret = process.env.HOMIO_SESSION_SECRET;
  const authSecretPresent =
    typeof sessionSecret === "string" &&
    Buffer.byteLength(sessionSecret, "utf8") >= 32;

  const authProviderConfigured = Boolean(
    process.env.HOMIO_OIDC_ISSUER?.trim() &&
      process.env.HOMIO_OIDC_CLIENT_ID?.trim(),
  );

  const issues = inspectProductionConfiguration({
    nodeEnvironment: process.env.NODE_ENV,
    publicAppUrl: process.env.HOMIO_APP_URL,
    authSecretPresent,
    authProviderConfigured,
    analyticsEnabled: process.env.HOMIO_ANALYTICS_ENABLED === "true",
    // No analytics provider is silently assumed to be configured.
    analyticsSinkConfigured: false,
  });

  for (const issue of issues) {
    const message = "[HOMIO F13 " + issue.code + "] " + issue.message;
    if (issue.severity === "error") {
      console.error(message);
    } else {
      console.warn(message);
    }
  }
}
