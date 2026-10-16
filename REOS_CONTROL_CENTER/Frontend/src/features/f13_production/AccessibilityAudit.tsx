export type AccessibilitySeverity = "error" | "warning";

export interface AccessibilityFinding {
  rule: string;
  severity: AccessibilitySeverity;
  message: string;
  count: number;
}

export interface AccessibilityAuditSummary {
  findings: AccessibilityFinding[];
  errorCount: number;
  warningCount: number;
}

export function auditAccessibility(
  root?: ParentNode,
): AccessibilityAuditSummary {
  const findings: AccessibilityFinding[] = [];

  const target =
    root ??
    (typeof document !== "undefined" ? document : undefined);

  if (!target) {
    return {
      findings: [
        {
          rule: "browser-dom",
          severity: "warning",
          message: "Accessibility audit requires a browser DOM.",
          count: 1,
        },
      ],
      errorCount: 0,
      warningCount: 1,
    };
  }

  const unnamedButtons = Array.from(
    target.querySelectorAll("button"),
  ).filter((button) => {
    const label = button.getAttribute("aria-label")?.trim();
    const labelledBy = button.getAttribute("aria-labelledby")?.trim();

    return (
      !label &&
      !labelledBy &&
      !button.textContent?.trim()
    );
  }).length;

  if (unnamedButtons > 0) {
    findings.push({
      rule: "button-name",
      severity: "error",
      message: "Some buttons have no accessible name.",
      count: unnamedButtons,
    });
  }

  const unlabeledInputs = Array.from(
    target.querySelectorAll(
      "input:not([type='hidden']), select, textarea",
    ),
  ).filter((input) => {
    if (
      input.getAttribute("aria-label")?.trim() ||
      input.getAttribute("aria-labelledby")?.trim()
    ) {
      return false;
    }

    const id = input.getAttribute("id");

    if (
      id &&
      Array.from(target.querySelectorAll("label")).some(
        (label) => label.htmlFor === id,
      )
    ) {
      return false;
    }

    return !input.closest("label");
  }).length;

  if (unlabeledInputs > 0) {
    findings.push({
      rule: "form-label",
      severity: "error",
      message: "Some form controls have no associated label.",
      count: unlabeledInputs,
    });
  }

  const imagesWithoutAlt = target.querySelectorAll(
    "img:not([alt])",
  ).length;

  if (imagesWithoutAlt > 0) {
    findings.push({
      rule: "image-alt",
      severity: "error",
      message:
        'Some images have no alt attribute. Use alt="" for decorative images.',
      count: imagesWithoutAlt,
    });
  }

  if (target.querySelectorAll("main").length === 0) {
    findings.push({
      rule: "landmark-main",
      severity: "warning",
      message: "No main landmark was found.",
      count: 1,
    });
  }

  return {
    findings,
    errorCount: findings.filter(
      (finding) => finding.severity === "error",
    ).length,
    warningCount: findings.filter(
      (finding) => finding.severity === "warning",
    ).length,
  };
}
