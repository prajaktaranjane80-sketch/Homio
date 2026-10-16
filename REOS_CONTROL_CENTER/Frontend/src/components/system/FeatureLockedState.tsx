import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  title: string;
  description: string;
  requirement?: string;
}>;

export function FeatureLockedState({ title, description, requirement }: Props) {
  return (
    <section className={styles.systemCard} aria-labelledby="feature-locked-title">
      <div className={styles.systemRow}>
        <span className={styles.systemIcon} aria-hidden="true">⌑</span>
        <div>
          <span className={styles.systemEyebrow}>Access boundary</span>
          <h2 className={styles.systemTitle} id="feature-locked-title">{title}</h2>
          <p className={styles.systemDescription}>{description}</p>
        </div>
      </div>
      {requirement ? <p className={styles.systemFootnote}>Requirement: {requirement}</p> : null}
      <p className={styles.systemFootnote}>
        A visible lock is informational only. Protected records and operations
        must still be authorized by the server.
      </p>
    </section>
  );
}
