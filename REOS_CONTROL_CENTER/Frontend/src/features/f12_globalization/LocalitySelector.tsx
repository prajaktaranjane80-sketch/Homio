
"use client";

import { useId } from "react";

import styles from "./MarketFieldSelectors.module.css";

export type LocalityOption = Readonly<{
  value: string;
  label: string;
  description?: string;
}>;

type LocalitySelectorProps = Readonly<{
  value: string;
  options: readonly LocalityOption[];
  onChange: (locality: string) => void;
  marketLabel?: string;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function LocalitySelector({
  value,
  options,
  onChange,
  marketLabel = "selected city",
  disabled = false,
  label = "Locality / district",
  id,
}: LocalitySelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-locality-${generatedId}`;
  const hintId = `${selectId}-hint`;

  const safeOptions = options.filter(
    (option) =>
      option.value.trim().length > 0 &&
      option.label.trim().length > 0,
  );

  const validValue = safeOptions.some(
    (option) => option.value === value,
  )
    ? value
    : "";

  return (
    <div className={styles.fieldCard}>
      <div className={styles.fieldHead}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
        </label>
        <span className={styles.fieldHint}>Location refinement</span>
      </div>

      <div className={styles.controlShell}>
        <span className={styles.leadingMark} aria-hidden="true">
          ⌖
        </span>

        <select
          id={selectId}
          className={styles.select}
          value={validValue}
          disabled={disabled || safeOptions.length === 0}
          onChange={(event) => onChange(event.currentTarget.value)}
          aria-describedby={hintId}
        >
          <option value="">
            {safeOptions.length > 0
              ? "Choose a locality"
              : "Locality data not connected"}
          </option>

          {safeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.description
                ? `${option.label} — ${option.description}`
                : option.label}
            </option>
          ))}
        </select>

        <span className={styles.chevron} aria-hidden="true">
          <svg viewBox="0 0 16 16" width="16" height="16" fill="none">
            <path
              d="m3.5 5.75 4.5 4.5 4.5-4.5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </div>

      <p className={styles.footnote} id={hintId}>
        {safeOptions.length > 0
          ? `Showing supplied locality options for ${marketLabel}.`
          : "Localities will appear when a trusted location source provides options. No placeholder locations are presented as real."}
      </p>
    </div>
  );
}
