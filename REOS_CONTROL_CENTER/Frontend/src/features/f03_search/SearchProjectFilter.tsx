"use client";

import type { ChangeEvent } from "react";
import styles from "./SearchProjectFilter.module.css";

type SearchProjectFilterProps = Readonly<{
  value?: string;
  onChange: (value: string | undefined) => void;
}>;

export default function SearchProjectFilter({
  value,
  onChange,
}: SearchProjectFilterProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const nextValue = event.target.value.trimStart();

    onChange(nextValue ? nextValue : undefined);
  }

  function clear() {
    onChange(undefined);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Project</legend>

      <div className={styles.field}>
        <span className={styles.icon} aria-hidden="true">
          #
        </span>

        <input
          type="search"
          value={value ?? ""}
          onChange={handleChange}
          placeholder="Search by project name"
          autoComplete="off"
        />

        {value ? (
          <button
            type="button"
            className={styles.clear}
            onClick={clear}
            aria-label="Clear project filter"
          >
            ×
          </button>
        ) : null}
      </div>
    </fieldset>
  );
}
