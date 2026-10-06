import type { PropertyRecord } from "./property.types";
import styles from "./PropertyDetails.module.css";

type PropertyDetailsProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyDetails({
  property,
}: PropertyDetailsProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>PROPERTY DETAILS</span>
        <h2>Everything important, in one view.</h2>
      </div>

      <p className={styles.description}>{property.description}</p>

      <div className={styles.highlightGrid}>
        {property.highlights.map((highlight) => (
          <div key={highlight} className={styles.highlight}>
            <span>✓</span>
            <p>{highlight}</p>
          </div>
        ))}
      </div>

      <div className={styles.infoGrid}>
        <div>
          <span>Furnishing</span>
          <strong>{property.furnishing}</strong>
        </div>

        <div>
          <span>Possession</span>
          <strong>{property.possession}</strong>
        </div>

        <div>
          <span>Status</span>
          <strong>{property.status}</strong>
        </div>

        <div>
          <span>Project</span>
          <strong>
            {property.projectName ?? "Independent property"}
          </strong>
        </div>
      </div>
    </section>
  );
}
