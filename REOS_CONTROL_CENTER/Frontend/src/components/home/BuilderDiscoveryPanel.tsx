import Link from "next/link";
import styles from "./BuilderDiscoveryPanel.module.css";

const signals = [
  "Project portfolio context",
  "Configurations and availability",
  "Location and market context",
  "Direct HOMIO project journey",
];

export default function BuilderDiscoveryPanel() {
  return (
    <aside className={styles.panel}>
      <span className={styles.eyebrow}>PROJECT DISCOVERY</span>

      <h3>A better way to evaluate new development.</h3>

      <p>
        Start from the project, then move through configurations, availability,
        location and the next HOMIO brokerage action.
      </p>

      <div className={styles.signals}>
        {signals.map((signal) => (
          <div key={signal} className={styles.signal}>
            <span>✓</span>
            <span>{signal}</span>
          </div>
        ))}
      </div>

      <Link href="/search?intent=projects" className={styles.action}>
        Start project discovery
        <span aria-hidden="true">↗</span>
      </Link>
    </aside>
  );
}
