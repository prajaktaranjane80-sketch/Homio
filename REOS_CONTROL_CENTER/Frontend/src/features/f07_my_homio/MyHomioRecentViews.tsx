"use client";

import {
  clearRecentViews,
  removeRecentView,
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

export default function MyHomioRecentViews() {
  const activity = useMyHomioActivity();

  return (
    <>
      <div className={styles.panelActions}>
        <a className={`${styles.button} ${styles.buttonPrimary}`} href="/search">
          Continue discovery →
        </a>

        {activity.recentViews.length > 0 ? (
          <button
            type="button"
            className={styles.button}
            onClick={clearRecentViews}
          >
            Clear viewed history
          </button>
        ) : null}
      </div>

      <div className={styles.notice}>
        This list records property and project detail pages opened through
        HOMIO. It is browsing history for the current browser tab—not a
        physical site visit, enquiry or appointment.
      </div>

      {activity.recentViews.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptySymbol} aria-hidden="true">↗</div>
          <h3 className={styles.emptyTitle}>Your viewed properties will appear here.</h3>
          <p className={styles.emptyText}>
            Open a property or project detail page. HOMIO will record that
            actual page view and provide a direct path back to its details.
          </p>
          <a className={styles.textLink} href="/search">
            Browse properties and projects ↗
          </a>
        </div>
      ) : (
        <div className={styles.activityList}>
          {activity.recentViews.map((view) => (
            <article className={styles.activityRow} key={view.id}>
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>
                  {view.kind} / detail preview
                </span>

                <a className={styles.activityTitle} href={view.href}>
                  {view.title}
                </a>

                <span className={styles.activityMeta}>
                  {view.subtitle || "Location not supplied"}
                </span>

                <span className={styles.activityMeta}>
                  Opened {readableDate(view.viewedAt)}
                </span>
              </div>

              <div className={styles.activityActions}>
                <a className={styles.smallButton} href={view.href}>
                  Return to details
                </a>

                <button
                  type="button"
                  className={styles.smallButton}
                  onClick={() => removeRecentView(view.id)}
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
