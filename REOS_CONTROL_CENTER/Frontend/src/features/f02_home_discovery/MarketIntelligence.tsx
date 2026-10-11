import Link from "next/link";
import styles from "./MarketIntelligence.module.css";

const markets = [
  {
    city: "Dubai",
    country: "UAE",
    trend: "Residential",
    value: "Prime market",
    detail: "Luxury · New projects · Investment",
    href: "/market/dubai",
  },
  {
    city: "Singapore",
    country: "Singapore",
    trend: "Residential",
    value: "Core market",
    detail: "Urban living · Prime districts · Commercial",
    href: "/market/singapore",
  },
  {
    city: "London",
    country: "UK",
    trend: "Residential",
    value: "Prime market",
    detail: "Prime homes · Investment · Commercial",
    href: "/market/london",
  },
  {
    city: "Tokyo",
    country: "Japan",
    trend: "Residential",
    value: "Urban market",
    detail: "City homes · Prime districts · Investment",
    href: "/market/tokyo",
  },
];

const signals = [
  {
    label: "Price context",
    value: "Location-based",
  },
  {
    label: "Rental context",
    value: "Market-based",
  },
  {
    label: "Project activity",
    value: "Discovery signal",
  },
  {
    label: "Locality insight",
    value: "Area context",
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
              HOMIO connects property discovery with location and market
              context so you can understand where an opportunity sits before
              moving into an enquiry.
            </p>
          </div>

          <Link href="/market" className={styles.viewAll}>
            Explore markets
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
              A property is more useful when you can see the location,
              neighbourhood, project and market signals around it.
            </p>

            <div className={styles.signals}>
              {signals.map((signal) => (
                <div key={signal.label} className={styles.signal}>
                  <span>{signal.label}</span>
                  <strong>{signal.value}</strong>
                </div>
              ))}
            </div>

            <Link href="/market" className={styles.panelAction}>
              Open market intelligence
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
