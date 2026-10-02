import type { ReactNode } from "react";

export function PageContainer({
  children,
  narrow = false,
}: Readonly<{
  children: ReactNode;
  narrow?: boolean;
}>) {
  return (
    <div className={`page-container${narrow ? " page-container--narrow" : ""}`}>
      {children}
    </div>
  );
}
