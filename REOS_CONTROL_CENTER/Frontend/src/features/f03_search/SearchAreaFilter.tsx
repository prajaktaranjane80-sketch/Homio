"use client";

import type { ChangeEvent } from "react";
import styles from "./SearchAreaFilter.module.css";

type SearchAreaFilterProps = Readonly<{
  min?: number;
  max?: number;
  onChange: (value: { min?: number; max?: number }) => void;
  unit?: string;
}>;

function parseArea(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const area = Number(value);

  return Number.isFinite(area) && area >= 0 ? area : undefined;
}

export default function SearchAreaFilter({
  min,
  max,
  onChange,
  unit = "sq ft",
}: SearchAreaFilterProps) {
  function handleMin(event: ChangeEvent<HTMLInputElement>) {
    onChange({
      min: parseArea(event.target.value),
      max,
    });
  }

  function handleMax(event: ChangeEvent<HTMLInputElement>) {
    onChange({
      min,
      max: parseArea(event.target.value),
    });
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Area</legend>

      <div className={styles.row}>
        <label className={styles.inputGroup}>
          <span>Minimum area</span>

          <div className={styles.inputWrap}>
            <input
              type="number"
              min="0"
              inputMode="numeric"
              value={min ?? ""}
              onChange={handleMin}
              placeholder="Min"
            />

            <span>{unit}</span>
          </div>
        </label>

        <label className={styles.inputGroup}>
          <span>Maximum area</span>

          <div className={styles.inputWrap}>
            <input
              type="number"
              min="0"
              inputMode="numeric"
              value={max ?? ""}
              onChange={handleMax}
              placeholder="Max"
            />

            <span>{unit}</span>
          </div>
        </label>
      </div>
    </fieldset>
  );
}
