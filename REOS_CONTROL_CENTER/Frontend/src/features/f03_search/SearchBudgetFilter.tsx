"use client";

import type { ChangeEvent } from "react";

import { SEARCH_CURRENCIES } from "./search.constants";
import type { SearchCurrency } from "./search.types";
import styles from "./SearchBudgetFilter.module.css";

type SearchBudgetFilterProps = Readonly<{
  min?: number;
  max?: number;
  currency: SearchCurrency;
  onChange: (value: {
    min?: number;
    max?: number;
    currency: SearchCurrency;
  }) => void;
}>;

function parseAmount(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const amount = Number(value);

  return Number.isFinite(amount) && amount >= 0
    ? amount
    : undefined;
}

export default function SearchBudgetFilter({
  min,
  max,
  currency,
  onChange,
}: SearchBudgetFilterProps) {
  function handleMinChange(event: ChangeEvent<HTMLInputElement>) {
    onChange({
      min: parseAmount(event.target.value),
      max,
      currency,
    });
  }

  function handleMaxChange(event: ChangeEvent<HTMLInputElement>) {
    onChange({
      min,
      max: parseAmount(event.target.value),
      currency,
    });
  }

  function handleCurrencyChange(
    event: ChangeEvent<HTMLSelectElement>,
  ) {
    onChange({
      min,
      max,
      currency: event.target.value as SearchCurrency,
    });
  }

  const currencySymbol =
    SEARCH_CURRENCIES.find((item) => item.value === currency)?.symbol ??
    currency;

  return (
    <fieldset className={styles.fieldset}>
      <legend>Budget</legend>

      <label className={styles.inputGroup} style={{ marginBottom: 12 }}>
        <span>Budget currency</span>

        <select
          value={currency}
          onChange={handleCurrencyChange}
          style={{
            width: "100%",
            minHeight: 44,
            padding: "0 12px",
            border: "1px solid #e2e5ea",
            borderRadius: 10,
            background: "#fff",
            color: "#17212b",
            font: "inherit",
          }}
        >
          {SEARCH_CURRENCIES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>

      <div className={styles.row}>
        <label className={styles.inputGroup}>
          <span>Minimum</span>

          <div className={styles.inputWrap}>
            <span>{currencySymbol}</span>
            <input
              type="number"
              min="0"
              step="any"
              inputMode="decimal"
              value={min ?? ""}
              onChange={handleMinChange}
              placeholder="No minimum"
              aria-label={`Minimum budget in ${currency}`}
            />
          </div>
        </label>

        <span className={styles.separator} aria-hidden="true">
          to
        </span>

        <label className={styles.inputGroup}>
          <span>Maximum</span>

          <div className={styles.inputWrap}>
            <span>{currencySymbol}</span>
            <input
              type="number"
              min="0"
              step="any"
              inputMode="decimal"
              value={max ?? ""}
              onChange={handleMaxChange}
              placeholder="No maximum"
              aria-label={`Maximum budget in ${currency}`}
            />
          </div>
        </label>
      </div>

      <p
        style={{
          margin: "10px 0 0",
          color: "#667085",
          fontSize: 11,
          lineHeight: 1.5,
        }}
      >
        Enter the full amount in the selected currency. For example,
        ₹2 crore is 20000000 INR. Unknown or unpriced preview records
        are not treated as price matches.
      </p>
    </fieldset>
  );
}
