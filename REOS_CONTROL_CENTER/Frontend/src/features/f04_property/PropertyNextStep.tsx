"use client";

import { useState } from "react";
import styles from "./PropertyNextStep.module.css";

export default function PropertyNextStep() {
  const [mode, setMode] = useState<"enquiry" | "visit">("enquiry");

  return (
    <section
      className={styles.section}
      id="property-next-step"
      aria-labelledby="property-next-step-heading"
    >
      <div className={styles.content}>
        <span className={styles.eyebrow}>NEXT STEP PREVIEW</span>

        <h2 id="property-next-step-heading">
          Ready to take the conversation forward?
        </h2>

        <p>
          Choose the next step you intend to take. Lead creation,
          qualification, agent routing and visit scheduling are not
          connected on this experience preview page.
        </p>

        <div
          className={styles.tabs}
          role="group"
          aria-label="Choose intended next step"
        >
          <button
            type="button"
            className={mode === "enquiry" ? styles.active : ""}
            onClick={() => setMode("enquiry")}
            aria-pressed={mode === "enquiry"}
          >
            Enquire
          </button>

          <button
            type="button"
            className={mode === "visit" ? styles.active : ""}
            onClick={() => setMode("visit")}
            aria-pressed={mode === "visit"}
          >
            Schedule visit
          </button>
        </div>

        <button
          type="button"
          className={styles.primary}
          disabled
          aria-describedby="property-next-step-disclosure"
          style={{ opacity: 0.55, cursor: "not-allowed" }}
        >
          {mode === "enquiry"
            ? "Enquiry workflow not connected"
            : "Visit request workflow not connected"}
        </button>

        <p
          id="property-next-step-disclosure"
          style={{
            margin: "10px 0 0",
            color: "#667085",
            fontSize: 11,
            lineHeight: 1.6,
          }}
        >
          This control is disabled because no approved lead/visit
          endpoint or submission form is connected. No request has
          been created or sent.
        </p>
      </div>
    </section>
  );
}
