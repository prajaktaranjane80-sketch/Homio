"use client";

import styles from "./SearchPropertyType.module.css";

type SearchPropertyTypeProps = Readonly<{
  value: string[];
  onChange: (value: string[]) => void;
}>;

const propertyTypes = [
  "Apartment",
  "Villa",
  "Independent House",
  "Plot",
  "Office",
  "Retail",
  "Warehouse",
  "Land",
];

export default function SearchPropertyType({
  value,
  onChange,
}: SearchPropertyTypeProps) {
  function toggle(type: string) {
    if (value.includes(type)) {
      onChange(value.filter((item) => item !== type));
      return;
    }

    onChange([...value, type]);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Property type</legend>

      <div className={styles.grid}>
        {propertyTypes.map((type) => {
          const selected = value.includes(type);

          return (
            <button
              key={type}
              type="button"
              aria-pressed={selected}
              className={`${styles.option} ${
                selected ? styles.selected : ""
              }`}
              onClick={() => toggle(type)}
            >
              {type}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
