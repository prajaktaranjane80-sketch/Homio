"use client";

import styles from "./SearchPossessionFilter.module.css";

type SearchPossessionFilterProps = Readonly<{
  value: string[];
  onChange: (value: string[]) => void;
}>;

const options = [
  "Ready now",
  "Within 3 months",
  "Within 6 months",
  "Within 12 months",
  "After 12 months",
];

export default function SearchPossessionFilter({
  value,
  onChange,
}: SearchPossessionFilterProps) {
  function toggle(option: string) {
    if (value.includes(option)) {
      onChange(value.filter((item) => item !== option));
      return;
    }

    onChange([...value, option]);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Possession</legend>

      <div className={styles.options}>
        {options.map((option) => {
          const selected = value.includes(option);

          return (
            <button
              key={option}
              type="button"
              aria-pressed={selected}
              className={`${styles.option} ${
                selected ? styles.selected : ""
              }`}
              onClick={() => toggle(option)}
            >
              <span className={styles.indicator} aria-hidden="true" />

              {option}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
