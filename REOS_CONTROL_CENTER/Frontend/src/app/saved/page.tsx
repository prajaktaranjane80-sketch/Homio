"use client";

import Link from "next/link";

import {
  removeSavedRecord,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";
import styles from "@/features/f06_save_compare/SaveComparePages.module.css";

export default function SavedPage() {
  const { savedRecords } = useSaveCompareSession();

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href="/search" className={styles.backLink}>
          ← Back to discovery
        </Link>

        <p className={styles.eyebrow}>YOUR HOMIO COLLECTION</p>
        <h1>Saved items</h1>
        <p className={styles.intro}>
          Keep property and project previews together while you explore.
        </p>

        <p className={styles.notice} role="note">
          Session only: this list is held in browser memory. It is not saved to
          an account and will clear after a full page reload.
        </p>

        {savedRecords.length === 0 ? (
          <section className={styles.empty}>
            <h2>No saved items yet</h2>
            <p>
              Save a property or project from its card or detail page to see it
              here.
            </p>
            <Link href="/search" className={styles.primaryLink}>
              Explore properties
            </Link>
          </section>
        ) : (
          <div className={styles.list}>
            {savedRecords.map((record) => (
              <article
                className={styles.item}
                key={`${record.kind}:${record.id}`}
              >
                <div className={styles.itemContent}>
                  <span className={styles.kind}>{record.kind}</span>
                  <h2>
                    {record.href ? (
                      <Link href={record.href}>{record.title}</Link>
                    ) : (
                      record.title
                    )}
                  </h2>
                  {record.subtitle ? <p>{record.subtitle}</p> : null}
                  {record.statusLabel ? (
                    <p className={styles.meta}>{record.statusLabel}</p>
                  ) : null}
                  {record.detailLine ? (
                    <p className={styles.meta}>{record.detailLine}</p>
                  ) : null}
                </div>

                <button
                  type="button"
                  className={styles.removeButton}
                  onClick={() => removeSavedRecord(record.id)}
                  aria-label={`Remove ${record.title} from saved items`}
                >
                  Remove
                </button>
              </article>
            ))}
          </div>
        )}

        <p className={styles.footerNote}>
          HOMIO preview data does not itself confirm availability, verification,
          pricing, or a transaction.
        </p>
      </div>
    </main>
  );
}
