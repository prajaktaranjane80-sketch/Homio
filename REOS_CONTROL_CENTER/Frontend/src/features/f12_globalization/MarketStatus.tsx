
import MarketActivationBadge from "./MarketActivationBadge";
import styles from "./MarketSelector.module.css";

import { getMarketById, getMarketAvailability } from "./market-activation.utils";

type MarketStatusProps = Readonly<{
  marketId: string;
  compact?: boolean;
}>;

export default function MarketStatus({
  marketId,
  compact = false,
}: MarketStatusProps) {
  const market = getMarketById(marketId);
  const availability = getMarketAvailability(marketId);
  const isActive = availability.activationState === "ACTIVE";

  return (
    <section
      className={[
        styles.statusPanel,
        isActive ? styles.statusPanelActive : styles.statusPanelBuilt,
        compact ? styles.statusPanelCompact : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-labelledby="f12-market-status-title"
    >
      <div className={styles.statusPanelHeader}>
        <div className={styles.statusIcon} aria-hidden="true">
          {isActive ? "✓" : "↗"}
        </div>

        <div className={styles.statusHeading}>
          <span className={styles.eyebrow}>
            MARKET ACTIVATION
          </span>

          <h3 id="f12-market-status-title">
            {availability.title}
          </h3>
        </div>

        <MarketActivationBadge marketId={marketId} />
      </div>

      <p className={styles.statusDescription}>
        {availability.description}
      </p>

      {!compact ? (
        <div className={styles.marketMetadata}>
          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Country</span>
            <strong>{market?.country ?? "Not configured"}</strong>
          </div>

          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Display currency</span>
            <strong>{market?.currency ?? "—"}</strong>
          </div>

          <div className={styles.metadataItem}>
            <span className={styles.metadataLabel}>Area convention</span>
            <strong>
              {market?.areaUnit === "sqm" ? "Square metres" : "Square feet"}
            </strong>
          </div>
        </div>
      ) : null}

      <div className={styles.serviceDisclosure}>
        <span className={styles.disclosureMark} aria-hidden="true">
          i
        </span>
        <p>{availability.serviceDisclosure}</p>
      </div>
    </section>
  );
}
