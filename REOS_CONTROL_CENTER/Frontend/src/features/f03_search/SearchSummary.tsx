import { SEARCH_INTENT_LABELS } from "./search.constants";
import type { SearchState } from "./search.types";
import { countActiveFilters } from "./search.utils";
import styles from "./SearchSummary.module.css";

type SearchSummaryProps = Readonly<{
  state: SearchState;
}>;

export default function SearchSummary({ state }: SearchSummaryProps) {
  const locationLabel =
    state.location?.label?.trim() ||
    state.query ||
    "All available markets";

  const activeFilters =
    state.intent === "projects"
      ? 0
      : countActiveFilters(state.filters);

  const heading =
    state.intent === "projects"
      ? `Projects in ${locationLabel}`
      : `${SEARCH_INTENT_LABELS[state.intent]} properties in ${locationLabel}`;

  const viewLabel =
    state.intent === "projects"
      ? "Project list"
      : state.viewMode === "map"
        ? "Location preview — not a live map"
        : "List view";

  return (
    <section className={styles.summary} aria-label="Search summary">
      <div>
        <span className={styles.eyebrow}>SEARCH CONTEXT</span>
        <h2>{heading}</h2>
      </div>

      <div className={styles.meta}>
        <span>{activeFilters} active filters</span>
        <span aria-hidden="true">•</span>
        <span>{viewLabel}</span>
      </div>
    </section>
  );
}
