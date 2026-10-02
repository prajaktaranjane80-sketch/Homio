"use client";

import { useEffect } from "react";

import { ErrorState } from "@/components/ui/ErrorState";

export default function GlobalErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("HOMIO frontend boundary error:", error);
  }, [error]);

  return (
    <main className="page-shell">
      <div className="page-container page-container--narrow">
        <ErrorState
          title="Something went wrong"
          description="The experience could not complete safely. No business state has been changed by this error boundary."
          actionLabel="Retry"
          onAction={reset}
        />
      </div>
    </main>
  );
}
