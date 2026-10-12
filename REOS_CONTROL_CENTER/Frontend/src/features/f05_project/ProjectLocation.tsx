import type { ProjectRecord } from "./project.types";

import styles from "./ProjectLocation.module.css";

type ProjectLocationProps = Readonly<{
  project: ProjectRecord;
}>;

function isPlaceholder(value: string): boolean {
  const normalized = value.trim().toLowerCase();

  return [
    "preview information",
    "not connected",
    "not supplied",
    "not verified",
    "preview only",
  ].some((placeholder) => normalized.includes(placeholder));
}

export default function ProjectLocation({
  project,
}: ProjectLocationProps) {
  const nearbyItems = project.nearby.filter(
    (item) => item.value.trim() && !isPlaceholder(item.value),
  );

  return (
    <section className={styles.section}>
      <div className={styles.left}>
        <span className={styles.eyebrow}>Location preview</span>

        <h2>{project.location}</h2>

        <p>
          Explore the project&apos;s location context. Exact coordinates,
          nearby distances and route guidance require a connected,
          authoritative location source.
        </p>

        <div className={styles.nearby}>
          {nearbyItems.length > 0 ? (
            nearbyItems.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))
          ) : (
            <div>
              <span>Nearby information</span>
              <strong>Not supplied by the current data source</strong>
            </div>
          )}
        </div>
      </div>

      <div
        className={styles.map}
        role="img"
        aria-label={`Illustrative location placeholder for ${project.location}. This is not a live map and has no verified coordinates.`}
      >
        <div className={styles.pin}>
          <span>HOMIO · LOCATION PREVIEW</span>
          <strong>{project.locality || project.city}</strong>
          <small>Illustrative graphic only · not a live map</small>
        </div>
      </div>
    </section>
  );
}
