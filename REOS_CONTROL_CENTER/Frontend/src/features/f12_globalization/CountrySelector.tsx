
"use client";

import { useId } from "react";

import { COUNTRY_OPTIONS } from "./market-activation.constants";
import styles from "./MarketFieldSelectors.module.css";

type CountrySelectorProps = Readonly<{
  value: string;
  onChange: (countryCode: string) => void;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function CountrySelector({
  value,
  onChange,
  disabled = false,
  label = "Country",
  id,
}: CountrySelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-country-${generatedId}`;
  const hintId = `${selectId}-hint`;

  return (
    <div className={styles.fieldCard}>
      <div className={styles.fieldHead}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
        </label>
        <span className={styles.fieldHint}>Country / region</span>
      </div>

      <div className={styles.controlShell}>
        <span className={styles.leadingMark} aria-hidden="true">
          ◉
        </span>

        <select
          id={selectId}
          className={styles.select}
          value={value}
          disabled={disabled}
          onChange={(event) => onChange(event.currentTarget.value)}
          aria-describedby={hintId}
        >
          <option value="">Choose a country</option>
          {COUNTRY_OPTIONS.map((country) => (
            <option key={country.value} value={country.value}>
              {country.label}
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
        Countries are limited to the markets configured in HOMIO.
      </p>
    </div>
  );
}
