import Link from "next/link";
import styles from "./PropertyTools.module.css";

const tools = [
  {
    number: "01",
    title: "EMI Calculator",
    description:
      "Understand estimated monthly payments from property price, loan amount and tenure.",
    href: "/tools/emi-calculator",
    action: "Calculate EMI",
  },
  {
    number: "02",
    title: "Affordability",
    description:
      "Explore a realistic property budget based on income, savings and financing assumptions.",
    href: "/tools/affordability",
    action: "Check affordability",
  },
  {
    number: "03",
    title: "Property Valuation",
    description:
      "Build a starting view of property value using location, property type and key facts.",
    href: "/tools/property-valuation",
    action: "Explore valuation",
  },
  {
    number: "04",
    title: "Market Trends",
    description:
      "Understand price and rental movement across locations and property categories.",
    href: "/tools/market-trends",
    action: "View trends",
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
              Useful calculators and market tools sit alongside discovery, so
              research becomes part of the HOMIO experience instead of a
              separate destination.
            </p>
          </div>

          <Link href="/tools" className={styles.viewAll}>
            Explore all tools
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.grid}>
          {tools.map((tool) => (
            <Link key={tool.number} href={tool.href} className={styles.card}>
              <div className={styles.top}>
                <span className={styles.number}>{tool.number}</span>

                <span className={styles.arrow} aria-hidden="true">
                  ↗
                </span>
              </div>

              <h3>{tool.title}</h3>

              <p>{tool.description}</p>

              <span className={styles.action}>{tool.action}</span>
            </Link>
          ))}
        </div>

        <div className={styles.feature}>
          <div className={styles.featureText}>
            <span className={styles.featureEyebrow}>DECISION SUPPORT</span>

            <h3>Research first. Enquire when you are ready.</h3>

            <p>
              HOMIO tools are designed to support discovery without interrupting
              the consumer journey into brokerage.
            </p>
          </div>

          <div className={styles.featureActions}>
            <Link href="/tools" className={styles.primary}>
              Open HOMIO tools
            </Link>

            <Link href="/search" className={styles.secondary}>
              Continue property search
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
