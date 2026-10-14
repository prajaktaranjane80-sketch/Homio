"use client";

import type { SearchCurrency } from "@/features/f03_search/search.types";

import { AI_CURRENCY_OPTIONS } from "./ai.constants";
import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  budget: string;
  currency: SearchCurrency;
  onBudgetChange: (value: string) => void;
  onCurrencyChange: (value: SearchCurrency) => void;
}>;

export default function AIBudgetGuidance({
  budget,
  currency,
  onBudgetChange,
  onCurrencyChange,
}: Props) {
  return (
    <section
      className={styles.card}
      aria-labelledby="ai-budget-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>A more realistic brief</p>
          <h2 className={styles.cardTitle} id="ai-budget-title">
            Set your budget ceiling
          </h2>
        </div>

        <span className={styles.cardGlyph} aria-hidden="true">
          ◇
        </span>
      </div>

      <div className={styles.fieldGrid}>
        <div className={styles.controlGroup}>
          <label className={styles.label} htmlFor="ai-budget-currency">
            Currency
          </label>

          <select
            id="ai-budget-currency"
            className={styles.select}
            value={currency}
            onChange={(event) => {
              onCurrencyChange(event.currentTarget.value as SearchCurrency);
            }}
          >
            {AI_CURRENCY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.controlGroup}>
          <label className={styles.label} htmlFor="ai-budget">
            Maximum budget
          </label>

          <input
            id="ai-budget"
            className={styles.input}
            type="number"
            min="0"
            step="any"
            inputMode="decimal"
            value={budget}
            onChange={(event) => {
              onBudgetChange(event.currentTarget.value);
            }}
            placeholder="Enter amount"
          />
        </div>
      </div>

      <ul className={styles.guidanceList}>
        <li>
          Keep a separate allowance for taxes, fees, moving or fit-out costs.
        </li>
        <li>
          Confirm financing terms and recurring charges with the relevant provider.
        </li>
        <li>
          Compare equivalent area, condition and included features, not price alone.
        </li>
      </ul>

      <p className={styles.disclosure}>
        Guidance only. No affordability result is calculated and no financial advice is provided.
      </p>
    </section>
  );
}
