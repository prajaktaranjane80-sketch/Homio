"use client";

import type { ChangeEvent } from "react";
import styles from "./SearchBuilderFilter.module.css";

type SearchBuilderFilterProps = Readonly<{
  value?: string;
  onChange: (value: string | undefined) => void;
}>;

export default function SearchBuilderFilter({
  value,
  onChange,
}: SearchBuilderFilterProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const nextValue = event.target.value.trimStart();

    onChange(nextValue ? nextValue : undefined);
  }

  function clear() {
    onChange(undefined);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Builder / developer</legend>

      <div className={styles.field}>
        <span className={styles.icon} aria-hidden="true">
          B
        </span>

        <input
          type="search"
          value={value ?? ""}
          onChange={handleChange}
          placeholder="Search builder or developer"
          autoComplete="off"
        />

        {value ? (
          <button
            type="button"
            className={styles.clear}
            onClick={clear}
            aria-label="Clear builder filter"
          >
            ×
          </button>
        ) : null}
      </div>
    </fieldset>
  );
}
