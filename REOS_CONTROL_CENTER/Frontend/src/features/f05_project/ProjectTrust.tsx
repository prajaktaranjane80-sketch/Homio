import type { ProjectRecord } from "./project.types";

import styles from "./ProjectTrust.module.css";

type ProjectTrustProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectTrust({
  project,
}: ProjectTrustProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>
          TRUST & EVIDENCE
        </span>

        <span
          className={`${styles.badge} ${
            project.verified
              ? styles.verified
              : styles.pending
          }`}
        >
          {project.verificationLabel}
        </span>
      </div>

      <div className={styles.grid}>
        <div>
          <h2>Clear project context.</h2>

          <p>
            HOMIO presents project information with an explicit trust state
            rather than implying verification that has not been established.
          </p>
        </div>

        <div className={styles.boundary}>
          <span>Production rule</span>

          <strong>
            Verified REOS project and inventory capability remains
            authoritative.
          </strong>
        </div>
      </div>
    </section>
  );
}
