import type { ReactNode } from "react";

import { ContextBar } from "@/components/shell/ContextBar";
import { GlobalActionLayer } from "@/components/shell/GlobalActionLayer";
import { Header } from "@/components/shell/Header";

export function AppShell({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <Header />

      <ContextBar
        primary="HOMIO ? Global real-estate experience"
        secondary="REOS remains the canonical business authority"
      />

      {children}

      <GlobalActionLayer />
    </>
  );
}