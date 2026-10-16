"use client";

import { useState } from "react";

import CountrySelector from "./CountrySelector";
import CitySelector from "./CitySelector";
import LocalitySelector from "./LocalitySelector";
import CurrencySelector from "./CurrencySelector";
import UnitSelector from "./UnitSelector";
import LanguageSelector from "./LanguageSelector";
import MarketStatus from "./MarketStatus";

import {
  DEFAULT_MARKET_ID,
  MARKET_DEFINITIONS,
} from "./market-activation.constants";

import { getMarketById } from "./market-activation.utils";

import type {
  AreaUnit,
  CurrencyCode,
  MarketId,
} from "./market-activation.types";

import styles from "./MarketActivationWorkspace.module.css";

export default function MarketActivationWorkspace() {
  const [marketId, setMarketId] = useState<MarketId>(DEFAULT_MARKET_ID);
  const [currency, setCurrency] = useState<CurrencyCode>("INR");
  const [areaUnit, setAreaUnit] = useState<AreaUnit>("sqft");
  const [language, setLanguage] = useState("English");

  const market = getMarketById(marketId);

  function selectMarket(nextMarketId: MarketId | "") {
    if (!nextMarketId) return;

    const nextMarket = getMarketById(nextMarketId);
    if (!nextMarket) return;

    setMarketId(nextMarket.id);
    setCurrency(nextMarket.currency);
    setAreaUnit(nextMarket.areaUnit);
    setLanguage(nextMarket.supportedLanguages[0] ?? "English");
  }

  return (
    <section className={styles.workspace}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>F12 · GLOBAL MARKET CONTROL</span>
        <h1 className={styles.title}>One global platform. Clear local context.</h1>
        <p className={styles.description}>
          Choose a configured market and set display preferences. A selection
          changes presentation context; it does not authorize operations or
          prove that inventory and services are live.
        </p>
      </header>

      <div className={styles.layout}>
        <div className={styles.mainColumn}>
          <div className={styles.marketPanel}>
            <span className={styles.panelEyebrow}>01 / MARKET</span>
            <h2 className={styles.panelTitle}>Choose a market</h2>

            <div className={styles.fieldGrid}>
              <CountrySelector
                value={market?.countryCode ?? ""}
                onChange={(countryCode) => {
                  const firstMarket = MARKET_DEFINITIONS.find(
                    (item) => item.countryCode === countryCode,
                  );

                  if (firstMarket) selectMarket(firstMarket.id);
                }}
              />

              <CitySelector
                countryCode={market?.countryCode ?? ""}
                value={marketId}
                onChange={selectMarket}
              />
            </div>
          </div>

          <div className={styles.marketPanel}>
            <span className={styles.panelEyebrow}>02 / LOCAL PRESENTATION</span>
            <h2 className={styles.panelTitle}>Regional preferences</h2>
            <p className={styles.panelDescription}>
              These preferences do not convert numeric data or translate content automatically.
            </p>

            <div className={styles.fieldGrid}>
              <CurrencySelector value={currency} onChange={setCurrency} />
              <UnitSelector value={areaUnit} onChange={setAreaUnit} />
              <LanguageSelector
                marketId={marketId}
                value={language}
                onChange={setLanguage}
              />
              <LocalitySelector
                value=""
                options={[]}
                marketLabel={market?.displayName ?? "selected market"}
                disabled
                onChange={() => undefined}
              />
            </div>

            <div className={styles.preferencesSummary}>
              <span><strong>Market</strong>{market?.displayName ?? "Unknown"}</span>
              <span><strong>Currency preference</strong>{currency}</span>
              <span><strong>Area convention</strong>{areaUnit === "sqm" ? "Square metres" : "Square feet"}</span>
              <span><strong>Language preference</strong>{language}</span>
            </div>
          </div>
        </div>

        <aside className={styles.statusColumn}>
          <span className={styles.panelEyebrow}>03 / SERVICE READINESS</span>
          <MarketStatus marketId={marketId} />
          <p className={styles.disclosure}>
            Operational service readiness is independent of market-selection
            preferences. The relevant REOS service must verify each business
            capability separately.
          </p>
        </aside>
      </div>
    </section>
  );
}
