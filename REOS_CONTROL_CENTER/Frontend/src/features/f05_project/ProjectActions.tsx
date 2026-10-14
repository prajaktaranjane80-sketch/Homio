"use client";

import { useEffect, useState } from "react";

import {
  compareFromProject,
  savedFromProject,
} from "@/features/f06_save_compare/saveCompareAdapters";

import {
  toggleComparedItem,
  toggleSavedRecord,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";

import { recordRecentView } from "@/features/f07_my_homio/myHomioActivityStore";

import type { ProjectRecord } from "./project.types";

import styles from "./ProjectActions.module.css";

type ProjectActionsProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectActions({
  project,
}: ProjectActionsProps) {
  const session = useSaveCompareSession();

  const [shareMessage, setShareMessage] = useState("");

  const saved = session.savedRecords.some(
    (item) =>
      item.id === project.id &&
      item.kind === "project",
  );

  const compared = session.comparedItems.some(
    (item) =>
      item.id === project.id &&
      item.kind === "project",
  );

  useEffect(() => {
    recordRecentView({
      id: project.id,
      kind: "project",
      title: project.name,
      href: `/project/${encodeURIComponent(project.id)}`,
      subtitle: project.location,
    });
  }, [project.id, project.name, project.location]);

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
      if (
        error instanceof Error &&
        error.name === "AbortError"
      ) {
        return;
      }

      setShareMessage(
        "Sharing was unavailable. Copy the page address instead.",
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
          className={`${styles.secondary}${saved ? ` ${styles.active}` : ""}`}
          aria-pressed={saved}
          onClick={() =>
            toggleSavedRecord(savedFromProject(project))
          }
        >
          {saved ? "Saved" : "Save"}
        </button>

        <button
          type="button"
          className={`${styles.secondary}${compared ? ` ${styles.active}` : ""}`}
          aria-pressed={compared}
          onClick={() =>
            toggleComparedItem(compareFromProject(project))
          }
          title="Compare up to four items in this browser session."
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
          <span aria-hidden="true"> →</span>
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
        These are temporary experience controls, not account-synced
        actions. Save and Compare state remains in browser memory
        and clears after a full page reload. Share uses the
        current page URL; it does not submit an enquiry or
        confirm project availability.
      </p>
    </section>
  );
}
