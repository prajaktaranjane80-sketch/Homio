"use client";

import { useEffect } from "react";

type ToastTone = "info" | "success" | "warning" | "error";

export function Toast({
  open,
  title,
  description,
  tone = "info",
  autoDismissMs = 0,
  onOpenChange,
}: Readonly<{
  open: boolean;
  title: string;
  description?: string;
  tone?: ToastTone;
  autoDismissMs?: number;
  onOpenChange?: (open: boolean) => void;
}>) {
  useEffect(() => {
    if (!open || autoDismissMs <= 0) {
      return;
    }

    const timer = window.setTimeout(() => {
      onOpenChange?.(false);
    }, autoDismissMs);

    return () => window.clearTimeout(timer);
  }, [autoDismissMs, onOpenChange, open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className={`toast toast--${tone}`}
      role={tone === "error" ? "alert" : "status"}
      aria-live={tone === "error" ? "assertive" : "polite"}
    >
      <p className="toast__title">{title}</p>
      {description ? (
        <p className="toast__description">{description}</p>
      ) : null}
    </div>
  );
}
