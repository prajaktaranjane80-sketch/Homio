"use client";

import styles from "./AIWorkspace.module.css";

type Props = Readonly<{
  message: string;
  onDismiss?: () => void;
}>;

export default function AIErrorState({
  message,
  onDismiss,
}: Props) {
  return (
    <div className={styles.errorState} role="alert">
      <span className={styles.errorGlyph} aria-hidden="true">
        !
      </span>

      <div className={styles.errorCopy}>
        <strong>Check this before continuing</strong>
        <p>{message}</p>
      </div>

      {onDismiss ? (
        <button
          className={styles.dismissButton}
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss message"
        >
          ×
        </button>
      ) : null}
    </div>
  );
}
