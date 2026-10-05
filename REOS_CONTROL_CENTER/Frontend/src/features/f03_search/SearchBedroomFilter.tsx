"use client";

import styles from "./SearchBedroomFilter.module.css";

type SearchBedroomFilterProps = Readonly<{
  value: number[];
  onChange: (value: number[]) => void;
}>;

const options = [1, 2, 3, 4, 5];

export default function SearchBedroomFilter({
  value,
  onChange,
}: SearchBedroomFilterProps) {
  function toggle(bedroom: number) {
    if (value.includes(bedroom)) {
      onChange(value.filter((item) => item !== bedroom));
      return;
    }

    onChange([...value, bedroom].sort((a, b) => a - b));
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Bedrooms</legend>

      <div className={styles.options}>
        {options.map((bedroom) => {
          const selected = value.includes(bedroom);

          return (
            <button
              key={bedroom}
              type="button"
              aria-pressed={selected}
              className={`${styles.option} ${
                selected ? styles.selected : ""
              }`}
              onClick={() => toggle(bedroom)}
            >
              {bedroom === 5 ? "5+" : bedroom} BHK
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
