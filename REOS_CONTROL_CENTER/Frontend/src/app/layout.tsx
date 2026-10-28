import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorBoundary } from "@/features/f13_production/ErrorBoundary";
import ProductionQualityMonitor from "@/features/f13_production/ProductionQualityMonitor";

import "./globals.css";

const siteTitle = "HOMIO | Pune Homes, Flats & Property Discovery";

const siteDescription =
  "Explore homes, flats, rentals and residential projects across Pune. Compare localities, shortlist property options and enquire through HOMIO. Listing details and availability depend on information supplied by the responsible source.";

export const metadata: Metadata = {
  title: {
    default: siteTitle,
    template: "%s | HOMIO",
  },

  description: siteDescription,

  applicationName: "HOMIO",
  category: "real estate",

  // Fail closed: a route must explicitly opt in before it is indexed.
  // Preview inventory, account pages and unfinished experiences stay hidden.
  robots: {
    index: false,
    follow: false,
  },

  openGraph: {
    type: "website",
    locale: "en_IN",
    siteName: "HOMIO",
    title: siteTitle,
    description: siteDescription,
  },

  twitter: {
    card: "summary",
    title: siteTitle,
    description: siteDescription,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f8f1e7",
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
