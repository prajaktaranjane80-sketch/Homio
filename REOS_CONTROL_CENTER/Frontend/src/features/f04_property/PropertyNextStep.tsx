"use client";

import { useState } from "react";
import styles from "./PropertyNextStep.module.css";

export default function PropertyNextStep() {
  const [mode, setMode] = useState<"enquiry" | "visit">("enquiry");

  return (
    <section className={styles.section}>
      <div className={styles.content}>
        <span className={styles.eyebrow}>NEXT STEP</span>

        <h2>Ready to take the conversation forward?</h2>

        <p>
          Start with an enquiry or request a visit. The actual lead,
          qualification and visit workflow remain authoritative in REOS.
        </p>

        <div className={styles.tabs}>
          <button
            type="button"
            className={mode === "enquiry" ? styles.active : ""}
            onClick={() => setMode("enquiry")}
          >
            Enquire
          </button>

          <button
            type="button"
            className={mode === "visit" ? styles.active : ""}
            onClick={() => setMode("visit")}
          >
            Schedule visit
          </button>
        </div>

        <button type="button" className={styles.primary}>
          {mode === "enquiry"
            ? "Start HOMIO enquiry"
            : "Request a HOMIO visit"}
        </button>
      </div>
    </section>
  );
}
