import styles from "./SearchExperience.module.css";
import type { ActiveSearchFilter } from "./SearchExperience.types";

type Props = Readonly<{
  resultCount?: number;
  resultCountLabel?: string;
  filters: readonly ActiveSearchFilter[];
}>;

export default function SearchFilterSummary({
  resultCount,
  resultCountLabel,
  filters,
}: Props) {
  const safeCount =
    typeof resultCount === "number" &&
    Number.isFinite(resultCount) &&
    resultCount >= 0
      ? Math.floor(resultCount)
      : undefined;

  return (
    <div className={styles.filterSummary} aria-live="polite">
      {safeCount !== undefined ? (
        <span className={styles.filterCount}>
          {safeCount.toLocaleString()} results
        </span>
      ) : (
        <span className={styles.filterCount}>Results not available</span>
      )}
      {resultCountLabel ? (
        <span className={styles.filterSummaryText}>{resultCountLabel}</span>
      ) : null}
      {filters.length > 0 ? (
        <span className={styles.filterSummaryText}>
          {filters.length} active {filters.length === 1 ? "filter" : "filters"}
        </span>
      ) : null}
    </div>
  );
}
