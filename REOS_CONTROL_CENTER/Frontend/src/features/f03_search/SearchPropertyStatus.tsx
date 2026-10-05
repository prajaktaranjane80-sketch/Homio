"use client";

import styles from "./SearchPropertyStatus.module.css";

type SearchPropertyStatusProps = Readonly<{
  value: string[];
  onChange: (value: string[]) => void;
}>;

const statuses = [
  "Ready to move",
  "Under construction",
  "New launch",
  "Resale",
  "Pre-launch",
];

export default function SearchPropertyStatus({
  value,
  onChange,
}: SearchPropertyStatusProps) {
  function toggle(status: string) {
    if (value.includes(status)) {
      onChange(value.filter((item) => item !== status));
      return;
    }

    onChange([...value, status]);
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Property status</legend>

      <div className={styles.options}>
        {statuses.map((status) => {
          const selected = value.includes(status);

          return (
            <button
              key={status}
              type="button"
              aria-pressed={selected}
              className={`${styles.option} ${
                selected ? styles.selected : ""
              }`}
              onClick={() => toggle(status)}
            >
              <span
                className={styles.dot}
                aria-hidden="true"
              />

              {status}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
