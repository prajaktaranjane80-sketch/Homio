import Link from "next/link";
import type { ReactNode } from "react";

import { getEmptyStateCopy } from "@/features/f13_production/EmptyStatePolicy";

import styles from "./SavedCompareExperience.module.css";

type CompareEmptyStateProps = Readonly<{
  title?: string;
  description?: string;
  action?: ReactNode;
}>;

export default function CompareEmptyState({
  title,
  description,
  action,
}: CompareEmptyStateProps) {
  const policy = getEmptyStateCopy("no-comparisons");
  const heading = title ?? policy.title;
  const detail = description ?? policy.description;

  return (
    <section className={styles.emptyState} aria-label={heading}>
      <span className={styles.emptyOrb} aria-hidden="true">⇄</span>
      <p className={styles.eyebrow}>DECIDE WITH CLARITY</p>
      <h3>{heading}</h3>
      <p className={styles.emptyDescription}>{detail}</p>
      {action ? (
        <div className={styles.emptyAction}>{action}</div>
      ) : policy.actionHref && policy.actionLabel ? (
        <div className={styles.emptyAction}>
          <Link className="button button--secondary" href={policy.actionHref}>
            {policy.actionLabel}
          </Link>
        </div>
      ) : null}
    </section>
  );
}
