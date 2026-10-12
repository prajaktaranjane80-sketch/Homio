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
    description:
      "The intended journey connects a consumer's interest with HOMIO brokerage.",
  },
  {
    number: "03",
    title: "Visit",
    description:
      "The planned workflow moves from digital discovery toward a property visit.",
  },
  {
    number: "04",
    title: "Deal",
    description:
      "A structured brokerage process is the intended next step.",
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
              HOMIO is designed to connect property discovery with brokerage.
              Actual enquiry submission, visit scheduling and transaction
              workflows must be connected before they can be treated as active.
            </p>

            <div className={styles.actions}>
              <Link href="/search" className={styles.primary}>
                Find a property
                <span aria-hidden="true">↗</span>
              </Link>

              <Link href="/#my-homio" className={styles.secondary}>
                Explore My HOMIO preview
              </Link>
            </div>

            <div className={styles.trust}>
              <span className={styles.trustIcon} aria-hidden="true">
                H
              </span>

              <div>
                <strong>One HOMIO brokerage relationship.</strong>
                <span>
                  A connected journey from discovery to the next real-world
                  action.
                </span>
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

                  {index < journey.length - 1 ? (
                    <div className={styles.connector} />
                  ) : null}
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
