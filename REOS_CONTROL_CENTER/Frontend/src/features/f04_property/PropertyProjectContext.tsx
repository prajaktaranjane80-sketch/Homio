import Link from "next/link";

import type { PropertyRecord } from "./property.types";

import styles from "./PropertyProjectContext.module.css";

type PropertyProjectContextProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyProjectContext({
  property,
}: PropertyProjectContextProps) {
  if (!property.projectName) {
    return null;
  }

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            PROJECT CONTEXT
          </span>

          <h2>{property.projectName}</h2>

          <p>
            Understand the wider project around this individual property.
          </p>
        </div>

        {property.projectId ? (
          <Link
            href={`/project/${property.projectId}`}
            className={styles.linkButton}
          >
            View project
            <span aria-hidden="true">→</span>
          </Link>
        ) : null}
      </div>

      <div className={styles.grid}>
        <div>
          <span>Builder / partner</span>
          <strong>
            {property.builderName ??
              "Authorized project partner"}
          </strong>
        </div>

        <div>
          <span>Property position</span>
          <strong>{property.propertyType}</strong>
        </div>

        <div>
          <span>Location</span>
          <strong>{property.location}</strong>
        </div>

        <div>
          <span>Availability</span>
          <strong>{property.status}</strong>
        </div>
      </div>
    </section>
  );
}
