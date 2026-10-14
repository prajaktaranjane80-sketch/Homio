"use client";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}>;

export default function AIEmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: Props) {
  return (
    <div className={styles.emptyState}>
      <span className={styles.emptySymbol} aria-hidden="true">
        ✦
      </span>

      <h3 className={styles.emptyTitle}>{title}</h3>
      <p className={styles.muted}>{description}</p>

      {actionLabel && onAction ? (
        <button
          className={styles.buttonSecondary}
          type="button"
          onClick={onAction}
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
