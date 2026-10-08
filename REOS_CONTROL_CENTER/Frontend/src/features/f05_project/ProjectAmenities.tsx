import type { ProjectRecord } from "./project.types";

import styles from "./ProjectAmenities.module.css";

type ProjectAmenitiesProps = Readonly<{
  project: ProjectRecord;
}>;

export default function ProjectAmenities({
  project,
}: ProjectAmenitiesProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            PROJECT FEATURES
          </span>

          <h2>
            See what shapes the project experience.
          </h2>
        </div>
      </div>

      <div className={styles.grid}>
        {project.amenities.map((amenity) => (
          <div
            key={amenity.label}
            className={styles.item}
          >
            <span>{amenity.label}</span>
            <strong>{amenity.value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
