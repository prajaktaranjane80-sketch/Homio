"use client";

import { useState } from "react";
import styles from "./SavedCompareExperience.module.css";

type ShareComparisonProps = Readonly<{ ids: readonly string[]; disabled?: boolean }>;

export default function ShareComparison({ ids, disabled = false }: ShareComparisonProps) {
  const [status, setStatus] = useState("");
  async function share() {
    if (typeof window === "undefined" || ids.length === 0) return;
    const url = new URL(window.location.href);
    url.searchParams.set("compare", ids.join(","));
    setStatus("");
    try {
      if (!navigator.clipboard?.writeText) {
        setStatus("Link copying is not supported here. Copy the current page URL manually.");
        return;
      }
      await navigator.clipboard.writeText(url.toString());
      setStatus("Comparison link copied. The receiving page must support these item IDs to reopen the comparison.");
    } catch {
      setStatus("Could not copy automatically. Copy the page URL manually.");
    }
  }
  return <div className={styles.shareControl}><button type="button" className={styles.primaryAction} onClick={share} disabled={disabled || ids.length === 0}>Share comparison <span aria-hidden="true">↗</span></button><p className={styles.liveStatus} aria-live="polite">{status}</p></div>;
}
