
import styles from "./MarketSelector.module.css";

import { getMarketById } from "./market-activation.utils";

type MarketActivationBadgeProps = Readonly<{
  marketId: string;
}>;

export default function MarketActivationBadge({
  marketId,
}: MarketActivationBadgeProps) {
  const market = getMarketById(marketId);

  if (!market) {
    return (
      <span className={`${styles.statusBadge} ${styles.statusBadgeUnknown}`}>
        <span className={styles.statusDot} aria-hidden="true" />
        MARKET UNCONFIGURED
      </span>
    );
  }

  const isActive = market.activationState === "ACTIVE";

  return (
    <span
      className={[
        styles.statusBadge,
        isActive ? styles.statusBadgeActive : styles.statusBadgeBuilt,
      ].join(" ")}
      aria-label={
        isActive
          ? "Active market activation policy"
          : "Market built but not operationally active"
      }
    >
      <span className={styles.statusDot} aria-hidden="true" />
      {isActive ? "ACTIVE MARKET" : "BUILT · NOT LIVE"}
    </span>
  );
}
