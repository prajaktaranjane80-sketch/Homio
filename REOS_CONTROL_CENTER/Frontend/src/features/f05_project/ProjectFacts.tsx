import type { ProjectRecord } from "./project.types";

import styles from "./ProjectFacts.module.css";

type ProjectFactsProps = Readonly<{
  project: ProjectRecord;
}>;

function isUnavailableValue(value: string): boolean {
  const normalized = value.trim().toLowerCase();

  const markers = [
    "preview",
    "not verified",
    "not supplied",
    "not connected",
    "not available",
    "not provided",
    "no verified data",
  ];

  return markers.some((marker) => normalized.includes(marker));
}

export default function ProjectFacts({
  project,
}: ProjectFactsProps) {
  const facts = project.facts.filter(
    (fact) =>
      fact.label.trim().length > 0 &&
      fact.value.trim().length > 0 &&
      !isUnavailableValue(fact.value),
  );

  return (
    <section
      className={styles.section}
      aria-labelledby="project-facts-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>PROJECT FACTS</span>

          <h2 id="project-facts-title">
            Understand the opportunity at a glance.
          </h2>
        </div>

        <span className={styles.context}>
          {project.locality}, {project.city}
        </span>
      </div>

      <div className={styles.grid}>
        {facts.length > 0 ? (
          facts.map((fact) => (
            <div key={fact.label} className={styles.item}>
              <span>{fact.label}</span>
              <strong>{fact.value}</strong>
            </div>
          ))
        ) : (
          <p className={styles.emptyState}>
            Project facts will appear here when verified project
            information is available. HOMIO will not fill gaps with
            assumed figures.
          </p>
        )}
      </div>
    </section>
  );
}
