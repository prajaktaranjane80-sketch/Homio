
/* File: src/components/system/SkeletonGrid.tsx */
import { Skeleton } from "@/components/ui/Skeleton";

import styles from "./SharedSystem.module.css";

type Props = Readonly<{
  count?: number;
  columns?: 1 | 2 | 3 | 4;
  label?: string;
}>;

export default function SkeletonGrid({
  count = 6,
  columns = 3,
  label = "Loading results",
}: Props) {
  const safeCount = Math.max(1, Math.min(Math.floor(count), 12));

  return (
    <div
      className={styles.skeletonGrid}
      style={{ "--skeleton-columns": columns } as React.CSSProperties}
      role="status"
      aria-label={label}
    >
      {Array.from({ length: safeCount }, (_, index) => (
        <article className={styles.skeletonCard} key={index} aria-hidden="true">
          <div className={`${styles.skeletonBlock} ${styles.skeletonMedia}`} />
          <Skeleton height="13px" className={styles.skeletonBlock} />
          <Skeleton
            width="79%"
            height="11px"
            className={styles.skeletonBlock}
          />
          <div
            className={`${styles.skeletonBlock} ${styles.skeletonLineShort}`}
          />
        </article>
      ))}
    </div>
  );
}
