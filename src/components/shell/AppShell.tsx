import type { ReactNode } from "react";

import { Header } from "@/components/shell/Header";
import { ContextBar } from "@/components/shell/ContextBar";
import { GlobalActionLayer } from "@/components/shell/GlobalActionLayer";

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
        primary="HOMIO Experience Foundation"
        secondary="REOS remains the canonical business authority"
      />

      {children}

      <GlobalActionLayer />
    </>
  );
}
