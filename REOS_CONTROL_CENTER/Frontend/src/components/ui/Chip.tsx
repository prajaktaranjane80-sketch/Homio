import type { ReactNode } from "react";

export function Chip({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return <span className="chip">{children}</span>;
}
