"use client";

import styles from "./SearchAmenityFilter.module.css";

type SearchAmenityFilterProps = Readonly<{
  value: string[];
  onChange: (value: string[]) => void;
}>;

const amenities = [
  "Parking",
  "Swimming Pool",
  "Gym",
  "Security",
  "Lift",
  "Garden",
  "Balcony",
  "Clubhouse",
  "Power Backup",
  "Pet Friendly",
  "Concierge",
  "CCTV",
];

export default function SearchAmenityFilter({
  value,
  onChange,
}: SearchAmenityFilterProps) {
  function toggle(amenity: string) {
    if (value.includes(amenity)) {
      onChange(value.filter((item) => item !== amenity));
      return;
    }

    onChange([...value, amenity]);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Amenities</legend>

      <div className={styles.grid}>
        {amenities.map((amenity) => {
          const selected = value.includes(amenity);

          return (
            <button
              key={amenity}
              type="button"
              aria-pressed={selected}
              className={`${styles.option} ${
                selected ? styles.selected : ""
              }`}
              onClick={() => toggle(amenity)}
            >
              <span
                className={styles.checkbox}
                aria-hidden="true"
              />

              <span>{amenity}</span>
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
