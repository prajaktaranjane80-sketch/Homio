import type { ReactNode } from "react";
import styles from "./SavedCompareExperience.module.css";

type CompareEmptyStateProps = Readonly<{
  title?: string;
  description?: string;
  action?: ReactNode;
}>;

export default function CompareEmptyState({
  title = "Your comparison starts here",
  description = "Add properties, projects or localities from a connected HOMIO experience. Once options are available, meaningful differences will appear side by side.",
  action,
}: CompareEmptyStateProps) {
  return (
    <section className={styles.emptyState} aria-label={title}>
      <span className={styles.emptyOrb} aria-hidden="true">⇄</span>
      <p className={styles.eyebrow}>DECIDE WITH CLARITY</p>
      <h3>{title}</h3>
      <p className={styles.emptyDescription}>{description}</p>
      {action ? <div className={styles.emptyAction}>{action}</div> : null}
    </section>
  );
}
