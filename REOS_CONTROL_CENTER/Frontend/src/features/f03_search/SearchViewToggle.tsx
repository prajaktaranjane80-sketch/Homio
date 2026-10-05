"use client";

import type { SearchViewMode } from "./search.types";
import styles from "./SearchViewToggle.module.css";

type SearchViewToggleProps = Readonly<{
  value: SearchViewMode;
  onChange: (value: SearchViewMode) => void;
}>;

export default function SearchViewToggle({
  value,
  onChange,
}: SearchViewToggleProps) {
  return (
    <div className={styles.toggle} aria-label="Search result view">
      <button
        type="button"
        className={`${styles.button} ${
          value === "list" ? styles.active : ""
        }`}
        aria-pressed={value === "list"}
        onClick={() => onChange("list")}
      >
        List
      </button>

      <button
        type="button"
        className={`${styles.button} ${
          value === "map" ? styles.active : ""
        }`}
        aria-pressed={value === "map"}
        onClick={() => onChange("map")}
      >
        Map
      </button>
    </div>
  );
}
