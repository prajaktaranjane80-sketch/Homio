import type { ReactNode } from "react";

interface LoadingBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  isLoading: boolean;
  label?: string;
}

export function LoadingBoundary({
  children,
  fallback,
  isLoading,
  label = "Loading content",
}: LoadingBoundaryProps) {
  if (isLoading) {
    return (
      <div
        aria-busy="true"
        aria-live="polite"
        aria-label={label}
      >
        {fallback ?? (
          <div className="loading-stack">
            <div
              className="skeleton"
              style={{ width: "9rem", height: "0.875rem" }}
            />

            <div
              className="skeleton"
              style={{ width: "68%", height: "2.5rem" }}
            />

            <div
              className="skeleton"
              style={{ width: "45%", height: "1rem" }}
            />

            <div className="loading-grid">
              <div
                className="skeleton"
                style={{ minHeight: "10rem" }}
              />
              <div
                className="skeleton"
                style={{ minHeight: "10rem" }}
              />
              <div
                className="skeleton"
                style={{ minHeight: "10rem" }}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  return <>{children}</>;
}
