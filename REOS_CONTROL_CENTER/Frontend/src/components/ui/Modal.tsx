"use client";

import { useEffect, useId, type ReactNode } from "react";

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

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [onOpenChange, open]);

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
        className="overlay__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
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
