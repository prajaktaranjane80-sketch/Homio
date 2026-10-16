"use client";

import {
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
  };

  static getDerivedStateFromError(): State {
    return {
      hasError: true,
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.onError?.(error, info);

    if (process.env.NODE_ENV !== "production") {
      console.error(
        "HOMIO feature boundary caught an error:",
        error,
      );
    }
  }

  private retry = (): void => {
    this.setState({ hasError: false });
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    return (
      <section
        className="page-container page-container--narrow"
        role="alert"
        aria-live="assertive"
      >
        <div
          className="card"
          style={{
            padding: "clamp(1.25rem, 3vw, 2rem)",
          }}
        >
          <p style={{ marginTop: 0, fontWeight: 750 }}>
            This section could not load
          </p>

          <p style={{ color: "var(--homio-text-soft)" }}>
            Your saved information has not been changed by
            this display error.
          </p>

          <button
            className="button button--primary"
            type="button"
            onClick={this.retry}
          >
            Try again
          </button>
        </div>
      </section>
    );
  }
}
