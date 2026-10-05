"use client";

import type { ChangeEvent } from "react";
import styles from "./SearchLocationField.module.css";

type SearchLocationFieldProps = Readonly<{
  value: string;
  onChange: (value: string) => void;
  intentLabel: string;
}>;

export default function SearchLocationField({
  value,
  onChange,
  intentLabel,
}: SearchLocationFieldProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    onChange(event.target.value);
  }

  return (
    <div className={styles.field}>
      <span className={styles.icon} aria-hidden="true">
        ◎
      </span>

      <div className={styles.content}>
        <label htmlFor="f03-search-location">
          {intentLabel} property search
        </label>

        <input
          id="f03-search-location"
          type="search"
          value={value}
          onChange={handleChange}
          placeholder="City, locality, project or landmark"
          autoComplete="off"
          spellCheck={false}
        />
      </div>
    </div>
  );
}
