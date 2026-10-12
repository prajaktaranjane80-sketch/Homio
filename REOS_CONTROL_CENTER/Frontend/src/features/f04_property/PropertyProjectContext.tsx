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
          <span className={styles.eyebrow}>PROJECT CONTEXT</span>

          <h2>{property.projectName}</h2>

          <p>
            Explore the project reference attached to this property
            preview. This association does not independently verify
            a developer, project or property.
          </p>
        </div>

        {property.projectId ? (
          <Link
            href={`/project/${encodeURIComponent(property.projectId)}`}
            className={styles.linkButton}
          >
            View project
            <span aria-hidden="true">→</span>
          </Link>
        ) : null}
      </div>

      <div className={styles.grid}>
        <div>
          <span>Builder / developer</span>
          <strong>
            {property.builderName ?? "Not supplied in preview"}
          </strong>
        </div>

        <div>
          <span>Property type</span>
          <strong>{property.propertyType}</strong>
        </div>

        <div>
          <span>Location text</span>
          <strong>{property.location}</strong>
        </div>

        <div>
          <span>Availability context</span>
          <strong>{property.status}</strong>
        </div>
      </div>
    </section>
  );
}
