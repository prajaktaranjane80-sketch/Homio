"use client";

import type { SearchIntent } from "./search.types";
import styles from "./PopularSearches.module.css";

export type PopularSearch = {
  id: string;
  label: string;
  intent: SearchIntent;
  location: string;
  meta?: string;
};

type PopularSearchesProps = Readonly<{
  searches: PopularSearch[];
  onSelect?: (search: PopularSearch) => void;
}>;

export default function PopularSearches({
  searches,
  onSelect,
}: PopularSearchesProps) {
  if (searches.length === 0) {
    return null;
  }

  return (
    <section
      className={styles.section}
      aria-labelledby="popular-searches-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>DISCOVER</span>
          <h2 id="popular-searches-title">Popular searches</h2>
        </div>
      </div>

      <div className={styles.grid}>
        {searches.map((search) => (
          <button
            key={search.id}
            type="button"
            className={styles.card}
            onClick={() => onSelect?.(search)}
          >
            <span className={styles.icon} aria-hidden="true">
              ↗
            </span>

            <span className={styles.content}>
              <strong>{search.label}</strong>

              <span className={styles.meta}>
                {search.location}
                {search.meta ? ` · ${search.meta}` : ""}
              </span>

              <span className={styles.intent}>{search.intent}</span>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
