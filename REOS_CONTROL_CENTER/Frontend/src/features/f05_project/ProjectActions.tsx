"use client";

import { useState } from "react";

import {
  compareFromProject,
  savedFromProject,
} from "@/features/f06_save_compare/saveCompareAdapters";
import {
  toggleComparedItem,
  toggleSavedRecord,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";
import type { ProjectRecord } from "./project.types";
import styles from "./ProjectActions.module.css";

type ProjectActionsProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectActions({ project }: ProjectActionsProps) {
  const session = useSaveCompareSession();
  const [shareMessage, setShareMessage] = useState("");

  const saved = session.savedRecords.some(
    (item) => item.id === project.id && item.kind === "project",
  );
  const compared = session.comparedItems.some(
    (item) => item.id === project.id && item.kind === "project",
  );

  async function shareProject() {
    setShareMessage("");

    try {
      const url = window.location.href;
      if (typeof navigator.share === "function") {
        await navigator.share({
          title: project.name,
          text: `Explore ${project.name} on HOMIO.`,
          url,
        });
        setShareMessage("Share completed.");
        return;
      }
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        setShareMessage("Project link copied.");
        return;
      }
      setShareMessage("Copy the page address from your browser.");
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") return;
      setShareMessage("Sharing was unavailable. Copy the page address instead.");
    }
  }

  return (
    <section className={styles.card} aria-label="Project actions">
      <div className={styles.grid}>
        <button
          type="button"
          className={`${styles.secondary}${saved ? ` ${styles.active}` : ""}`}
          aria-pressed={saved}
          onClick={() => toggleSavedRecord(savedFromProject(project))}
        >
          {saved ? "Saved" : "Save"}
        </button>
        <button
          type="button"
          className={`${styles.secondary}${compared ? ` ${styles.active}` : ""}`}
          aria-pressed={compared}
          onClick={() => toggleComparedItem(compareFromProject(project))}
          title="Compare up to four items in this browser session."
        >
          {compared ? "Compared" : "Compare"}
        </button>
        <button type="button" className={styles.secondary} onClick={shareProject}>
          Share
        </button>
        <a href="#inventory" className={styles.primary}>
          Explore inventory <span aria-hidden="true">→</span>
        </a>
      </div>

      {shareMessage ? (
        <p className={styles.shareStatus} role="status" aria-live="polite">
          {shareMessage}
        </p>
      ) : null}

      <p className={styles.note}>
        Save and compare are temporary experience controls until approved REOS
        persistence capabilities are connected. These items are not synced to
        an account and are cleared by a full page reload.
      </p>
    </section>
  );
}
