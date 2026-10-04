import Link from "next/link";
import styles from "./WhyHomio.module.css";

const pillars = [
  {
    number: "01",
    title: "One connected journey",
    description:
      "Discovery, research, enquiry, visits and transactions are designed to work together.",
  },
  {
    number: "02",
    title: "Brokerage at the center",
    description:
      "HOMIO is built around its own brokerage relationship, not a marketplace of competing brokers.",
  },
  {
    number: "03",
    title: "Context before action",
    description:
      "Property, project, locality and market information help consumers make better decisions.",
  },
  {
    number: "04",
    title: "Built for global markets",
    description:
      "The experience is designed for international residential, commercial and investment journeys.",
  },
];

export default function WhyHomio() {
  return (
    <section id="why-homio" className={styles.section}>
      <div className="homio-container">
        <div className={styles.header}>
          <div>
            <span className={styles.eyebrow}>WHY HOMIO</span>

            <h2>Real estate should feel simpler.</h2>

            <p>
              HOMIO combines discovery, intelligence and brokerage into one
              connected experience built around the consumer journey.
            </p>
          </div>

          <Link href="/about" className={styles.aboutLink}>
            About HOMIO
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className={styles.grid}>
          {pillars.map((pillar) => (
            <article key={pillar.number} className={styles.card}>
              <span className={styles.number}>{pillar.number}</span>

              <h3>{pillar.title}</h3>

              <p>{pillar.description}</p>
            </article>
          ))}
        </div>

        <div className={styles.statement}>
          <span className={styles.quoteMark}>“</span>

          <div>
            <p>
              From finding a property to completing a transaction, every step
              should feel like part of the same journey.
            </p>

            <span>— The HOMIO experience principle</span>
          </div>
        </div>
      </div>
    </section>
  );
}
