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

  async function shareProject() {
    const url =
      typeof window !== "undefined"
        ? window.location.href
        : "";

    if (!url) {
      return;
    }

    try {
      if (navigator.share) {
        await navigator.share({
          title: project.name,
          text: `Explore ${project.name} on HOMIO.`,
          url,
        });
        return;
      }

      await navigator.clipboard?.writeText(url);
    } catch {
      // Share cancellation or clipboard restrictions are non-fatal.
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
          className={`${styles.secondary} ${
            saved ? styles.active : ""
          }`}
          aria-pressed={saved}
          onClick={() =>
            setSaved((value) => !value)
          }
        >
          {saved ? "Saved" : "Save"}
        </button>

        <button
          type="button"
          className={`${styles.secondary} ${
            compared ? styles.active : ""
          }`}
          aria-pressed={compared}
          onClick={() =>
            setCompared((value) => !value)
          }
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
        </a>
      </div>

      <div className={styles.note}>
        Save, compare and share are temporary experience controls until
        approved REOS persistence capabilities are connected.
      </div>
    </section>
  );
}
