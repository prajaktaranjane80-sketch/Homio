"use client";

import type { ChangeEvent } from "react";
import styles from "./SearchBudgetFilter.module.css";

type SearchBudgetFilterProps = Readonly<{
  min?: number;
  max?: number;
  onChange: (value: { min?: number; max?: number }) => void;
  currency?: string;
}>;

function parseAmount(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const amount = Number(value);

  return Number.isFinite(amount) && amount >= 0 ? amount : undefined;
}

export default function SearchBudgetFilter({
  min,
  max,
  onChange,
  currency = "₹",
}: SearchBudgetFilterProps) {
  function handleMinChange(event: ChangeEvent<HTMLInputElement>) {
    onChange({
      min: parseAmount(event.target.value),
      max,
    });
  }

  function handleMaxChange(event: ChangeEvent<HTMLInputElement>) {
    onChange({
      min,
      max: parseAmount(event.target.value),
    });
  }

  return (
    <fieldset className={styles.fieldset}>
      <legend>Budget</legend>

      <div className={styles.row}>
        <label className={styles.inputGroup}>
          <span>Minimum</span>

          <div className={styles.inputWrap}>
            <span>{currency}</span>

            <input
              type="number"
              min="0"
              inputMode="numeric"
              value={min ?? ""}
              onChange={handleMinChange}
              placeholder="No minimum"
            />
          </div>
        </label>

        <span className={styles.separator} aria-hidden="true">
          to
        </span>

        <label className={styles.inputGroup}>
          <span>Maximum</span>

          <div className={styles.inputWrap}>
            <span>{currency}</span>

            <input
              type="number"
              min="0"
              inputMode="numeric"
              value={max ?? ""}
              onChange={handleMaxChange}
              placeholder="No maximum"
            />
          </div>
        </label>
      </div>
    </fieldset>
  );
}
