import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  label?: string;
  detail?: string;
}>;

export function LoadingScreen({
  label = "Loading workspace",
  detail = "Retrieving the latest available information.",
}: Props) {
  return (
    <section className={styles.systemCard} role="status" aria-live="polite">
      <span className={styles.systemEyebrow}>HOMIO / WORKSPACE</span>
      <h2 className={styles.systemTitle}>{label}</h2>
      <p className={styles.systemDescription}>{detail}</p>
      <div style={{ marginTop: 20 }} className={styles.systemSkeletonGrid}>
        {[0, 1, 2].map((item) => (
          <div className={styles.systemSkeletonCard} key={item}>
            <span className={`${styles.systemSkeleton} ${styles.systemSkeletonShort}`} />
            <span className={`${styles.systemSkeleton} ${styles.systemSkeletonMedium}`} />
            <span className={styles.systemSkeleton} />
          </div>
        ))}
      </div>
    </section>
  );
}
