import { Badge } from "@/components/ui/Badge";

import type { ProjectRecord } from "./project.types";

import styles from "./ProjectSummary.module.css";

type ProjectSummaryProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectSummary({
  project,
}: ProjectSummaryProps) {
  return (
    <section className={styles.card}>
      <div className={styles.topline}>
        <span className={styles.eyebrow}>
          {project.kindLabel}
        </span>

        <Badge
          tone={
            project.verified
              ? "success"
              : "warning"
          }
        >
          {project.verificationLabel}
        </Badge>
      </div>

      <h1>{project.name}</h1>

      <p className={styles.location}>
        {project.location}
      </p>

      <p className={styles.description}>
        {project.description}
      </p>

      <div className={styles.value}>
        <span>{project.priceContext}</span>
        <strong>{project.priceFrom}</strong>
      </div>

      <div className={styles.meta}>
        <div>
          <span>Configurations</span>
          <strong>
            {project.configurations.join(" · ")}
          </strong>
        </div>

        <div>
          <span>Area</span>
          <strong>{project.areaRange}</strong>
        </div>

        <div>
          <span>Possession</span>
          <strong>{project.possession}</strong>
        </div>

        <div>
          <span>Partner</span>
          <strong>{project.developerName}</strong>
        </div>
      </div>
    </section>
  );
}
