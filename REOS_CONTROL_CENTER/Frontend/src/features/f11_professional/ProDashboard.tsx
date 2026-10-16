
import Link from "next/link";

import {
  PRO_NAVIGATION,
} from "./pro.types";
import ProWorkspace from "./ProWorkspace";
import styles from "./ProWorkspace.module.css";

export default function ProDashboard() {
  const sections = PRO_NAVIGATION.filter(
    (item) => item.section !== "dashboard",
  );

  return (
    <ProWorkspace section="dashboard">
      <section aria-labelledby="pro-workspaces-heading">
        <div className={styles.sectionHeader}>
          <div>
            <h2
              id="pro-workspaces-heading"
              className={styles.sectionTitle}
            >
              Your workspaces
            </h2>

            <p className={styles.sectionDescription}>
              Access paths are prepared for the approved professional
              workflow. Each business capability remains unavailable until
              its server-side authorization and data source are verified.
            </p>
          </div>
        </div>

        <div className={styles.workspaceGrid}>
          {sections.map((item, index) => (
            <Link
              key={item.section}
              href={item.href}
              className={styles.workspaceCard}
              aria-label={`${item.label}: capability not connected`}
            >
              <div className={styles.workspaceCardTop}>
                <span className={styles.workspaceCode}>
                  PRO / {String(index + 1).padStart(2, "0")}
                </span>

                <span className={styles.workspaceStatus}>
                  Not connected
                </span>
              </div>

              <h3 className={styles.workspaceTitle}>{item.label}</h3>

              <p className={styles.workspaceDescription}>
                {item.description}
              </p>

              <span className={styles.workspaceFooter}>
                <span>Open workspace</span>
                <span className={styles.arrow} aria-hidden="true">
                  →
                </span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      <aside
        className={styles.capabilitySummary}
        aria-labelledby="pro-capability-summary"
      >
        <span className={styles.summaryMark} aria-hidden="true">
          i
        </span>

        <div className={styles.summaryText}>
          <h2
            id="pro-capability-summary"
            className={styles.summaryTitle}
          >
            Business data is intentionally unavailable in this preview
          </h2>

          <p className={styles.summaryDescription}>
            This screen does not estimate performance, invent records, or
            simulate successful actions. Lead, inventory, enquiry, visit,
            client, project, deal and document data must come from approved
            REOS services with authorization for the current user and record.
          </p>
        </div>
      </aside>

      <p className={styles.footerNote}>
        HOMIO Pro · Presentation layer only · No broker directory, broker
        comparison, broker bidding, lead auction or competing broker marketplace.
      </p>
    </ProWorkspace>
  );
}
