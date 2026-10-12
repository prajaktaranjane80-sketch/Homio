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
      "Understand where property or project information should come from.",
  },
  {
    number: "02",
    title: "Useful property facts",
    description:
      "Review the details that matter before taking a high-intent action.",
  },
  {
    number: "03",
    title: "Journey continuity",
    description:
      "The planned experience keeps searches, properties and actions connected.",
  },
  {
    number: "04",
    title: "Structured next steps",
    description:
      "The intended workflow connects discovery to enquiry, visit and transaction.",
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
              This section previews the trust principles planned for HOMIO.
              It does not assert that any sample listing has passed
              ownership, identity or availability verification.
            </p>

            <span className={styles.action} aria-disabled="true">
              Trust workflow preview
            </span>
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
