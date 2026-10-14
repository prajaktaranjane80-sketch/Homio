"use client";

import type { SearchIntent } from "@/features/f03_search/search.types";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  onSelectPrompt: (
    prompt: string,
    intent?: SearchIntent,
  ) => void;
}>;

export default function AIInvestmentAssistant({
  onSelectPrompt,
}: Props) {
  return (
    <section
      className={styles.compactCard}
      aria-labelledby="ai-investment-title"
    >
      <p className={styles.kicker}>Investment readiness</p>

      <h2 className={styles.cardTitle} id="ai-investment-title">
        Ask better investment questions
      </h2>

      <p className={styles.muted}>
        Separate assumptions from evidence before evaluating a property.
      </p>

      <ul className={styles.guidanceList}>
        <li>Which comparable sales and rents can be independently verified?</li>
        <li>
          Which vacancy, maintenance, financing and resale assumptions need testing?
        </li>
        <li>What legal and tax checks apply in this jurisdiction?</li>
      </ul>

      <button
        className={styles.buttonSecondary}
        type="button"
        onClick={() => {
          onSelectPrompt(
            "Prepare an investment due-diligence checklist covering verified comparable data, rental assumptions, vacancy, recurring costs, financing, resale and local legal checks.",
          );
        }}
      >
        Build due-diligence checklist
        <span aria-hidden="true">↗</span>
      </button>

      <p className={styles.disclosure}>
        Not investment, tax or legal advice. No return forecast is produced.
      </p>
    </section>
  );
}
