"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";

import styles from "./error.module.css";

type ProjectErrorProps = Readonly<{
  error: Error & {
    digest?: string;
  };
  reset: () => void;
}>;

export default function ProjectError({
  error,
  reset,
}: ProjectErrorProps) {
  useEffect(() => {
    console.error("HOMIO project route error:", error);
  }, [error]);

  return (
    <main className={styles.page}>
      <div className="homio-container">
        <section className={styles.card} role="alert">
          <span className={styles.eyebrow}>HOMIO PROJECT</span>

          <h1>
            Something went wrong while opening this project.
          </h1>

          <p>
            The project experience could not be completed safely.
            Your project information has not been changed.
          </p>

          <div className={styles.actions}>
            <Button variant="primary" onClick={reset}>
              Try again
            </Button>

            <a href="/search" className={styles.secondary}>
              Return to search
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
