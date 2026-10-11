import Link from "next/link";
import styles from "./MarketIntelligence.module.css";

const markets = [
  {
    city: "Dubai",
    country: "UAE",
    trend: "Residential",
    value: "Market preview",
    detail: "Luxury · New projects · Investment",
    href: "/search?city=Dubai",
  },
  {
    city: "Singapore",
    country: "Singapore",
    trend: "Residential",
    value: "Market preview",
    detail: "Urban living · Prime districts · Commercial",
    href: "/search?city=Singapore",
  },
  {
    city: "London",
    country: "UK",
    trend: "Residential",
    value: "Market preview",
    detail: "Prime homes · Investment · Commercial",
    href: "/search?city=London",
  },
  {
    city: "Tokyo",
    country: "Japan",
    trend: "Residential",
    value: "Market preview",
    detail: "City homes · Prime districts · Investment",
    href: "/search?city=Tokyo",
  },
];

const signals = [
  {
    label: "Price context",
    value: "Preview only",
  },
  {
    label: "Rental context",
    value: "Not connected",
  },
  {
    label: "Project activity",
    value: "Preview only",
  },
  {
    label: "Locality insight",
    value: "Location context",
  },
];

export default function MarketIntelligence() {
  return (
    <section id="market-intelligence" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>MARKET INTELLIGENCE</span>

            <h2>See the market around the property.</h2>

            <p>
              Explore property-search context across global cities. Live
              market statistics, authoritative price trends and confirmed
              inventory are not connected in this frontend preview.
            </p>
          </div>

          <Link href="/search" className={styles.viewAll}>
            Explore property search
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.layout}>
          <div className={styles.markets}>
            {markets.map((market, index) => (
              <Link
                key={market.city}
                href={market.href}
                className={styles.market}
              >
                <div className={styles.marketIndex}>
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div className={styles.marketMain}>
                  <div className={styles.marketTitleRow}>
                    <div>
                      <span className={styles.country}>
                        {market.country}
                      </span>

                      <h3>{market.city}</h3>
                    </div>

                    <span className={styles.arrow} aria-hidden="true">
                      ↗
                    </span>
                  </div>

                  <div className={styles.marketMeta}>
                    <span>{market.trend}</span>
                    <span>{market.value}</span>
                    <span>{market.detail}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className={styles.insightPanel}>
            <div className={styles.panelTop}>
              <div>
                <span className={styles.panelEyebrow}>HOMIO VIEW</span>
                <h3>Context before action.</h3>
              </div>

              <span className={styles.panelIcon} aria-hidden="true">
                ◌
              </span>
            </div>

            <p>
              A property is more useful when its location, neighbourhood
              and project context are clear. The signals below describe
              this experience preview, not verified market data.
            </p>

            <div className={styles.signals}>
              {signals.map((signal) => (
                <div key={signal.label} className={styles.signal}>
                  <span>{signal.label}</span>
                  <strong>{signal.value}</strong>
                </div>
              ))}
            </div>

            <Link href="/search" className={styles.panelAction}>
              Open property search
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
