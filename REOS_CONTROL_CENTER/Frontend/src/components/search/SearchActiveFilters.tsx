"use client";

import styles from "./SearchExperience.module.css";
import type { ActiveSearchFilter } from "./SearchExperience.types";

type Props = Readonly<{
  filters: readonly ActiveSearchFilter[];
  onRemove: (filterId: string) => void;
  onClearAll?: () => void;
  disabled?: boolean;
}>;

export default function SearchActiveFilters({
  filters,
  onRemove,
  onClearAll,
  disabled = false,
}: Props) {
  if (filters.length === 0) return null;

  return (
    <div className={styles.activeFilters} aria-label="Active search filters">
      {filters.map((filter) => (
        <span className={styles.filterChip} key={filter.id}>
          <span className={styles.filterChipLabel}>
            {filter.label}: {filter.value}
          </span>
          <button
            type="button"
            className={styles.filterRemove}
            aria-label={`Remove ${filter.label} filter`}
            disabled={disabled}
            onClick={() => onRemove(filter.id)}
          >
            ×
          </button>
        </span>
      ))}
      {onClearAll ? (
        <button
          type="button"
          className={styles.filterClear}
          disabled={disabled}
          onClick={onClearAll}
        >
          Clear all
        </button>
      ) : null}
    </div>
  );
}
