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
          title: "HOMIO Property Experience Preview",
          text:
            "Explore this HOMIO property experience preview. " +
            "The listing is not verified inventory.",
          url,
        });

        setShareStatus("The share action was completed.");
        return;
      }

      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        setShareStatus("Property preview link copied.");
        return;
      }

      setShareStatus(
        "Automatic sharing is unavailable. Copy the page URL manually.",
      );
    } catch (error) {
      if (
        typeof DOMException !== "undefined" &&
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      setShareStatus(
        "The preview link could not be shared automatically.",
      );
    }
  }

  return (
    <div className={styles.bar} aria-label="Property actions">
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
        Share preview
      </button>

      <a href="#property-ai" className={styles.ai}>
        Ask HOMIO
      </a>

      <a
        href="#property-next-step-enquiry"
        className={styles.primary}
      >
        Enquire
      </a>

      <a
        href="#property-next-step-visit"
        className={styles.primary}
      >
        Schedule visit
      </a>

      <small className={styles.disclosure}>
        Save and compare change only this page&apos;s temporary state.
        Enquiry and visit links lead to capability notices. No lead,
        enquiry or visit request is submitted by this preview.
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
