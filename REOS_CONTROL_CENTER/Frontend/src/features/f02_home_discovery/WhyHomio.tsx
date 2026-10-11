import Link from "next/link";
import WhyHomioPillar, {
  type WhyHomioPillarData,
} from "./WhyHomioPillar";
import WhyHomioStatement from "./WhyHomioStatement";
import styles from "./WhyHomio.module.css";

const pillars: WhyHomioPillarData[] = [
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
            <WhyHomioPillar key={pillar.number} pillar={pillar} />
          ))}
        </div>

        <WhyHomioStatement />
      </div>
    </section>
  );
}
