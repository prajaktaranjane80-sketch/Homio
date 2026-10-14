"use client";

import Link from "next/link";

import { useSaveCompareSession } from "@/features/f06_save_compare/saveCompareSession";

import AIEmptyState from "./AIEmptyState";
import styles from "./AIWorkspace.module.css";

export default function AIPropertyComparison() {
  const session = useSaveCompareSession();

  return (
    <section
      className={styles.card}
      aria-labelledby="ai-property-compare-title"
    >
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.kicker}>Your existing shortlist</p>
          <h2 className={styles.cardTitle} id="ai-property-compare-title">
            Comparison board
          </h2>
          <p className={styles.muted}>
            Connected to your current F06 browser-session comparison.
          </p>
        </div>

        <span className={styles.countPill}>
          {session.comparedItems.length} / 4
        </span>
      </div>

      {session.comparedItems.length > 0 ? (
        <>
          <div className={styles.compareList}>
            {session.comparedItems.map((item) => (
              <article
                className={styles.compareItem}
                key={`${item.kind}:${item.id}`}
              >
                <span className={styles.entityType}>{item.kind}</span>

                <div className={styles.compareCopy}>
                  <strong>{item.title}</strong>
                  <span>
                    {item.subtitle ||
                      item.summary ||
                      "Additional details depend on the source record."}
                  </span>
                </div>
              </article>
            ))}
          </div>

          <Link className={styles.buttonSecondary} href="/compare">
            Open full comparison
            <span aria-hidden="true">↗</span>
          </Link>
        </>
      ) : (
        <AIEmptyState
          title="Bring two options into focus"
          description="Add properties or projects from Search to the existing F06 comparison board. Items currently last for this browser session."
          actionLabel="Explore properties"
          onAction={() => {
            window.location.assign("/search");
          }}
        />
      )}
    </section>
  );
}
