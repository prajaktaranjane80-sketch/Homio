import styles from "./SystemComponents.module.css";

type Props = Readonly<{
  marketName: string;
  state: "ACTIVE" | "BUILT" | "UNKNOWN";
  description: string;
}>;

export function MarketAvailabilityState({
  marketName,
  state,
  description,
}: Props) {
  const tone =
    state === "ACTIVE"
      ? styles.systemBadgeGood
      : state === "BUILT"
        ? styles.systemBadgeWarning
        : styles.systemBadge;

  const label =
    state === "ACTIVE"
      ? "ACTIVE MARKET POLICY"
      : state === "BUILT"
        ? "BUILT · NOT LIVE"
        : "STATUS UNKNOWN";

  return (
    <section className={styles.systemCard} aria-labelledby="market-state-title">
      <div className={styles.systemRow}>
        <span className={styles.systemIcon} aria-hidden="true">◎</span>
        <div>
          <span className={styles.systemEyebrow}>Market availability</span>
          <h2 className={styles.systemTitle} id="market-state-title">
            {marketName}
          </h2>
          <span className={`${styles.systemBadge} ${tone}`}>
            <span className={styles.systemDot} aria-hidden="true" />
            {label}
          </span>
        </div>
      </div>
      <p className={styles.systemDescription} style={{ marginTop: 14 }}>
        {description}
      </p>
      <p className={styles.systemFootnote}>
        Market policy is not proof of live inventory, authorized brokerage,
        confirmed visits or functioning transaction services.
      </p>
    </section>
  );
}
