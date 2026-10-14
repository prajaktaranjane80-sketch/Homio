"use client";

import Link from "next/link";

import styles from "./AIWorkspace.module.css";

export default function AIBrokerageHandoff() {
  return (
    <section
      className={styles.handoffCard}
      aria-labelledby="ai-handoff-title"
    >
      <p className={styles.kicker}>When you are ready</p>

      <h2 className={styles.cardTitle} id="ai-handoff-title">
        Move from exploration to action
      </h2>

      <p className={styles.handoffCopy}>
        Continue into HOMIO discovery, compare your shortlist or return to your personal workspace.
      </p>

      <div className={styles.handoffActions}>
        <Link className={styles.buttonPrimary} href="/search">
          Explore properties
          <span aria-hidden="true">↗</span>
        </Link>

        <Link className={styles.buttonQuiet} href="/my">
          Open My HOMIO
        </Link>
      </div>

      <p className={styles.disclosure}>
        This navigation does not submit an enquiry, create a lead or notify a broker.
      </p>
    </section>
  );
}
