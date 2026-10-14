"use client";

import { useSaveCompareSession, removeSavedRecord } from "@/features/f06_save_compare/saveCompareSession";

import styles from "./MyHomio.module.css";

export default function MyHomioSaved() {
  const { savedRecords } = useSaveCompareSession();

  return (
    <>
      <div className={styles.panelActions}>
        <a className={styles.button} href="/saved">
          Open full Saved workspace ↗
        </a>
        <a className={styles.button} href="/search">
          Discover more options
        </a>
      </div>

      <div className={styles.notice}>
        F06 currently holds Save and Compare selections in browser memory.
        They are not account-synced and reset after a full page reload.
      </div>

      {savedRecords.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptySymbol} aria-hidden="true">♡</div>
          <h3 className={styles.emptyTitle}>Nothing saved in this session yet.</h3>
          <p className={styles.emptyText}>
            Use Save from a property card, project card or detail page.
            Your real selection will appear here without fabricated listings.
          </p>
          <a className={`${styles.button} ${styles.buttonPrimary}`} href="/search">
            Explore HOMIO →
          </a>
        </div>
      ) : (
        <div className={styles.activityList}>
          {savedRecords.map((record) => (
            <article
              className={styles.activityRow}
              key={`${record.kind}:${record.id}`}
            >
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>{record.kind}</span>

                {record.href ? (
                  <a className={styles.activityTitle} href={record.href}>
                    {record.title}
                  </a>
                ) : (
                  <strong className={styles.activityTitle}>
                    {record.title}
                  </strong>
                )}

                <span className={styles.activityMeta}>
                  {[record.subtitle, record.detailLine]
                    .filter(Boolean)
                    .join(" · ") || "Additional details not supplied"}
                </span>
                {record.statusLabel ? (
                  <span className={styles.activityMeta}>
                    {record.statusLabel}
                  </span>
                ) : null}
              </div>

              <div className={styles.activityActions}>
                {record.href ? (
                  <a className={styles.smallButton} href={record.href}>
                    Reopen
                  </a>
                ) : null}

                <button
                  type="button"
                  className={`${styles.smallButton} ${styles.smallButtonDanger}`}
                  onClick={() => removeSavedRecord(record.id, record.kind)}
                  aria-label={`Remove ${record.title} from saved items`}
                >
                  Remove
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      <p className={styles.footer}>
        Showing {savedRecords.length} saved item(s) from the current F06
        browser-memory session.
      </p>
    </>
  );
}
