
import MarketAvailabilityNotice from "./MarketAvailabilityNotice";
import MarketUnavailableState from "./MarketUnavailableState";
import styles from "./MarketStates.module.css";

import { getMarketById } from "./market-activation.utils";

import type { MarketId } from "./market-activation.types";

type MarketComingSoonProps = Readonly<{
  marketId: MarketId;
  description?: string;
}>;

export default function MarketComingSoon({
  marketId,
  description,
}: MarketComingSoonProps) {
  const market = getMarketById(marketId);

  if (!market) {
    return (
      <MarketUnavailableState
        title="This market is not configured"
        description="Choose a configured market. HOMIO will not infer market support from a city name alone."
        eyebrow="MARKET NOT CONFIGURED"
      />
    );
  }

  if (market.activationState === "ACTIVE") {
    return (
      <MarketAvailabilityNotice
        marketId={market.id}
        description={
          description ??
          "This market's activation policy is enabled. Individual services may still require verified integrations."
        }
      />
    );
  }

  return (
    <section
      className={styles.comingCard}
      aria-labelledby="f12-coming-title"
    >
      <div className={styles.comingAtmosphere} aria-hidden="true">
        <span className={styles.comingOrbit} />
        <span className={styles.comingOrbitInner} />
        <span className={styles.comingCore}>H</span>
      </div>

      <div className={styles.comingContent}>
        <div className={styles.comingTopline}>
          <span className={styles.comingEyebrow}>
            HOMIO GLOBAL EXPANSION
          </span>

          <span className={styles.comingBadge}>
            <span className={styles.comingBadgeDot} aria-hidden="true" />
            BUILT · NOT LIVE
          </span>
        </div>

        <h3 className={styles.comingTitle} id="f12-coming-title">
          {market.city}
          <span> is on the expansion roadmap.</span>
        </h3>

        <p className={styles.comingDescription}>
          {description ??
            `${market.displayName} is configured in the HOMIO market experience, but is not operationally active. Services will remain unavailable until formal activation and integration checks are complete.`}
        </p>

        <div className={styles.comingFooter}>
          <span className={styles.comingFooterMark} aria-hidden="true">
            ↗
          </span>
          <span>
            <strong>Designed for future activation</strong>
            <small>
              No live inventory, brokerage or service availability is implied.
            </small>
          </span>
        </div>
      </div>
    </section>
  );
}
