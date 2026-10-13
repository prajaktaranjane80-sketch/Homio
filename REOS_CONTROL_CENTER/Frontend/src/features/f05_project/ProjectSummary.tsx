import { Badge } from "@/components/ui/Badge";

import type { ProjectRecord } from "./project.types";

import styles from "./ProjectSummary.module.css";

type ProjectSummaryProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectSummary({
  project,
}: ProjectSummaryProps) {
  const verified = project.verified;

  return (
    <section className={styles.card} aria-label="Project summary">
      <div className={styles.topline}>
        <span className={styles.eyebrow}>
          {project.kindLabel}
        </span>

        <Badge tone={verified ? "success" : "warning"}>
          {project.verificationLabel}
        </Badge>
      </div>

      <h1>{project.name}</h1>

      <p className={styles.location}>{project.location}</p>

      <p className={styles.description}>{project.description}</p>

      <div className={styles.value}>
        <span>
          {verified
            ? project.priceContext
            : "PRICING · PENDING VERIFICATION"}
        </span>

        <strong>
          {verified ? project.priceFrom : "Preview only"}
        </strong>
      </div>

      <div className={styles.meta}>
        <div>
          <span>Configurations</span>
          <strong>
            {verified
              ? project.configurations.join(" · ")
              : "Available after verification"}
          </strong>
        </div>

        <div>
          <span>Area</span>
          <strong>
            {verified
              ? project.areaRange
              : "Available after verification"}
          </strong>
        </div>

        <div>
          <span>Possession</span>
          <strong>
            {verified
              ? project.possession
              : "Available after verification"}
          </strong>
        </div>

        <div>
          <span>Project source</span>
          <strong>
            {verified
              ? project.developerName
              : "Verification pending"}
          </strong>
        </div>
      </div>
    </section>
  );
}
