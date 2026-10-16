
"use client";

import { useId } from "react";

import { CURRENCY_OPTIONS } from "./market-activation.constants";
import styles from "./MarketFieldSelectors.module.css";

import type { CurrencyCode } from "./market-activation.types";

type CurrencySelectorProps = Readonly<{
  value: CurrencyCode;
  onChange: (currency: CurrencyCode) => void;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function CurrencySelector({
  value,
  onChange,
  disabled = false,
  label = "Display currency",
  id,
}: CurrencySelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-currency-${generatedId}`;
  const hintId = `${selectId}-hint`;

  return (
    <div className={styles.fieldCard}>
      <div className={styles.fieldHead}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
        </label>
        <span className={styles.fieldHint}>Presentation preference</span>
      </div>

      <div className={styles.controlShell}>
        <span className={styles.leadingMark} aria-hidden="true">
          ◈
        </span>

        <select
          id={selectId}
          className={styles.select}
          value={value}
          disabled={disabled}
          onChange={(event) => {
            const nextValue = CURRENCY_OPTIONS.find(
              (currency) => currency.value === event.currentTarget.value,
            );

            if (nextValue) onChange(nextValue.value);
          }}
          aria-describedby={hintId}
        >
          {CURRENCY_OPTIONS.map((currency) => (
            <option key={currency.value} value={currency.value}>
              {currency.symbol} {currency.label} ({currency.value})
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
        Changing the display currency does not convert prices or guarantee a live exchange rate.
      </p>
    </div>
  );
}
