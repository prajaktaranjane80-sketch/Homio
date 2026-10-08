import type { ProjectRecord } from "./project.types";

import styles from "./ProjectLocation.module.css";

type ProjectLocationProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectLocation({
  project,
}: ProjectLocationProps) {
  return (
    <section className={styles.section}>
      <div className={styles.left}>
        <span className={styles.eyebrow}>LOCATION</span>

        <h2>{project.location}</h2>

        <p>
          Project context should help the consumer understand not just the
          address, but the opportunity around it.
        </p>

        <div className={styles.nearby}>
          {project.nearby.map((item) => (
            <div key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
      </div>

      <div
        className={styles.map}
        role="img"
        aria-label={`Location preview for ${project.location}`}
      >
        <div className={styles.pin}>
          <span>HOMIO</span>
          <strong>{project.locality}</strong>
          <small>Location preview</small>
        </div>
      </div>
    </section>
  );
}
