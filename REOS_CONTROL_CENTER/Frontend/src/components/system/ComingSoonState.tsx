import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  title: string;
  description: string;
  market?: string;
}>;

export function ComingSoonState({ title, description, market }: Props) {
  return (
    <section className={styles.systemCard} aria-labelledby="coming-soon-title">
      <div className={styles.systemRow}>
        <span className={styles.systemIcon} aria-hidden="true">↗</span>
        <div>
          <span className={styles.systemEyebrow}>HOMIO roadmap</span>
          <h2 className={styles.systemTitle} id="coming-soon-title">{title}</h2>
          {market ? <span className={`${styles.systemBadge} ${styles.systemBadgeWarning}`}>{market}</span> : null}
        </div>
      </div>
      <p className={styles.systemDescription} style={{ marginTop: 14 }}>{description}</p>
      <p className={styles.systemFootnote}>
        This is a future capability notice, not a promise of an activation date.
      </p>
    </section>
  );
}
