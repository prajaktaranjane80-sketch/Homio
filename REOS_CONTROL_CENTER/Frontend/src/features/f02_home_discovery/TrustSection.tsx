import Link from "next/link";
import TrustSignalCard, {
  type TrustSignalCardData,
} from "./TrustSignalCard";
import TrustDisclaimer from "./TrustDisclaimer";
import styles from "./TrustSection.module.css";

const signals: TrustSignalCardData[] = [
  {
    number: "01",
    title: "Clear source context",
    description:
      "Understand where the property or project information comes from.",
  },
  {
    number: "02",
    title: "Useful property facts",
    description:
      "See the details that matter before moving into an enquiry.",
  },
  {
    number: "03",
    title: "Journey continuity",
    description:
      "Your saved searches, properties and actions remain connected.",
  },
  {
    number: "04",
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
            {signals.map((signal) => (
              <TrustSignalCard key={signal.number} signal={signal} />
            ))}
          </div>
        </div>

        <TrustDisclaimer />
      </div>
    </section>
  );
}
