"use client";

import { useMyHomioActivity } from "./myHomioActivityStore";

import styles from "./MyHomio.module.css";

export default function MyHomioRecommendations() {
  const activity = useMyHomioActivity();

  return (
    <>
      <header className={styles.panelHeader}>
        <p className={styles.kicker}>PERSONALIZED DISCOVERY</p>

        <h2 className={styles.panelTitle}>Recommendations for your next move</h2>

        <p className={styles.panelLead}>
          A future recommendation feed should connect your real search
          requirements to eligible property and project records, with clear
          reasons for each match.
        </p>
      </header>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Recommendation feed</h3>
          <span className={styles.statusBadge}>Matching service required</span>
        </div>

        <p className={styles.featureText}>
          No approved personalized recommendation feed is connected to this
          account. HOMIO will not label arbitrary catalogue items as
          personalized matches.
        </p>

        <div className={styles.panelActions}>
          <a className={`${styles.button} ${styles.buttonPrimary}`} href="/search">
            Explore available previews →
          </a>
          <a className={styles.button} href="/search">
            Define a requirement
          </a>
        </div>
      </div>

      <div className={styles.sectionHeading}>
        <div>
          <h3>Your saved requirements</h3>
          <p>Actual search criteria that could inform recommendations later.</p>
        </div>
        <span className={styles.navCount}>{activity.savedSearches.length}</span>
      </div>

      {activity.savedSearches.length === 0 ? (
        <div className={styles.emptyState}>
          <h3 className={styles.emptyTitle}>No saved requirement is available yet.</h3>
          <p className={styles.emptyText}>
            Save a search from the Search page. That records your requirement
            in this browser tab; it does not automatically activate alerts or
            return recommendations.
          </p>
          <a className={styles.textLink} href="/search">
            Create a saved requirement →
          </a>
        </div>
      ) : (
        <div className={styles.activityList}>
          {activity.savedSearches.map((search) => (
            <article className={styles.activityRow} key={search.id}>
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>
                  Saved {search.intent} requirement
                </span>
                <a className={styles.activityTitle} href={search.href}>
                  {search.title}
                </a>
                <span className={styles.activityMeta}>
                  {[search.location, search.filtersLabel]
                    .filter(Boolean)
                    .join(" · ") || "No additional filters supplied"}
                </span>
              </div>

              <a className={styles.smallButton} href={search.href}>
                Reopen search
              </a>
            </article>
          ))}
        </div>
      )}

      <div className={styles.notice}>
        This panel shows requirements—not recommended listings. Actual matches
        require an approved matching source and source-backed reason codes.
      </div>
    </>
  );
}
