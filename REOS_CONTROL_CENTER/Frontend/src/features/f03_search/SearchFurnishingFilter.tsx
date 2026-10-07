"use client";

import styles from "./SearchFurnishingFilter.module.css";

type SearchFurnishingFilterProps = Readonly<{
  value: string[];
  onChange: (value: string[]) => void;
}>;

const options = ["Unfurnished", "Semi-furnished", "Fully furnished"];

export default function SearchFurnishingFilter({
  value,
  onChange,
}: SearchFurnishingFilterProps) {
  function toggle(option: string) {
    if (value.includes(option)) {
      onChange(value.filter((item) => item !== option));
      return;
    }

    onChange([...value, option]);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Furnishing</legend>

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
              {option}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
