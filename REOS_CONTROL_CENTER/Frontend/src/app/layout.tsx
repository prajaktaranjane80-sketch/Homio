import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorBoundary } from "@/features/f13_production/ErrorBoundary";
import ProductionQualityMonitor from "@/features/f13_production/ProductionQualityMonitor";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "HOMIO | Global Property Discovery",
    template: "%s | HOMIO",
  },
  description:
    "Explore property discovery, homes, rentals, projects and commercial spaces through HOMIO. Property facts and availability depend on approved source data.",
  applicationName: "HOMIO",
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f8f7f4",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          <>
            <ProductionQualityMonitor />
            <AppShell>{children}</AppShell>
          </>
        </ErrorBoundary>
      </body>
    </html>
  );
}
