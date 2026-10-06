"use client";

import { useState } from "react";
import styles from "./PropertyActionBar.module.css";

export default function PropertyActionBar() {
  const [saved, setSaved] = useState(false);
  const [compared, setCompared] = useState(false);

  async function shareProperty() {
    const url =
      typeof window !== "undefined"
        ? window.location.href
        : "";

    if (!url) {
      return;
    }

    if (navigator.share) {
      await navigator.share({
        title: "HOMIO Property",
        text: "Explore this property on HOMIO.",
        url,
      });
      return;
    }

    await navigator.clipboard?.writeText(url);
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
      >
        {saved ? "Saved" : "Save"}
      </button>

      <button
        type="button"
        className={`${styles.secondary} ${
          compared ? styles.active : ""
        }`}
        aria-pressed={compared}
        onClick={() => setCompared((value) => !value)}
      >
        {compared ? "Compared" : "Compare"}
      </button>

      <button
        type="button"
        className={styles.secondary}
        onClick={shareProperty}
      >
        Share
      </button>

      <button
        type="button"
        className={styles.ai}
      >
        Ask HOMIO
      </button>

      <button
        type="button"
        className={styles.primary}
      >
        Enquire
      </button>

      <button
        type="button"
        className={styles.primary}
      >
        Schedule Visit
      </button>
    </div>
  );
}
