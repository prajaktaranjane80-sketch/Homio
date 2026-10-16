import type { ReactNode } from "react";
import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  title: string;
  description: string;
  action?: ReactNode;
}>;

export function EmptyResults({ title, description, action }: Props) {
  return (
    <section className={styles.systemCard} aria-labelledby="empty-results-title">
      <div className={styles.systemRow}>
        <span className={styles.systemIcon} aria-hidden="true">⌕</span>
        <div>
          <span className={styles.systemEyebrow}>No items to display</span>
          <h2 className={styles.systemTitle} id="empty-results-title">{title}</h2>
          <p className={styles.systemDescription}>{description}</p>
        </div>
      </div>
      {action ? <div className={styles.systemActions}>{action}</div> : null}
    </section>
  );
}
