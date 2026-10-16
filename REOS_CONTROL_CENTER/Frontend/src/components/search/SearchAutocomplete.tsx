"use client";

import SearchSuggestionGroup from "./SearchSuggestionGroup";
import styles from "./SearchExperience.module.css";
import type { SearchSuggestion } from "./SearchExperience.types";

type Props = Readonly<{
  query: string;
  onQueryChange: (value: string) => void;
  suggestions?: readonly SearchSuggestion[];
  recent?: readonly SearchSuggestion[];
  popular?: readonly SearchSuggestion[];
  onSelect?: (suggestion: SearchSuggestion) => void;
}>;

export default function SearchAutocomplete({
  query,
  onQueryChange,
  suggestions = [],
  recent = [],
  popular = [],
  onSelect,
}: Props) {
  const trimmed = query.trim();

  const matchingSuggestions = trimmed
    ? suggestions.filter((item) =>
        `${item.title} ${item.description ?? ""}`
          .toLocaleLowerCase()
          .includes(trimmed.toLocaleLowerCase()),
      )
    : [];

  return (
    <div>
      <label className={styles.searchInputShell}>
        <span aria-hidden="true">⌕</span>
        <input
          className={styles.searchInput}
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.currentTarget.value)}
          placeholder="City, locality, project or property"
          autoComplete="off"
          spellCheck={false}
          aria-label="Search HOMIO"
        />
      </label>

      <div className={styles.searchSuggestions}>
        {trimmed ? (
          matchingSuggestions.length > 0 ? (
            <SearchSuggestionGroup
              heading="Suggestions"
              suggestions={matchingSuggestions}
              onSelect={onSelect}
            />
          ) : (
            <p className={styles.searchEmpty}>
              No supplied suggestions match this query. Submit your search to
              check the configured search experience.
            </p>
          )
        ) : (
          <>
            <SearchSuggestionGroup
              heading="Recent searches"
              suggestions={recent}
              onSelect={onSelect}
            />
            <SearchSuggestionGroup
              heading="Popular searches"
              suggestions={popular}
              onSelect={onSelect}
            />
          </>
        )}
      </div>
    </div>
  );
}
