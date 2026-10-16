import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  count?: number;
  columns?: 1 | 2 | 3 | 4;
  label?: string;
}>;

export function SkeletonGrid({
  count = 6,
  columns = 3,
  label = "Loading results",
}: Props) {
  const safeCount = Number.isFinite(count)
    ? Math.max(1, Math.min(12, Math.floor(count)))
    : 6;

  return (
    <div
      className={styles.systemSkeletonGrid}
      style={{ "--skeleton-columns": columns } as React.CSSProperties}
      role="status"
      aria-label={label}
    >
      {Array.from({ length: safeCount }, (_, index) => (
        <div className={styles.systemSkeletonCard} key={index}>
          <span className={`${styles.systemSkeleton} ${styles.systemSkeletonShort}`} />
          <span className={styles.systemSkeleton} style={{ "--skeleton-height": "96px" } as React.CSSProperties} />
          <span className={`${styles.systemSkeleton} ${styles.systemSkeletonMedium}`} />
          <span className={styles.systemSkeleton} />
        </div>
      ))}
    </div>
  );
}
