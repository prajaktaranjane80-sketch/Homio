"use client";

import type { SearchIntent } from "@/features/f03_search/search.types";

import { AI_INTENT_OPTIONS } from "./ai.constants";
import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  intent: SearchIntent;
  location: string;
  onIntentChange: (value: SearchIntent) => void;
  onLocationChange: (value: string) => void;
  onOpenSearch: () => void;
}>;

export default function AISearch({
  intent,
  location,
  onIntentChange,
  onLocationChange,
  onOpenSearch,
}: Props) {
  return (
    <section
      className={styles.card}
      aria-labelledby="ai-search-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Discovery, made clearer</p>
          <h2 className={styles.cardTitle} id="ai-search-title">
            What are you looking for?
          </h2>
          <p className={styles.muted}>
            Set the direction first. Refine the details in HOMIO Search.
          </p>
        </div>

        <span className={styles.cardGlyph} aria-hidden="true">
          ⌕
        </span>
      </div>

      <div className={styles.fieldGrid}>
        <div className={styles.controlGroup}>
          <label className={styles.label} htmlFor="ai-intent">
            I want to
          </label>

          <select
            id="ai-intent"
            className={styles.select}
            value={intent}
            onChange={(event) => {
              onIntentChange(event.currentTarget.value as SearchIntent);
            }}
          >
            {AI_INTENT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.controlGroup}>
          <label className={styles.label} htmlFor="ai-location">
            City, locality or landmark
          </label>

          <input
            id="ai-location"
            className={styles.input}
            value={location}
            maxLength={120}
            onChange={(event) => {
              onLocationChange(event.currentTarget.value);
            }}
            placeholder="e.g. Singapore, Dubai Marina, Tokyo"
          />
        </div>
      </div>

      <div className={styles.inlineActions}>
        <button
          className={styles.buttonPrimary}
          type="button"
          onClick={onOpenSearch}
        >
          Continue to property search
          <span aria-hidden="true">↗</span>
        </button>

        <span className={styles.fieldHelp}>
          Opens the existing F03 search experience.
        </span>
      </div>
    </section>
  );
}
