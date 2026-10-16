
"use client";

import { useId } from "react";

import styles from "./MarketFieldSelectors.module.css";

import { getMarketById } from "./market-activation.utils";

import type { MarketId } from "./market-activation.types";

type LanguageSelectorProps = Readonly<{
  marketId: MarketId;
  value: string;
  onChange: (language: string) => void;
  disabled?: boolean;
  label?: string;
  id?: string;
}>;

export default function LanguageSelector({
  marketId,
  value,
  onChange,
  disabled = false,
  label = "Preferred language",
  id,
}: LanguageSelectorProps) {
  const generatedId = useId();
  const selectId = id ?? `f12-language-${generatedId}`;
  const hintId = `${selectId}-hint`;

  const market = getMarketById(marketId);
  const languages = market?.supportedLanguages ?? [];
  const validValue = languages.includes(value) ? value : "";

  return (
    <div className={styles.fieldCard}>
      <div className={styles.fieldHead}>
        <label className={styles.fieldLabel} htmlFor={selectId}>
          {label}
        </label>
        <span className={styles.fieldHint}>Market-supported languages</span>
      </div>

      <div className={styles.controlShell}>
        <span className={styles.leadingMark} aria-hidden="true">
          文
        </span>

        <select
          id={selectId}
          className={styles.select}
          value={validValue}
          disabled={disabled || languages.length === 0}
          onChange={(event) => onChange(event.currentTarget.value)}
          aria-describedby={hintId}
        >
          <option value="">
            {languages.length > 0
              ? "Choose a language"
              : "No language options configured"}
          </option>

          {languages.map((language) => (
            <option key={language} value={language}>
              {language}
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
        {market
          ? `Options use the configured language list for ${market.displayName}. Full translated content requires localization support.`
          : "Choose a configured market before selecting a language."}
      </p>
    </div>
  );
}
