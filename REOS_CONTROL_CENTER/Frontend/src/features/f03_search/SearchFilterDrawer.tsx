"use client";

import SearchAdvancedFilters from "./SearchAdvancedFilters";
import type { SearchFilters } from "./search.types";
import styles from "./SearchFilterDrawer.module.css";

type SearchFilterDrawerProps = Readonly<{
  open: boolean;
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onApply: () => void;
  onClose: () => void;
}>;

export default function SearchFilterDrawer({
  open,
  filters,
  onChange,
  onApply,
  onClose,
}: SearchFilterDrawerProps) {
  if (!open) {
    return null;
  }

  const invalidBudget =
    filters.budgetMin !== undefined &&
    filters.budgetMax !== undefined &&
    filters.budgetMin > filters.budgetMax;

  const invalidArea =
    filters.areaMin !== undefined &&
    filters.areaMax !== undefined &&
    filters.areaMin > filters.areaMax;

  const invalidRange = invalidBudget || invalidArea;

  return (
    <div
      className={styles.overlay}
      role="presentation"
      onMouseDown={onClose}
    >
      <aside
        className={styles.drawer}
        role="dialog"
        aria-modal="true"
        aria-labelledby="search-filter-drawer-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>FILTERS</span>
            <h2 id="search-filter-drawer-title">
              Refine your search
            </h2>
          </div>

          <button
            type="button"
            className={styles.close}
            onClick={onClose}
            aria-label="Close filters without applying changes"
          >
            ×
          </button>
        </div>

        <div className={styles.content}>
          <SearchAdvancedFilters
            filters={filters}
            onChange={onChange}
          />

          {invalidBudget ? (
            <p
              role="alert"
              style={{
                padding: 12,
                color: "#9b1c1c",
                fontSize: 12,
              }}
            >
              Minimum budget cannot exceed maximum budget.
            </p>
          ) : null}

          {invalidArea ? (
            <p
              role="alert"
              style={{
                padding: 12,
                color: "#9b1c1c",
                fontSize: 12,
              }}
            >
              Minimum area cannot exceed maximum area.
            </p>
          ) : null}
        </div>

        <div className={styles.footer}>
          <button
            type="button"
            className={styles.secondary}
            onClick={onClose}
          >
            Cancel
          </button>

          <button
            type="button"
            className={styles.primary}
            onClick={onApply}
            disabled={invalidRange}
            style={
              invalidRange
                ? { opacity: 0.5, cursor: "not-allowed" }
                : undefined
            }
          >
            Apply filters
          </button>
        </div>
      </aside>
    </div>
  );
}
