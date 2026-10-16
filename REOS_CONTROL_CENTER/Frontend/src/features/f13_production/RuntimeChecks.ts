
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
    const webpSupported = supportsWebP();
    const motionApiAvailable =
      typeof window.matchMedia === "function";

    checks.push({
      name: "viewport-width",
      passed:
        Number.isFinite(viewportWidth) &&
        viewportWidth >= 320,
      detail: Number.isFinite(viewportWidth)
        ? "Viewport width: " + viewportWidth + "px."
        : "Viewport width is not finite.",
    });

    checks.push({
      name: "main-landmark",
      passed: hasMain,
      detail: hasMain
        ? "Main landmark found."
        : "No main landmark found.",
    });

    checks.push({
      name: "webp-support",
      passed: webpSupported,
      detail: webpSupported
        ? "WebP image encoding is supported."
        : "WebP image encoding is not supported.",
    });

    checks.push({
      name: "reduced-motion-api",
      passed: motionApiAvailable,
      detail: motionApiAvailable
        ? "Motion preference API is available."
        : "Motion preference API is unavailable.",
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
  if (typeof document === "undefined") return false;

  try {
    const canvas = document.createElement("canvas");

    if (typeof canvas.toDataURL !== "function") {
      return false;
    }

    return canvas
      .toDataURL("image/webp")
      .startsWith("data:image/webp");
  } catch {
    return false;
  }
}
