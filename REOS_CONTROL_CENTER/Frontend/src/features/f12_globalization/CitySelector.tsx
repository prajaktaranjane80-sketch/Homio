
"use client";

import { useId } from "react";

import { MARKET_DEFINITIONS } from "./market-activation.constants";
import styles from "./MarketFieldSelectors.module.css";

import { isMarketId } from "./market-activation.utils";

import type { MarketId } from "./market-activation.types";

type CitySelectorProps = Readonly<{
  countryCode: string;
  value: MarketId | "";
  onChange: (marketId: MarketId | "") => void;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function CitySelector({
  countryCode,
  value,
  onChange,
  disabled = false,
  label = "City",
  id,
}: CitySelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-city-${generatedId}`;
  const hintId = `${selectId}-hint`;

  const cities = MARKET_DEFINITIONS.filter(
    (market) => market.countryCode === countryCode,
  );

  const availableMarketIds = new Set(cities.map((market) => market.id));
  const safeValue =
    value && availableMarketIds.has(value) ? value : "";

  return (
    <div className={styles.fieldCard}>
      <div className={styles.fieldHead}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
        </label>
        <span className={styles.fieldHint}>Configured destinations</span>
      </div>

      <div className={styles.controlShell}>
        <span className={styles.leadingMark} aria-hidden="true">
          ◎
        </span>

        <select
          id={selectId}
          className={styles.select}
          value={safeValue}
          disabled={disabled || cities.length === 0}
          onChange={(event) => {
            const nextValue = event.currentTarget.value;

            if (
              nextValue === "" ||
              (isMarketId(nextValue) && availableMarketIds.has(nextValue))
            ) {
              onChange(nextValue);
            }
          }}
          aria-describedby={hintId}
        >
          <option value="">
            {cities.length > 0
              ? "Choose a city"
              : "No city configured for this country"}
          </option>

          {cities.map((city) => (
            <option key={city.id} value={city.id}>
              {city.city}
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
        City options update according to the selected country.
      </p>
    </div>
  );
}
