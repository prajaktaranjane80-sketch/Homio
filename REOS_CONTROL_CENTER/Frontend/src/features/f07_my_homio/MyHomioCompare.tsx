"use client";

import {
  clearComparedItems,
  removeComparedItem,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";

import { COMPARE_MAX_ITEMS } from "@/features/f06_save_compare/compare.types";

import styles from "./MyHomio.module.css";

export default function MyHomioCompare() {
  const { comparedItems } = useSaveCompareSession();

  return (
    <>
      <div className={styles.panelActions}>
        <a className={styles.button} href="/compare">
          Open side-by-side comparison ↗
        </a>
        <a className={styles.button} href="/search">
          Add another option
        </a>
        {comparedItems.length > 0 ? (
          <button
            type="button"
            className={styles.button}
            onClick={clearComparedItems}
          >
            Clear board
          </button>
        ) : null}
      </div>

      <div className={styles.featureCard}>
        <div className={styles.featureHead}>
          <h3 className={styles.featureTitle}>Decision board</h3>
          <span className={styles.statusBadge}>
            {comparedItems.length} of {COMPARE_MAX_ITEMS} options
          </span>
        </div>

        <p className={styles.featureText}>
          F06 is the single source for comparison selections. The board
          below uses that same session store, including entity-aware identity
          when different types have the same ID.
        </p>
      </div>

      {comparedItems.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptySymbol} aria-hidden="true">⇄</div>
          <h3 className={styles.emptyTitle}>Your comparison board is clear.</h3>
          <p className={styles.emptyText}>
            Add a property or project from HOMIO search. Compare supports up
            to four options and uses only facts supplied by the source.
          </p>
          <a className={`${styles.button} ${styles.buttonPrimary}`} href="/search">
            Browse options →
          </a>
        </div>
      ) : (
        <div className={styles.activityList}>
          {comparedItems.map((item) => (
            <article
              className={styles.activityRow}
              key={`${item.kind}:${item.id}`}
            >
              <div className={styles.activityMain}>
                <span className={styles.activityKind}>{item.kind}</span>

                {item.href ? (
                  <a className={styles.activityTitle} href={item.href}>
                    {item.title}
                  </a>
                ) : (
                  <strong className={styles.activityTitle}>{item.title}</strong>
                )}

                <span className={styles.activityMeta}>
                  {item.subtitle || "Location not supplied"}
                </span>

                <span className={styles.activityMeta}>
                  {item.fields.length} comparison field(s) supplied
                </span>
              </div>

              <div className={styles.activityActions}>
                {item.href ? (
                  <a className={styles.smallButton} href={item.href}>
                    View details
                  </a>
                ) : null}

                <button
                  type="button"
                  className={`${styles.smallButton} ${styles.smallButtonDanger}`}
                  onClick={() => removeComparedItem(item.id, item.kind)}
                  aria-label={`Remove ${item.title} from comparison`}
                >
                  Remove
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className={styles.notice}>
        Comparison selections remain in browser memory. A full page reload
        clears the current F06 board; account synchronization is not connected.
      </div>
    </>
  );
}
