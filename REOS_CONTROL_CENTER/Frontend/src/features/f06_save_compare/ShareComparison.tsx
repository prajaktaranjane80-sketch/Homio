"use client";

import { useState } from "react";

import type { CompareItem } from "./compare.types";

import styles from "./SavedCompareExperience.module.css";

type ShareComparisonProps = Readonly<{
  items: readonly CompareItem[];
  disabled?: boolean;
}>;

export default function ShareComparison({
  items,
  disabled = false,
}: ShareComparisonProps) {
  const [status, setStatus] = useState("");

  async function share() {
    if (items.length === 0) {
      setStatus("Add an item before sharing comparison context.");
      return;
    }

    const url = new URL(window.location.href);

    const identities = items.map(
      (item) => `${item.kind}:${item.id}`,
    );

    url.searchParams.set(
      "compare",
      identities.join(","),
    );

    setStatus("");

    try {
      if (!navigator.clipboard?.writeText) {
        setStatus(
          "Automatic copying is unavailable. Copy the page URL manually.",
        );
        return;
      }

      await navigator.clipboard.writeText(url.toString());

      setStatus(
        "Context link copied. Comparison records remain browser-session data and will not automatically load in another browser.",
      );
    } catch {
      setStatus(
        "Copy failed. Copy the page URL manually.",
      );
    }
  }

  return (
    <div className={styles.shareControl}>
      <button
        type="button"
        className={styles.primaryAction}
        onClick={share}
        disabled={disabled || items.length === 0}
      >
        Copy comparison context
        <span aria-hidden="true"> ↗</span>
      </button>

      <p
        className={styles.liveStatus}
        role="status"
        aria-live="polite"
      >
        {status}
      </p>
    </div>
  );
}
