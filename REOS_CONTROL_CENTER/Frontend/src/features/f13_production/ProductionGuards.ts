export interface ProductionGuardIssue {
  code: string;
  message: string;
  severity: "error" | "warning";
}

export interface ProductionGuardInput {
  nodeEnvironment?: string;
  publicAppUrl?: string;
  authSecretPresent?: boolean;
  authProviderConfigured?: boolean;
  analyticsEnabled?: boolean;
  analyticsSinkConfigured?: boolean;
}

export function inspectProductionConfiguration(
  input: ProductionGuardInput,
): ProductionGuardIssue[] {
  const issues: ProductionGuardIssue[] = [];

  if (input.nodeEnvironment !== "production") return issues;

  if (!input.publicAppUrl?.trim()) {
    issues.push({
      code: "PUBLIC_APP_URL_MISSING",
      message: "Set the public application URL before production deployment.",
      severity: "error",
    });
  } else {
    try {
      const url = new URL(input.publicAppUrl);

      if (url.protocol !== "https:") {
        issues.push({
          code: "PUBLIC_APP_URL_NOT_HTTPS",
          message: "The production application URL must use HTTPS.",
          severity: "error",
        });
      }

      if (url.username || url.password || url.search || url.hash) {
        issues.push({
          code: "PUBLIC_APP_URL_INVALID",
          message: "The public application URL must not contain credentials, a query or a fragment.",
          severity: "error",
        });
      }
    } catch {
      issues.push({
        code: "PUBLIC_APP_URL_INVALID",
        message: "The public application URL is not a valid absolute URL.",
        severity: "error",
      });
    }
  }

  if (input.authSecretPresent === false) {
    issues.push({
      code: "AUTH_SECRET_MISSING",
      message: "The authentication session secret is missing or too short.",
      severity: "error",
    });
  }

  if (input.authProviderConfigured === false) {
    issues.push({
      code: "AUTH_PROVIDER_CONFIGURATION_MISSING",
      message: "The OIDC issuer or client identifier is not configured.",
      severity: "error",
    });
  }

  if (input.analyticsEnabled && !input.analyticsSinkConfigured) {
    issues.push({
      code: "ANALYTICS_SINK_MISSING",
      message: "Analytics is enabled but no event sink is configured.",
      severity: "warning",
    });
  }

  return issues;
}

export function assertNoProductionConfigurationErrors(
  issues: ProductionGuardIssue[],
): void {
  const errors = issues.filter((issue) => issue.severity === "error");

  if (errors.length > 0) {
    throw new Error(
      "HOMIO production configuration has " +
        errors.length +
        " blocking issue(s): " +
        errors.map((issue) => issue.code).join(", "),
    );
  }
}
