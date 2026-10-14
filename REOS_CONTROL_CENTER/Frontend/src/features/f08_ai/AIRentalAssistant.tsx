"use client";

import type { SearchIntent } from "@/features/f03_search/search.types";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  onSelectPrompt: (
    prompt: string,
    intent?: SearchIntent,
  ) => void;
}>;

export default function AIRentalAssistant({
  onSelectPrompt,
}: Props) {
  return (
    <section
      className={styles.compactCard}
      aria-labelledby="ai-rental-title"
    >
      <p className={styles.kicker}>Rental planning</p>

      <h2 className={styles.cardTitle} id="ai-rental-title">
        Make the lease work for you
      </h2>

      <p className={styles.muted}>
        Cover practical details as well as monthly rent.
      </p>

      <ul className={styles.guidanceList}>
        <li>Lease length, deposit, renewal and notice requirements.</li>
        <li>Commute, utilities, parking, furnishing and pet policies.</li>
        <li>Property condition and maintenance responsibility.</li>
      </ul>

      <button
        className={styles.buttonSecondary}
        type="button"
        onClick={() => {
          onSelectPrompt(
            "Help me prepare a rental brief and viewing checklist covering monthly budget, commute, lease term, deposit, utilities, furnishing, maintenance and move-in date.",
            "rent",
          );
        }}
      >
        Create rental brief
        <span aria-hidden="true">↗</span>
      </button>
    </section>
  );
}
