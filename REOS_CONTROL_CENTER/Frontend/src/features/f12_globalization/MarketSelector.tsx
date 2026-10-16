
"use client";

import { useId } from "react";

import MarketStatus from "./MarketStatus";
import styles from "./MarketSelector.module.css";

import { MARKET_DEFINITIONS } from "./market-activation.constants";

import {
  getMarketById,
  normalizeMarketId,
} from "./market-activation.utils";

import type { MarketId } from "./market-activation.types";

type MarketSelectorProps = Readonly<{
  value: MarketId;
  onChange: (marketId: MarketId) => void;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function MarketSelector({
  value,
  onChange,
  disabled = false,
  label = "Choose your market",
  id,
}: MarketSelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-market-${generatedId}`;
  const policyId = `${selectId}-policy`;

  const normalizedMarketId = normalizeMarketId(value);
  const selectedMarket = getMarketById(normalizedMarketId);

  function handleChange(nextValue: string) {
    const safeMarketId = normalizeMarketId(nextValue);
    onChange(safeMarketId);
  }

  return (
    <section className={styles.selectorCard}>
      <div className={styles.selectorHeader}>
        <div className={styles.selectorTitleGroup}>
          <span className={styles.eyebrow}>
            HOMIO GLOBAL
          </span>

          <h2 className={styles.selectorTitle}>
            One platform. Local market context.
          </h2>

          <p className={styles.selectorDescription}>
            Set your preferred market to align location, currency and
            measurement conventions with the selected destination.
          </p>
        </div>

        <div className={styles.globeMark} aria-hidden="true">
          <svg
            viewBox="0 0 48 48"
            width="42"
            height="42"
            fill="none"
          >
            <circle cx="24" cy="24" r="18" stroke="currentColor" strokeWidth="1.4" />
            <ellipse cx="24" cy="24" rx="8" ry="18" stroke="currentColor" strokeWidth="1.2" />
            <path d="M7 24h34M11 15h26M11 33h26" stroke="currentColor" strokeWidth="1.2" />
          </svg>
        </div>
      </div>

      <div className={styles.selectorBody}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
          <span className={styles.fieldHint}>
            Choose a configured market
          </span>
        </label>

        <div className={styles.selectWrap}>
          <span className={styles.selectMarker} aria-hidden="true">
            ◎
          </span>

          <select
            id={selectId}
            value={normalizedMarketId}
            onChange={(event) => handleChange(event.target.value)}
            disabled={disabled}
            aria-describedby={policyId}
            className={styles.selectField}
          >
            {MARKET_DEFINITIONS.map((market) => (
              <option key={market.id} value={market.id}>
                {market.displayName}
                {market.activationState === "ACTIVE"
                  ? " — Active market policy"
                  : " — Built for future activation"}
              </option>
            ))}
          </select>

          <span className={styles.selectChevron} aria-hidden="true">
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

        <p className={styles.selectorFootnote} id={policyId}>
          Market activation is separate from user permissions and live
          service availability.
        </p>
      </div>

      <MarketStatus marketId={selectedMarket?.id ?? normalizedMarketId} />
    </section>
  );
}
