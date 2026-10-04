import Link from "next/link";
import styles from "./BrokerageCTA.module.css";

const journey = [
  {
    number: "01",
    title: "Discover",
    description: "Find the property, project or market that fits your intent.",
  },
  {
    number: "02",
    title: "Enquire",
    description: "Send your interest directly into the HOMIO journey.",
  },
  {
    number: "03",
    title: "Visit",
    description: "Move from digital discovery toward the right property visit.",
  },
  {
    number: "04",
    title: "Deal",
    description: "Continue through a structured HOMIO brokerage process.",
  },
];

export default function BrokerageCTA() {
  return (
    <section id="brokerage" className={styles.section}>
      <div className="homio-container">
        <div className={styles.shell}>
          <div className={styles.intro}>
            <span className={styles.eyebrow}>HOMIO BROKERAGE</span>

            <h2>
              When you are ready,
              <br />
              we take it further.
            </h2>

            <p>
              HOMIO brings discovery, enquiry, visits and transactions into one
              brokerage journey—without turning the consumer experience into a
              marketplace of competing brokers.
            </p>

            <div className={styles.actions}>
              <Link href="/search" className={styles.primary}>
                Find a property
                <span aria-hidden="true">↗</span>
              </Link>

              <Link href="/my" className={styles.secondary}>
                Continue my journey
              </Link>
            </div>

            <div className={styles.trust}>
              <span className={styles.trustIcon}>H</span>

              <div>
                <strong>One HOMIO brokerage relationship.</strong>
                <span>From discovery to the next real-world action.</span>
              </div>
            </div>
          </div>

          <div className={styles.journey}>
            <div className={styles.journeyHeader}>
              <span>THE HOMIO JOURNEY</span>
              <small>DISCOVERY → BROKERAGE</small>
            </div>

            <div className={styles.steps}>
              {journey.map((step, index) => (
                <div key={step.number} className={styles.step}>
                  <div className={styles.stepNumber}>{step.number}</div>

                  <div className={styles.stepContent}>
                    <h3>{step.title}</h3>
                    <p>{step.description}</p>
                  </div>

                  {index < journey.length - 1 && (
                    <div className={styles.connector} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.bottom}>
          <div>
            <span className={styles.bottomLabel}>READY WHEN YOU ARE</span>

            <strong>
              Start with a property. Let HOMIO handle the next step.
            </strong>
          </div>

          <Link href="/search" className={styles.bottomAction}>
            Start your HOMIO journey
          </Link>
        </div>
      </div>
    </section>
  );
}
