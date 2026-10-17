"use client";

import {
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";

import { ErrorState } from "@/components/ui/ErrorState";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    try {
      this.props.onError?.(error, info);
    } catch {
      // Error reporting must not cause a second render failure.
    }

    if (process.env.NODE_ENV !== "production") {
      console.error("HOMIO feature boundary caught a rendering error.");
    }
  }

  private retry = (): void => {
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children;
    if (this.props.fallback) return this.props.fallback;

    return (
      <main className="page-shell">
        <div className="page-container page-container--narrow">
          <ErrorState
            title="This HOMIO view could not load"
            description="Reload the page to try again. This display error does not create or change a property, enquiry, visit or transaction."
            actionLabel="Reload page"
            onAction={this.retry}
          />
        </div>
      </main>
    );
  }
}
