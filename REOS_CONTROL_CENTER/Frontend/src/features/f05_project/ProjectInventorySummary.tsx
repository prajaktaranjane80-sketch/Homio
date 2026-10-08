import type { ProjectRecord } from "./project.types";

import styles from "./ProjectInventorySummary.module.css";

type ProjectInventorySummaryProps = Readonly<{
  summary: ProjectRecord["inventorySummary"];
}>;

export default function ProjectInventorySummary({
  summary,
}: ProjectInventorySummaryProps) {
  return (
    <section className={styles.section}>
      <div>
        <span className={styles.eyebrow}>
          INVENTORY SNAPSHOT
        </span>

        <h2>
          See what this project can open up.
        </h2>
      </div>

      <div className={styles.grid}>
        <div className={styles.item}>
          <span>Inventory</span>
          <strong>{summary.totalLabel}</strong>
        </div>

        <div className={styles.item}>
          <span>Residential</span>
          <strong>{summary.residentialLabel}</strong>
        </div>

        <div className={styles.item}>
          <span>Commercial</span>
          <strong>{summary.commercialLabel}</strong>
        </div>

        <div className={styles.item}>
          <span>Availability</span>
          <strong>{summary.availabilityLabel}</strong>
        </div>
      </div>
    </section>
  );
}
