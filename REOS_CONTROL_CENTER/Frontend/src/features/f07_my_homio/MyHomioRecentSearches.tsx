"use client";

import {
  clearRecentSearches,
  removeRecentSearch,
  removeSavedSearch,
  useMyHomioActivity,
} from "./myHomioActivityStore";

import styles from "./MyHomio.module.css";

function readableDate(value: string): string {
  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "Time unavailable"
    : new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(date);
}

export default function MyHomioRecentSearches() {
  const activity = useMyHomioActivity();

  return (
    <>
      <div className={styles.panelActions}>
        <a className={`${styles.button} ${styles.buttonPrimary}`} href="/search">
          Start a new search →
        </a>

        {activity.recentSearches.length > 0 ? (
          <button
            type="button"
            className={styles.button}
            onClick={clearRecentSearches}
          >
            Clear recent history
          </button>
        ) : null}
      </div>

      <div className={styles.notice}>
        Recent searches and saved requirements are held in this browser
        tab's session storage. Saved requirements reopen the search criteria;
        they do not create an email alert or guarantee matching inventory.
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Saved requirements</h3>
          <p>Search criteria you explicitly chose to save.</p>
        </div>
        <span className={styles.navCount}>
          {activity.savedSearches.length}
        </span>
      </div>

      {activity.savedSearches.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptySymbol} aria-hidden="true">⌕</div>
          <h3 className={styles.emptyTitle}>Keep a useful search close.</h3>
          <p className={styles.emptyText}>
            Run a search, then choose “Save this search” to keep its current
            criteria available in My HOMIO for this browser session.
          </p>
        </div>
      ) : (
        <div className={styles.activityList}>
          {activity.savedSearches.map((search) => (
            <article className={styles.activityRow} key={search.id}>
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>
                  {search.intent} / saved requirement
                </span>

                <a className={styles.activityTitle} href={search.href}>
                  {search.title}
                </a>

                <span className={styles.activityMeta}>
                  {[search.location, search.filtersLabel]
                    .filter(Boolean)
                    .join(" · ") || "No additional filters supplied"}
                </span>

                <span className={styles.activityMeta}>
                  Saved {readableDate(search.savedAt)}
                </span>
              </div>

              <div className={styles.activityActions}>
                <a className={styles.smallButton} href={search.href}>
                  Run search
                </a>

                <button
                  type="button"
                  className={`${styles.smallButton} ${styles.smallButtonDanger}`}
                  onClick={() => removeSavedSearch(search.id)}
                >
                  Remove
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className={styles.sectionHeading}>
        <div>
          <h3>Recent searches</h3>
          <p>Search criteria captured from actual Search interactions.</p>
        </div>
        <span className={styles.navCount}>
          {activity.recentSearches.length}
        </span>
      </div>

      {activity.recentSearches.length === 0 ? (
        <div className={styles.emptyState}>
          <h3 className={styles.emptyTitle}>Your search timeline is ready.</h3>
          <p className={styles.emptyText}>
            As you explore Search, HOMIO will record the last set of criteria
            used in this tab so you can reopen it without reconstructing the URL.
          </p>
          <a className={styles.textLink} href="/search">
            Open Search ↗
          </a>
        </div>
      ) : (
        <div className={styles.activityList}>
          {activity.recentSearches.map((search) => (
            <article className={styles.activityRow} key={search.id}>
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>
                  {search.intent}
                </span>

                <a className={styles.activityTitle} href={search.href}>
                  {search.title}
                </a>

                <span className={styles.activityMeta}>
                  {[search.location, search.filtersLabel]
                    .filter(Boolean)
                    .join(" · ") || "No additional filters supplied"}
                </span>

                <span className={styles.activityMeta}>
                  Last searched {readableDate(search.searchedAt)}
                </span>
              </div>

              <div className={styles.activityActions}>
                <a className={styles.smallButton} href={search.href}>
                  Reopen
                </a>

                <button
                  type="button"
                  className={styles.smallButton}
                  onClick={() => removeRecentSearch(search.id)}
                  aria-label={`Remove ${search.title} from recent search history`}
                >
                  Dismiss
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
