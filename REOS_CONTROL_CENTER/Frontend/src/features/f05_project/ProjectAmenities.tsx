import type { ProjectRecord } from "./project.types";

import styles from "./ProjectAmenities.module.css";

type ProjectAmenitiesProps = Readonly<{
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

export default function ProjectAmenities({
  project,
}: ProjectAmenitiesProps) {
  const amenities = project.amenities.filter(
    (amenity) =>
      amenity.label.trim().length > 0 &&
      amenity.value.trim().length > 0 &&
      !isUnavailableValue(amenity.value),
  );

  return (
    <section
      className={styles.section}
      aria-labelledby="project-amenities-title"
    >
      <div className={styles.header}>
        <span className={styles.eyebrow}>PROJECT FEATURES</span>

        <h2 id="project-amenities-title">
          See what shapes the project experience.
        </h2>
      </div>

      <div className={styles.grid}>
        {amenities.length > 0 ? (
          amenities.map((amenity) => (
            <div key={amenity.label} className={styles.item}>
              <span>{amenity.label}</span>
              <strong>{amenity.value}</strong>
            </div>
          ))
        ) : (
          <p className={styles.emptyState}>
            Amenities have not been supplied by a verified project
            source yet. Confirmed features will appear here when
            authoritative information is connected.
          </p>
        )}
      </div>
    </section>
  );
}
