import type { ProjectRecord } from "./project.types";

import styles from "./ProjectFacts.module.css";

type ProjectFactsProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectFacts({
  project,
}: ProjectFactsProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            PROJECT FACTS
          </span>

          <h2>
            Understand the opportunity at a glance.
          </h2>
        </div>

        <span className={styles.context}>
          {project.locality}, {project.city}
        </span>
      </div>

      <div className={styles.grid}>
        {project.facts.map((fact) => (
          <div
            key={fact.label}
            className={styles.item}
          >
            <span>{fact.label}</span>
            <strong>{fact.value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
