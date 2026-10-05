"use client";

import { SEARCH_SORT_OPTIONS } from "./search.constants";
import type { SearchSort } from "./search.types";
import styles from "./SearchSortBar.module.css";

type SearchSortBarProps = Readonly<{
  value: SearchSort;
  onChange: (value: SearchSort) => void;
}>;

export default function SearchSortBar({
  value,
  onChange,
}: SearchSortBarProps) {
  return (
    <label className={styles.wrapper}>
      <span>Sort by</span>

      <select
        value={value}
        onChange={(event) => onChange(event.target.value as SearchSort)}
        className={styles.select}
        aria-label="Sort search results"
      >
        {SEARCH_SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
