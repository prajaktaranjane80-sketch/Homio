"use client";

import type { SearchIntent } from "./search.types";
import styles from "./RecentSearches.module.css";

export type RecentSearch = {
  id: string;
  label: string;
  intent: SearchIntent;
  location?: string;
  filtersLabel?: string;
  createdAt: string;
};

type RecentSearchesProps = Readonly<{
  searches: RecentSearch[];
  onSelect?: (search: RecentSearch) => void;
  onRemove?: (search: RecentSearch) => void;
}>;

const intentLabels: Record<SearchIntent, string> = {
  buy: "Buy",
  rent: "Rent",
  commercial: "Commercial",
  projects: "Projects",
  land: "Land",
};

export default function RecentSearches({
  searches,
  onSelect,
  onRemove,
}: RecentSearchesProps) {
  if (searches.length === 0) {
    return null;
  }

  return (
    <section className={styles.section} aria-labelledby="recent-searches-title">
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>YOUR ACTIVITY</span>
          <h2 id="recent-searches-title">Recent searches</h2>
        </div>
      </div>

      <div className={styles.list}>
        {searches.map((search) => (
          <div key={search.id} className={styles.item}>
            <button
              type="button"
              className={styles.main}
              onClick={() => onSelect?.(search)}
            >
              <span className={styles.icon} aria-hidden="true">
                ↗
              </span>

              <span className={styles.content}>
                <strong>{search.label}</strong>

                <span>
                  {intentLabels[search.intent]}
                  {search.location ? ` · ${search.location}` : ""}
                  {search.filtersLabel ? ` · ${search.filtersLabel}` : ""}
                </span>

                <small>{search.createdAt}</small>
              </span>
            </button>

            {onRemove ? (
              <button
                type="button"
                className={styles.remove}
                onClick={() => onRemove(search)}
                aria-label={`Remove ${search.label} from recent searches`}
              >
                ×
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
