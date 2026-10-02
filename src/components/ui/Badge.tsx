import type { ReactNode } from "react";

type BadgeTone = "neutral" | "success" | "warning" | "error" | "info";

export function Badge({
  children,
  tone = "neutral",
}: Readonly<{
  children: ReactNode;
  tone?: BadgeTone;
}>) {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}
