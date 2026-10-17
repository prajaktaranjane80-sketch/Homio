"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { auditAccessibility } from "./AccessibilityAudit";
import { auditResponsiveDimensions } from "./ResponsiveAudit";
import { runRuntimeChecks } from "./RuntimeChecks";

const DIAGNOSTICS_ENABLED =
  process.env.NODE_ENV !== "production" ||
  process.env.NEXT_PUBLIC_HOMIO_F13_DIAGNOSTICS === "true";

export default function ProductionQualityMonitor() {
  const pathname = usePathname();

  useEffect(() => {
    if (!DIAGNOSTICS_ENABLED) return;

    let frame = 0;

    const inspect = () => {
      frame = 0;

      const failedRuntimeChecks = runRuntimeChecks().filter(
        (check) => !check.passed && check.name !== "browser-availability",
      );

      if (failedRuntimeChecks.length > 0) {
        console.warn(
          "[HOMIO F13] Runtime checks need attention.",
          failedRuntimeChecks.map(({ name, detail }) => ({ name, detail })),
        );
      }

      const accessibility = auditAccessibility(document);
      if (accessibility.findings.length > 0) {
        console.warn("[HOMIO F13] Accessibility findings.", {
          errorCount: accessibility.errorCount,
          warningCount: accessibility.warningCount,
          findings: accessibility.findings,
        });
      }

      const responsive = auditResponsiveDimensions(
        window.innerWidth,
        document.documentElement.scrollWidth,
      );

      if (responsive.hasHorizontalOverflow) {
        console.warn("[HOMIO F13] Horizontal overflow detected.", {
          viewport: responsive.viewport,
          viewportWidth: responsive.viewportWidth,
          documentWidth: responsive.documentWidth,
          horizontalOverflow: responsive.horizontalOverflow,
        });
      }
    };

    const scheduleInspection = () => {
      if (frame) window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(inspect);
    };

    scheduleInspection();
    window.addEventListener("resize", scheduleInspection, { passive: true });

    return () => {
      if (frame) window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", scheduleInspection);
    };
  }, [pathname]);

  return null;
}
