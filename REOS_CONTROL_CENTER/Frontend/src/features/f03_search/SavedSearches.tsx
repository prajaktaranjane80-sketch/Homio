"use client";

import type { SearchIntent } from "./search.types";
import styles from "./SavedSearches.module.css";

export type SavedSearch = {
  id: string;
  name: string;
  intent: SearchIntent;
  location?: string;
  filtersLabel?: string;
  alertsEnabled?: boolean;
};

type SavedSearchesProps = Readonly<{
  searches: SavedSearch[];
  onOpen?: (search: SavedSearch) => void;
  onToggleAlerts?: (search: SavedSearch) => void;
  onRemove?: (search: SavedSearch) => void;
}>;

const intentLabels: Record<SearchIntent, string> = {
  buy: "Buy",
  rent: "Rent",
  commercial: "Commercial",
  projects: "Projects",
  land: "Land",
};

export default function SavedSearches({
  searches,
  onOpen,
  onToggleAlerts,
  onRemove,
}: SavedSearchesProps) {
  if (searches.length === 0) {
    return null;
  }

  return (
    <section className={styles.section} aria-labelledby="saved-searches-title">
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>MY HOMIO</span>
          <h2 id="saved-searches-title">Saved searches</h2>
        </div>
      </div>

      <div className={styles.grid}>
        {searches.map((search) => (
          <article key={search.id} className={styles.card}>
            <div className={styles.top}>
              <span className={styles.badge}>
                {intentLabels[search.intent]}
              </span>

              {search.alertsEnabled ? (
                <span className={styles.alertBadge}>Alerts on</span>
              ) : null}
            </div>

            <h3>{search.name}</h3>

            <p>
              {search.location || "All available locations"}
              {search.filtersLabel ? ` · ${search.filtersLabel}` : ""}
            </p>

            <div className={styles.actions}>
              <button
                type="button"
                className={styles.primary}
                onClick={() => onOpen?.(search)}
              >
                Open search
              </button>

              {onToggleAlerts ? (
                <button
                  type="button"
                  className={styles.secondary}
                  onClick={() => onToggleAlerts(search)}
                >
                  {search.alertsEnabled ? "Turn alerts off" : "Turn alerts on"}
                </button>
              ) : null}

              {onRemove ? (
                <button
                  type="button"
                  className={styles.remove}
                  onClick={() => onRemove(search)}
                >
                  Remove
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
