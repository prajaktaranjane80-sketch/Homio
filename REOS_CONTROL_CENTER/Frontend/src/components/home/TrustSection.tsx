import Link from "next/link";
import styles from "./TrustSection.module.css";

const signals = [
  {
    title: "Clear source context",
    description:
      "Understand where the property or project information comes from.",
  },
  {
    title: "Useful property facts",
    description:
      "See the details that matter before moving into an enquiry.",
  },
  {
    title: "Journey continuity",
    description:
      "Your saved searches, properties and actions remain connected.",
  },
  {
    title: "Structured next steps",
    description:
      "Move from discovery to enquiry, visit and transaction with context.",
  },
];

export default function TrustSection() {
  return (
    <section id="trust" className={styles.section}>
      <div className="homio-container">
        <div className={styles.shell}>
          <div className={styles.intro}>
            <span className={styles.eyebrow}>TRUST AT HOMIO</span>

            <h2>Trust should be visible in the experience.</h2>

            <p>
              HOMIO is designed to surface useful signals and context before
              consumers take high-intent actions.
            </p>

            <Link href="/trust" className={styles.action}>
              Understand HOMIO trust
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className={styles.signalGrid}>
            {signals.map((signal, index) => (
              <article key={signal.title} className={styles.signal}>
                <div className={styles.top}>
                  <span className={styles.number}>
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <span className={styles.check} aria-hidden="true">
                    ✓
                  </span>
                </div>

                <h3>{signal.title}</h3>

                <p>{signal.description}</p>
              </article>
            ))}
          </div>
        </div>

        <div className={styles.bottom}>
          <span>
            <strong>Important:</strong> trust signals support informed
            decisions; they do not replace independent due diligence.
          </span>

          <Link href="/trust">Read trust principles</Link>
        </div>
      </div>
    </section>
  );
}
