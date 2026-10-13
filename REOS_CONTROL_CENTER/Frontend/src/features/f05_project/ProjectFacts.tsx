
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
  const facts = project.verified
    ? project.facts.filter(
        (fact) =>
          fact.label.trim().length > 0 &&
          fact.value.trim().length > 0 &&
          !isUnavailableValue(fact.value),
      )
    : [];

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
          {project.verified
            ? `${project.locality}, ${project.city}`
            : "Verification pending"}
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
            {project.verified
              ? "No verified project facts are available for display. Missing information will not be filled with assumed figures."
              : "This experience preview does not contain verified project facts. Location, configuration, area, possession and inventory details will appear here only when authoritative project data is available."}
          </p>
        )}
      </div>
    </section>
  );
}
