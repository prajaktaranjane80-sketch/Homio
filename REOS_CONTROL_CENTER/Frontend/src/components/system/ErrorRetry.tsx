import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  title?: string;
  description: string;
  onRetry?: () => void;
  retryLabel?: string;
  retryDisabled?: boolean;
}>;

export function ErrorRetry({
  title = "We couldn't load this information",
  description,
  onRetry,
  retryLabel = "Try again",
  retryDisabled = false,
}: Props) {
  return (
    <section className={styles.systemCard} role="alert">
      <div className={styles.systemRow}>
        <span className={styles.systemIcon} aria-hidden="true">!</span>
        <div>
          <span className={styles.systemEyebrow}>Request interrupted</span>
          <h2 className={styles.systemTitle}>{title}</h2>
          <p className={styles.systemDescription}>{description}</p>
        </div>
      </div>
      {onRetry ? (
        <div className={styles.systemActions}>
          <button type="button" className={styles.systemActionButton} onClick={onRetry} disabled={retryDisabled}>
            {retryLabel}
          </button>
        </div>
      ) : null}
    </section>
  );
}
