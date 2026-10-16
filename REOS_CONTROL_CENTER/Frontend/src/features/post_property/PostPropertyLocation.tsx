"use client";

import CountrySelector from "@/features/f12_globalization/CountrySelector";
import CitySelector from "@/features/f12_globalization/CitySelector";
import LocalitySelector from "@/features/f12_globalization/LocalitySelector";

import type { LocalityOption } from "@/features/f12_globalization/LocalitySelector";
import type { MarketId } from "@/features/f12_globalization/market-activation.types";

import styles from "./PostProperty.module.css";

type Props = Readonly<{
  countryCode: string;
  marketId: MarketId | "";
  locality: string;
  address: string;
  localityOptions: readonly LocalityOption[];
  onCountryChange: (countryCode: string) => void;
  onMarketChange: (marketId: MarketId | "") => void;
  onLocalityChange: (locality: string) => void;
  onAddressChange: (address: string) => void;
  disabled?: boolean;
}>;

export default function PostPropertyLocation({
  countryCode,
  marketId,
  locality,
  address,
  localityOptions,
  onCountryChange,
  onMarketChange,
  onLocalityChange,
  onAddressChange,
  disabled = false,
}: Props) {
  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>Where is the property?</h2>
        <p className={styles.postPanelDescription}>Select a configured market. Locality options must come from the approved location source.</p>
      </header>

      <div className={styles.postFieldGrid}>
        <CountrySelector
          value={countryCode}
          disabled={disabled}
          onChange={(next) => {
            onCountryChange(next);
            onMarketChange("");
            onLocalityChange("");
          }}
        />

        <CitySelector
          countryCode={countryCode}
          value={marketId}
          disabled={disabled || !countryCode}
          onChange={(next) => {
            onMarketChange(next);
            onLocalityChange("");
          }}
        />

        <LocalitySelector
          value={locality}
          options={localityOptions}
          disabled={disabled || !marketId}
          onChange={onLocalityChange}
          marketLabel={marketId || "selected city"}
        />

        <div className={`${styles.postField} ${styles.postFieldFull}`}>
          <label className={styles.postLabel} htmlFor="post-property-address">Address or location description</label>
          <textarea
            id="post-property-address"
            className={styles.postTextarea}
            value={address}
            onChange={(event) => onAddressChange(event.currentTarget.value)}
            disabled={disabled}
            maxLength={1000}
            placeholder="Enter a property location description"
          />
          <span className={styles.postHint}>Do not include access codes or other sensitive entry details.</span>
        </div>
      </div>

      <p className={styles.postNotice}>
        Selecting a city or country does not mean the market is operationally active or that property submission is approved for that market.
      </p>
    </section>
  );
}
