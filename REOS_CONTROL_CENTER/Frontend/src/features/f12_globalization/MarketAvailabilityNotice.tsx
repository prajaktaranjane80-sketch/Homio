
import { useId } from "react";

import styles from "./MarketStates.module.css";

import {
  getMarketById,
  getMarketAvailability,
} from "./market-activation.utils";

type MarketAvailabilityNoticeProps = Readonly<{
  marketId: string;
  description?: string;
  compact?: boolean;
}>;

export default function MarketAvailabilityNotice({
  marketId,
  description,
  compact = false,
}: MarketAvailabilityNoticeProps) {
  const titleId = useId();
  const market = getMarketById(marketId);
  const availability = getMarketAvailability(marketId);

  const isActive = availability.activationState === "ACTIVE";
  const isBuilt = availability.activationState === "BUILT";

  return (
    <aside
      className={[
        styles.availabilityNotice,
        isActive ? styles.noticeActive : "",
        isBuilt ? styles.noticeBuilt : "",
        !market ? styles.noticeUnknown : "",
        compact ? styles.noticeCompact : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="note"
      aria-labelledby={titleId}
    >
      <span className={styles.noticeIcon} aria-hidden="true">
        {isActive ? "i" : "!"}
      </span>

      <div className={styles.noticeContent}>
        <div className={styles.noticeHeading}>
          <h3 className={styles.noticeTitle} id={titleId}>
            {market
              ? isActive
                ? `${market.city}: active market policy`
                : `${market.city}: built, not operational`
              : "Market status unavailable"}
          </h3>

          <span
            className={[
              styles.noticeLabel,
              isActive ? styles.noticeLabelActive : "",
              isBuilt ? styles.noticeLabelBuilt : "",
              !market ? styles.noticeLabelUnknown : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {availability.label}
          </span>
        </div>

        <p className={styles.noticeDescription}>
          {description ?? availability.serviceDisclosure}
        </p>
      </div>
    </aside>
  );
}
