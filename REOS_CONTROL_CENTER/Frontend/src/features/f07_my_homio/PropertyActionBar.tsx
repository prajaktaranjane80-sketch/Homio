"use client";

import { useEffect, useState } from "react";

import {
  compareFromProperty,
  savedFromProperty,
} from "@/features/f06_save_compare/saveCompareAdapters";

import {
  toggleComparedItem,
  toggleSavedRecord,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";

import { recordRecentView } from "@/features/f07_my_homio/myHomioActivityStore";

import type { PropertyRecord } from "./property.types";

import styles from "./PropertyActionBar.module.css";

type PropertyActionBarProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyActionBar({
  property,
}: PropertyActionBarProps) {
  const session = useSaveCompareSession();

  const [shareStatus, setShareStatus] = useState("");

  const saved = session.savedRecords.some(
    (item) =>
      item.id === property.id &&
      item.kind === "property",
  );

  const compared = session.comparedItems.some(
    (item) =>
      item.id === property.id &&
      item.kind === "property",
  );

  useEffect(() => {
    recordRecentView({
      id: property.id,
      kind: "property",
      title: property.title,
      href: `/property/${encodeURIComponent(property.id)}`,
      subtitle: property.location,
    });
  }, [property.id, property.title, property.location]);

  async function shareProperty() {
    setShareStatus("");

    try {
      const url = window.location.href;

      if (typeof navigator.share === "function") {
        await navigator.share({
          title: property.title,
          text: "Explore this property preview on HOMIO.",
          url,
        });

        setShareStatus("Share completed.");
        return;
      }

      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        setShareStatus("Property link copied.");
        return;
      }

      setShareStatus("Copy this page URL from your browser.");
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }

      setShareStatus("Sharing was unavailable. Copy the page URL instead.");
    }
  }

  return (
    <div className={styles.bar} aria-label="Property actions">
      <button
        type="button"
        className={`${styles.secondary} ${saved ? styles.active : ""}`}
        aria-pressed={saved}
        onClick={() => toggleSavedRecord(savedFromProperty(property))}
      >
        {saved ? "Saved" : "Save"}
      </button>

      <button
        type="button"
        className={`${styles.secondary} ${compared ? styles.active : ""}`}
        aria-pressed={compared}
        onClick={() => toggleComparedItem(compareFromProperty(property))}
        title="Compare up to four items in this browser session."
      >
        {compared ? "Compared" : "Compare"}
      </button>

      <button
        type="button"
        className={styles.secondary}
        onClick={shareProperty}
      >
        Share preview
      </button>

      <a href="#property-ai" className={styles.ai}>
        Ask HOMIO
      </a>

      <a href="#property-next-step-enquiry" className={styles.primary}>
        Enquire
      </a>

      <a href="#property-next-step-visit" className={styles.primary}>
        Schedule visit
      </a>

      <small className={styles.disclosure}>
        Saved and compared items remain in temporary in-memory session state.
        They are not synced to an account and are cleared by a full page reload.
        Enquiry and visit links do not submit a request.
      </small>

      <span
        className={styles.shareStatus}
        role="status"
        aria-live="polite"
      >
        {shareStatus}
      </span>
    </div>
  );
}
