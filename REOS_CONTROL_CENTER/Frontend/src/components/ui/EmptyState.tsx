import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
}: Readonly<{
  title: string;
  description: string;
  action?: ReactNode;
}>) {
  return (
    <section className="empty-state" aria-live="polite">
      <h2>{title}</h2>
      <p>{description}</p>

      {action ? <div className="empty-state__action">{action}</div> : null}
    </section>
  );
}
