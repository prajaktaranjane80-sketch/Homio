"use client";

import { useState } from "react";
import styles from "./PropertyActionBar.module.css";

export default function PropertyActionBar() {
  const [saved, setSaved] = useState(false);
  const [compared, setCompared] = useState(false);
  const [shareStatus, setShareStatus] = useState("");

  async function shareProperty() {
    if (typeof window === "undefined") {
      return;
    }

    setShareStatus("");

    try {
      const url = window.location.href;

      if (typeof navigator.share === "function") {
        await navigator.share({
          title: "HOMIO Property Preview",
          text: "Explore this HOMIO property experience preview.",
          url,
        });
        return;
      }

      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        setShareStatus("Property link copied.");
        return;
      }

      setShareStatus(
        "Automatic sharing is unavailable. Copy the page URL manually.",
      );
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      setShareStatus(
        "The property link could not be shared automatically.",
      );
    }
  }

  return (
    <div className={styles.bar}>
      <button
        type="button"
        className={`${styles.secondary} ${
          saved ? styles.active : ""
        }`}
        aria-pressed={saved}
        onClick={() => setSaved((value) => !value)}
        title="This state is temporary and is not saved to an account."
      >
        {saved ? "Saved in preview" : "Save"}
      </button>

      <button
        type="button"
        className={`${styles.secondary} ${
          compared ? styles.active : ""
        }`}
        aria-pressed={compared}
        onClick={() => setCompared((value) => !value)}
        title="This state is temporary and is not persisted."
      >
        {compared ? "In preview compare" : "Compare"}
      </button>

      <button
        type="button"
        className={styles.secondary}
        onClick={shareProperty}
      >
        Share
      </button>

      <a
        href="#property-ai"
        className={styles.ai}
        style={{ display: "inline-flex", alignItems: "center", textDecoration: "none" }}
      >
        Ask HOMIO
      </a>

      <a
        href="#property-next-step"
        className={styles.primary}
        style={{ display: "inline-flex", alignItems: "center", textDecoration: "none" }}
      >
        Enquire
      </a>

      <a
        href="#property-next-step"
        className={styles.primary}
        style={{ display: "inline-flex", alignItems: "center", textDecoration: "none" }}
      >
        Schedule Visit
      </a>

      <small
        style={{
          flexBasis: "100%",
          color: "#667085",
          fontSize: 10,
          lineHeight: 1.5,
        }}
      >
        Save and compare change only this page&apos;s temporary state.
        Enquiry and visit links lead to the capability notice below;
        no lead or visit request is submitted from this preview.
      </small>

      <span
        aria-live="polite"
        style={{
          flexBasis: "100%",
          color: "#34414d",
          fontSize: 11,
        }}
      >
        {shareStatus}
      </span>
    </div>
  );
}
