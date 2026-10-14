"use client";

import type { SearchIntent } from "@/features/f03_search/search.types";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  onSelectPrompt: (
    prompt: string,
    intent?: SearchIntent,
  ) => void;
}>;

export default function AIMarketAssistant({
  onSelectPrompt,
}: Props) {
  return (
    <section
      className={styles.compactCard}
      aria-labelledby="ai-market-title"
    >
      <p className={styles.kicker}>Market context</p>

      <h2 className={styles.cardTitle} id="ai-market-title">
        Read the market with care
      </h2>

      <p className={styles.muted}>
        Record the source, date and method behind each market claim.
      </p>

      <div className={styles.marketChecklist}>
        <span>Comparable properties</span>
        <span>Source and publication date</span>
        <span>Asking versus achieved price</span>
        <span>Supply and demand context</span>
      </div>

      <button
        className={styles.buttonSecondary}
        type="button"
        onClick={() => {
          onSelectPrompt(
            "Prepare a checklist to evaluate a real-estate market claim: source and date, comparable sales or rents, asking versus achieved prices, supply, demand, sample size and uncertainty.",
          );
        }}
      >
        Prepare a market review
        <span aria-hidden="true">↗</span>
      </button>

      <p className={styles.disclosure}>
        No live prices, appreciation rates or forecasts are retrieved in this preview.
      </p>
    </section>
  );
}
