
"use client";

import styles from "./PostProperty.module.css";
import type { PropertyAvailability } from "./post-property.types";

type Props = Readonly<{
  value: PropertyAvailability;
  availableFrom: string;
  onChange: (value: PropertyAvailability) => void;
  onDateChange: (value: string) => void;
  disabled?: boolean;
}>;

const OPTIONS: readonly Readonly<{
  value: PropertyAvailability;
  label: string;
}>[] = [
  { value: "available", label: "Submitter says available" },
  { value: "under_construction", label: "Under construction" },
  { value: "not_available", label: "Not currently available" },
  { value: "unknown", label: "Not confirmed" },
];

export default function PostPropertyAvailability({
  value,
  availableFrom,
  onChange,
  onDateChange,
  disabled = false,
}: Props) {
  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>
          Availability information
        </h2>
        <p className={styles.postPanelDescription}>
          Record the submitter&apos;s stated availability. It is not a live
          inventory confirmation.
        </p>
      </header>

      <div className={styles.postChoiceGrid}>
        {OPTIONS.map((option) => (
          <label className={styles.postChoice} key={option.value}>
            <input
              type="radio"
              name="post-property-availability"
              value={option.value}
              checked={value === option.value}
              disabled={disabled}
              onChange={() => onChange(option.value)}
            />
            <span className={styles.postChoiceText}>
              <span className={styles.postChoiceTitle}>
                {option.label}
              </span>
            </span>
          </label>
        ))}
      </div>

      <div className={styles.postField}>
        <label
          className={styles.postLabel}
          htmlFor="post-property-available-date"
        >
          Stated available-from date (optional)
        </label>
        <input
          id="post-property-available-date"
          className={styles.postInput}
          type="date"
          value={availableFrom}
          disabled={disabled}
          onChange={(event) => onDateChange(event.currentTarget.value)}
        />
      </div>

      <p className={styles.postNotice}>
        Availability must be revalidated by an authorized inventory service
        before being shown as current to buyers or renters.
      </p>
    </section>
  );
}
