import type { ReactNode } from "react";

import { ContextBar } from "@/components/shell/ContextBar";
import { GlobalActionLayer } from "@/components/shell/GlobalActionLayer";
import { Header } from "@/components/shell/Header";

export function AppShell({
  children,
  header,
}: Readonly<{
  children: ReactNode;
  header?: ReactNode;
}>) {
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      {header ?? <Header />}

      <ContextBar
        primary="HOMIO · India-first real-estate experience"
        secondary="REOS remains the canonical business authority"
      />

      {children}

      <GlobalActionLayer />
    </>
  );
}
