import type { ReactNode } from "react";
import styles from "./SavedCompareExperience.module.css";

type SavedEmptyStateProps = Readonly<{
  title: string;
  description: string;
  action?: ReactNode;
  icon?: string;
}>;

export default function SavedEmptyState({
  title,
  description,
  action,
  icon = "✧",
}: SavedEmptyStateProps) {
  return (
    <section className={styles.emptyState} aria-label={title}>
      <span className={styles.emptyOrb} aria-hidden="true">{icon}</span>
      <p className={styles.eyebrow}>YOUR SPACE · READY WHEN YOU ARE</p>
      <h3>{title}</h3>
      <p className={styles.emptyDescription}>{description}</p>
      {action ? <div className={styles.emptyAction}>{action}</div> : null}
    </section>
  );
}
