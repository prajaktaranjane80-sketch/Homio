
"use client";

import { useId } from "react";

import styles from "./MarketStates.module.css";

type MarketUnavailableStateProps = Readonly<{
  title: string;
  description: string;
  eyebrow?: string;
  marketName?: string;
  compact?: boolean;
}>;

export default function MarketUnavailableState({
  title,
  description,
  eyebrow = "AVAILABILITY NOTICE",
  marketName,
  compact = false,
}: MarketUnavailableStateProps) {
  const headingId = useId();

  return (
    <section
      className={[
        styles.stateCard,
        styles.stateCardUnavailable,
        compact ? styles.stateCardCompact : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-labelledby={headingId}
      role="note"
    >
      <div className={styles.stateIcon} aria-hidden="true">
        <svg
          viewBox="0 0 24 24"
          width="23"
          height="23"
          fill="none"
        >
          <path
            d="M12 3.75 21 20.25H3L12 3.75Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path
            d="M12 9v4.5m0 3h.01"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <div className={styles.stateContent}>
        <div className={styles.stateOverline}>
          <span className={styles.stateOverlineMark} aria-hidden="true" />
          {eyebrow}
        </div>

        <h3 className={styles.stateTitle} id={headingId}>
          {title}
        </h3>

        {marketName ? (
          <p className={styles.stateMarket}>{marketName}</p>
        ) : null}

        <p className={styles.stateDescription}>{description}</p>

        <div className={styles.stateFoot}>
          <span className={styles.stateFootMark} aria-hidden="true">
            i
          </span>
          <span>
            Availability is determined by approved market policy and the
            relevant verified service—not by this screen alone.
          </span>
        </div>
      </div>
    </section>
  );
}
