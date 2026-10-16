export interface RuntimeCheckResult {
  name: string;
  passed: boolean;
  detail: string;
}

export function runRuntimeChecks(): RuntimeCheckResult[] {
  const checks: RuntimeCheckResult[] = [];

  const isBrowser =
    typeof window !== "undefined" &&
    typeof document !== "undefined";

  checks.push({
    name: "browser-availability",
    passed: isBrowser,
    detail: isBrowser
      ? "Browser APIs are available."
      : "Server rendering environment detected.",
  });

  if (isBrowser) {
    const viewportWidth = window.innerWidth;
    const hasMain = document.querySelector("main") !== null;

    checks.push({
      name: "viewport-width",
      passed:
        Number.isFinite(viewportWidth) &&
        viewportWidth >= 320,
      detail: Number.isFinite(viewportWidth)
        ? `Viewport width: ${viewportWidth}px.`
        : "Viewport width is not finite.",
    });

    checks.push({
      name: "main-landmark",
      passed: hasMain,
      detail: hasMain
        ? "Main landmark found."
        : "No main landmark found.",
    });
  }

  return checks;
}

export function hasReducedMotionPreference(): boolean {
  if (
    typeof window === "undefined" ||
    typeof window.matchMedia !== "function"
  ) {
    return false;
  }

  return window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
}

export function supportsWebP(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof document !== "undefined"
  );
}
