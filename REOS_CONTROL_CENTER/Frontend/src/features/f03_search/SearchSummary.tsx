import { SEARCH_INTENT_LABELS } from "./search.constants";
import type { SearchState } from "./search.types";
import { countActiveFilters } from "./search.utils";
import styles from "./SearchSummary.module.css";

type SearchSummaryProps = Readonly<{
  state: SearchState;
}>;

export default function SearchSummary({ state }: SearchSummaryProps) {
  const intentLabel = SEARCH_INTENT_LABELS[state.intent];
  const locationLabel =
    state.location?.label ?? state.query ?? "All available markets";
  const activeFilters = countActiveFilters(state.filters);

  return (
    <section className={styles.summary} aria-label="Search summary">
      <div>
        <span className={styles.eyebrow}>SEARCH CONTEXT</span>
        <h2>
          {intentLabel} properties in {locationLabel}
        </h2>
      </div>

      <div className={styles.meta}>
        <span>{activeFilters} active filters</span>
        <span aria-hidden="true">•</span>
        <span>{state.viewMode === "map" ? "Map view" : "List view"}</span>
      </div>
    </section>
  );
}
