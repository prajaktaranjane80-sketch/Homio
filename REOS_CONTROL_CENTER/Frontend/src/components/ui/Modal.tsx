"use client";

import { useId, useRef, type ReactNode } from "react";

import { useDialogFocus } from "@/components/ui/useDialogFocus";

export function Modal({
  open,
  title,
  children,
  onOpenChange,
}: Readonly<{
  open: boolean;
  title: string;
  children: ReactNode;
  onOpenChange: (open: boolean) => void;
}>) {
  const titleId = useId();
  const panelRef = useRef<HTMLElement | null>(null);

  useDialogFocus({ open, onOpenChange, panelRef });

  if (!open) {
    return null;
  }

  return (
    <div
      className="overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target) {
          onOpenChange(false);
        }
      }}
    >
      <section
        ref={panelRef}
        className="overlay__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
      >
        <div className="overlay__header">
          <h2 className="overlay__title" id={titleId}>
            {title}
          </h2>

          <button
            className="overlay__close"
            type="button"
            onClick={() => onOpenChange(false)}
            aria-label="Close dialog"
          >
            ×
          </button>
        </div>

        <div className="overlay__body">{children}</div>
      </section>
    </div>
  );
}
