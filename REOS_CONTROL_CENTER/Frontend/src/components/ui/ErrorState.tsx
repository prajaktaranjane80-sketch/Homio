import { Button } from "@/components/ui/Button";

import type { ReactNode } from "react";

export function ErrorState({
  title,
  description,
  actionLabel,
  onAction,
  action,
}: Readonly<{
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  action?: ReactNode;
}>) {
  return (
    <section className="error-state" role="alert">
      <h2>{title}</h2>
      <p>{description}</p>

      {action ? (
        <div className="error-state__action">{action}</div>
      ) : onAction && actionLabel ? (
        <div className="error-state__action">
          <Button variant="secondary" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      ) : null}
    </section>
  );
}
