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
        primary="HOMIO · Property discovery, made personal"
        secondary="Find your next place, with HOMIO by your side."
      />

      <div id="main-content" tabIndex={-1}>
        {children}
      </div>

      <GlobalActionLayer />
    </>
  );
}
