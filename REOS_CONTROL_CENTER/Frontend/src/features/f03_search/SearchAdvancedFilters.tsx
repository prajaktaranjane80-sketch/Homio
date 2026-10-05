"use client";

import SearchAmenityFilter from "./SearchAmenityFilter";
import SearchAreaFilter from "./SearchAreaFilter";
import SearchBedroomFilter from "./SearchBedroomFilter";
import SearchBudgetFilter from "./SearchBudgetFilter";
import SearchBuilderFilter from "./SearchBuilderFilter";
import SearchFurnishingFilter from "./SearchFurnishingFilter";
import SearchPossessionFilter from "./SearchPossessionFilter";
import SearchProjectFilter from "./SearchProjectFilter";
import SearchPropertyStatus from "./SearchPropertyStatus";
import SearchPropertyType from "./SearchPropertyType";
import SearchVerificationFilter from "./SearchVerificationFilter";
import type { SearchFilters } from "./search.types";
import styles from "./SearchAdvancedFilters.module.css";

type SearchAdvancedFiltersProps = Readonly<{
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}>;

export default function SearchAdvancedFilters({
  filters,
  onChange,
}: SearchAdvancedFiltersProps) {
  function update(next: Partial<SearchFilters>) {
    onChange({
      ...filters,
      ...next,
    });
  }

  return (
    <section
      className={styles.section}
      aria-labelledby="advanced-search-filters"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>REFINE SEARCH</span>

          <h2 id="advanced-search-filters">Find a closer match.</h2>

          <p>
            Refine your HOMIO search using property, budget, availability and
            trust signals.
          </p>
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.card}>
          <SearchPropertyType
            value={filters.propertyTypes}
            onChange={(value) => update({ propertyTypes: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchBudgetFilter
            min={filters.budgetMin}
            max={filters.budgetMax}
            onChange={({ min, max }) =>
              update({
                budgetMin: min,
                budgetMax: max,
              })
            }
          />
        </div>

        <div className={styles.card}>
          <SearchBedroomFilter
            value={filters.bedrooms}
            onChange={(value) => update({ bedrooms: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchAreaFilter
            min={filters.areaMin}
            max={filters.areaMax}
            onChange={({ min, max }) =>
              update({
                areaMin: min,
                areaMax: max,
              })
            }
          />
        </div>

        <div className={styles.card}>
          <SearchPropertyStatus
            value={filters.propertyStatus}
            onChange={(value) => update({ propertyStatus: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchFurnishingFilter
            value={filters.furnishing}
            onChange={(value) => update({ furnishing: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchAmenityFilter
            value={filters.amenities}
            onChange={(value) => update({ amenities: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchProjectFilter
            value={filters.project}
            onChange={(value) => update({ project: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchBuilderFilter
            value={filters.builder}
            onChange={(value) => update({ builder: value })}
          />
        </div>

        <div className={styles.card}>
          <SearchPossessionFilter
            value={filters.possession}
            onChange={(value) => update({ possession: value })}
          />
        </div>

        <div className={`${styles.card} ${styles.fullWidth}`}>
          <SearchVerificationFilter
            value={filters.verifiedOnly ?? false}
            onChange={(value) => update({ verifiedOnly: value })}
          />
        </div>
      </div>
    </section>
  );
}
