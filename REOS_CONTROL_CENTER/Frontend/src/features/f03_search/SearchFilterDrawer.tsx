"use client";

import SearchAdvancedFilters from "./SearchAdvancedFilters";
import type { SearchFilters } from "./search.types";
import styles from "./SearchFilterDrawer.module.css";

type SearchFilterDrawerProps = Readonly<{
  open: boolean;
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onClose: () => void;
}>;

export default function SearchFilterDrawer({
  open,
  filters,
  onChange,
  onClose,
}: SearchFilterDrawerProps) {
  if (!open) {
    return null;
  }

  return (
    <div className={styles.overlay} role="presentation" onMouseDown={onClose}>
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
            <h2 id="search-filter-drawer-title">Refine your search</h2>
          </div>

          <button
            type="button"
            className={styles.close}
            onClick={onClose}
            aria-label="Close filters"
          >
            ×
          </button>
        </div>

        <div className={styles.content}>
          <SearchAdvancedFilters filters={filters} onChange={onChange} />
        </div>

        <div className={styles.footer}>
          <button type="button" className={styles.secondary} onClick={onClose}>
            Cancel
          </button>

          <button type="button" className={styles.primary} onClick={onClose}>
            Apply filters
          </button>
        </div>
      </aside>
    </div>
  );
}
