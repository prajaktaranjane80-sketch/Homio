"use client";

import { useState } from "react";

import type { ProjectRecord } from "./project.types";

import styles from "./ProjectActions.module.css";

type ProjectActionsProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectActions({
  project,
}: ProjectActionsProps) {
  const [saved, setSaved] = useState(false);
  const [compared, setCompared] = useState(false);
  const [shareMessage, setShareMessage] = useState("");

  async function shareProject() {
    const url = window.location.href;

    try {
      if (typeof navigator.share === "function") {
        await navigator.share({
          title: project.name,
          text: `Explore ${project.name} on HOMIO.`,
          url,
        });

        setShareMessage("Project share completed.");
        return;
      }

      if (
        typeof navigator.clipboard?.writeText === "function"
      ) {
        await navigator.clipboard.writeText(url);
        setShareMessage("Project link copied to clipboard.");
        return;
      }

      setShareMessage(
        "Sharing is unavailable here. Copy the page address from your browser.",
      );
    } catch (error) {
      if (
        error instanceof Error &&
        error.name === "AbortError"
      ) {
        return;
      }

      setShareMessage(
        "The link could not be copied. Copy the page address from your browser.",
      );
    }
  }

  return (
    <section
      className={styles.card}
      aria-label="Project actions"
    >
      <div className={styles.grid}>
        <button
          type="button"
          className={
            styles.secondary +
            (saved ? ` ${styles.active}` : "")
          }
          aria-pressed={saved}
          onClick={() => setSaved((value) => !value)}
        >
          {saved ? "Saved" : "Save"}
        </button>

        <button
          type="button"
          className={
            styles.secondary +
            (compared ? ` ${styles.active}` : "")
          }
          aria-pressed={compared}
          onClick={() => setCompared((value) => !value)}
        >
          {compared ? "Compared" : "Compare"}
        </button>

        <button
          type="button"
          className={styles.secondary}
          onClick={shareProject}
        >
          Share
        </button>

        <a
          href="#inventory"
          className={styles.primary}
        >
          Explore inventory
          <span aria-hidden="true">→</span>
        </a>
      </div>

      {shareMessage ? (
        <p
          className={styles.shareStatus}
          role="status"
          aria-live="polite"
        >
          {shareMessage}
        </p>
      ) : null}

      <p className={styles.note}>
        Save and compare are temporary experience controls until
        approved REOS persistence capabilities are connected.
      </p>
    </section>
  );
}
