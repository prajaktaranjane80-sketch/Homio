"use client";

import CurrencySelector from "@/features/f12_globalization/CurrencySelector";
import type { CurrencyCode } from "@/features/f12_globalization/market-activation.types";

import styles from "./PostProperty.module.css";

type Props = Readonly<{
  askingPrice: string;
  currency: CurrencyCode;
  onPriceChange: (value: string) => void;
  onCurrencyChange: (currency: CurrencyCode) => void;
  disabled?: boolean;
}>;

export default function PostPropertyPricing({
  askingPrice,
  currency,
  onPriceChange,
  onCurrencyChange,
  disabled = false,
}: Props) {
  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Pricing</h2>
        <p className={styles.postPanelDescription}>Enter a source-provided price and its currency. No currency conversion is performed.</p>
      </header>

      <div className={styles.postFieldGrid}>
        <div className={styles.postField}>
          <label className={styles.postLabel} htmlFor="property-asking-price">Asking price</label>
          <input
            id="property-asking-price"
            className={styles.postInput}
            type="number"
            min="0"
            step="any"
            value={askingPrice}
            disabled={disabled}
            onChange={(event) => onPriceChange(event.currentTarget.value)}
          />
        </div>
        <CurrencySelector value={currency} onChange={onCurrencyChange} disabled={disabled} />
      </div>

      <p className={styles.postNotice}>
        This is a draft value supplied by the submitter. It is not a verified asking price, valuation, offer or market estimate.
      </p>
    </section>
  );
}
