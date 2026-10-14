"use client";

import Link from "next/link";

import {
  clearComparedItems,
  removeComparedItem,
  useSaveCompareSession,
} from "@/features/f06_save_compare/saveCompareSession";
import { COMPARE_FIELD_GROUPS } from "@/features/f06_save_compare/compare.types";
import styles from "@/features/f06_save_compare/SaveComparePages.module.css";

export default function ComparePage() {
  const { comparedItems } = useSaveCompareSession();

  const fields = Array.from(
    new Set(comparedItems.flatMap((item) => item.fields.map((field) => field.label))),
  );

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href="/search" className={styles.backLink}>
          ← Back to discovery
        </Link>

        <p className={styles.eyebrow}>SIDE-BY-SIDE DISCOVERY</p>
        <h1>Compare items</h1>
        <p className={styles.intro}>
          Compare source-supplied details for up to four property or project
          previews.
        </p>

        <p className={styles.notice} role="note">
          Session only: comparisons are held in browser memory, not synced to
          an account, and cleared after a full page reload. Missing values mean
          the preview has not supplied that detail.
        </p>

        {comparedItems.length === 0 ? (
          <section className={styles.empty}>
            <h2>Nothing to compare yet</h2>
            <p>
              Use Compare on a property or project card to add it to this table.
              You can compare up to four items at a time.
            </p>
            <Link href="/search" className={styles.primaryLink}>
              Explore properties
            </Link>
          </section>
        ) : (
          <>
            <div className={styles.compareActions}>
              <p>{comparedItems.length} of 4 items selected</p>
              <button
                type="button"
                className={styles.removeButton}
                onClick={clearComparedItems}
              >
                Clear comparison
              </button>
            </div>

            <div className={styles.tableWrap}>
              <table className={styles.compareTable}>
                <thead>
                  <tr>
                    <th scope="col">Details</th>
                    {comparedItems.map((item) => (
                      <th
                        scope="col"
                        key={`${item.kind}:${item.id}`}
                      >
                        <span className={styles.kind}>{item.kind}</span>
                        <span className={styles.compareTitle}>
                          {item.href ? (
                            <Link href={item.href}>{item.title}</Link>
                          ) : (
                            item.title
                          )}
                        </span>
                        {item.subtitle ? (
                          <span className={styles.compareSubtitle}>
                            {item.subtitle}
                          </span>
                        ) : null}
                        <button
                          type="button"
                          className={styles.removeButton}
                          onClick={() => removeComparedItem(item.id)}
                          aria-label={`Remove ${item.title} from comparison`}
                        >
                          Remove
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {COMPARE_FIELD_GROUPS.map((group) => {
                    const groupFields = fields.filter((label) =>
                      comparedItems.some((item) =>
                        item.fields.some(
                          (field) =>
                            field.label === label && field.group === group.id,
                        ),
                      ),
                    );

                    if (groupFields.length === 0) {
                      return null;
                    }

                    return groupFields.map((label, index) => (
                      <tr key={`${group.id}:${label}`}>
                        <th scope="row">
                          {index === 0 ? (
                            <span className={styles.groupLabel}>
                              {group.label}
                            </span>
                          ) : null}
                          {label}
                        </th>
                        {comparedItems.map((item) => {
                          const field = item.fields.find(
                            (entry) =>
                              entry.label === label && entry.group === group.id,
                          );
                          const value = field?.value;

                          return (
                            <td key={`${item.kind}:${item.id}:${label}`}>
                              {value === null ||
                              value === undefined ||
                              value === "" ? (
                                <span className={styles.missing}>Not supplied</span>
                              ) : (
                                String(value)
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ));
                  })}

                  <tr>
                    <th scope="row">Status</th>
                    {comparedItems.map((item) => (
                      <td key={`${item.kind}:${item.id}:status`}>
                        {item.statusLabel || "Not supplied"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </>
        )}

        <p className={styles.footerNote}>
          This is an informational comparison of preview fields, not a
          recommendation or confirmation of listing accuracy.
        </p>
      </div>
    </main>
  );
}
