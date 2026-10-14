import Link from "next/link";
import styles from "./PropertyTools.module.css";

const tools = [
  {
    number: "01",
    title: "EMI Calculator",
    description:
      "Preview how monthly payment estimates could fit into property discovery.",
  },
  {
    number: "02",
    title: "Affordability",
    description:
      "A concept for exploring a property budget using financing assumptions.",
  },
  {
    number: "03",
    title: "Property Valuation",
    description:
      "A preview of value context based on location, type and property facts.",
  },
  {
    number: "04",
    title: "Market Trends",
    description:
      "A concept for reviewing price and rental movement by location.",
  },
];

export default function PropertyTools() {
  return (
    <section id="tools" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>HOMIO TOOLS</span>

            <h2>Make better property decisions.</h2>

            <p>
              These cards show the planned tool experience. Calculations,
              valuations and market data are not active services in this
              homepage preview.
            </p>
          </div>

          <span className={styles.viewAll} aria-disabled="true">
            Tools experience preview
          </span>
        </div>

        <div className={styles.grid}>
          {tools.map((tool) => (
                <article
                  key={tool.number}
                  className={styles.card}
                >
              <div className={styles.top}>
                <span className={styles.number}>{tool.number}</span>
                <span className={styles.arrow} aria-hidden="true">
                  ◇
                </span>
              </div>

              <h3>{tool.title}</h3>
              <p>{tool.description}</p>

              <span className={styles.action}>
                Tool preview · not interactive
              </span>
            </article>
          ))}
        </div>

        <div className={styles.feature}>
          <div className={styles.featureText}>
            <span className={styles.featureEyebrow}>DECISION SUPPORT</span>

            <h3>Research first. Enquire when you are ready.</h3>

            <p>
              Tools should support decisions with transparent assumptions.
              No financial calculation or valuation is being performed by
              these preview cards.
            </p>
          </div>

          <div className={styles.featureActions}>
            <span className={styles.primary} aria-disabled="true">
              Tools preview only
            </span>

            <Link href="/search" className={styles.secondary}>
              Continue property search
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
