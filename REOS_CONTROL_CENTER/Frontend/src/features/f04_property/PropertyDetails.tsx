import type { PropertyRecord } from "./property.types";
import styles from "./PropertyDetails.module.css";

type PropertyDetailsProps = Readonly<{
  property: PropertyRecord;
}>;

function isPlaceholder(value: string): boolean {
  return /experience preview|verification pending|preview information|not supplied|not connected|unavailable/i.test(
    value.trim(),
  );
}

export default function PropertyDetails({
  property,
}: PropertyDetailsProps) {
  const highlights = property.highlights.filter(
    (highlight) => !isPlaceholder(highlight),
  );

  return (
    <section
      className={styles.section}
      aria-labelledby="property-details-heading"
    >
      <div className={styles.header}>
        <span className={styles.eyebrow}>
          PROPERTY DETAILS
        </span>

        <h2 id="property-details-heading">
          Everything important, in one view.
        </h2>
      </div>

      <p className={styles.description}>
        {property.description}
      </p>

      <div className={styles.highlightGrid}>
        {highlights.length > 0 ? (
          highlights.map((highlight) => (
            <div key={highlight} className={styles.highlight}>
              <span aria-hidden="true">•</span>
              <p>{highlight}</p>
            </div>
          ))
        ) : (
          <div className={styles.highlight}>
            <span aria-hidden="true">i</span>
            <p>
              No property highlights are supplied in this experience
              preview. No features have been added by the interface.
            </p>
          </div>
        )}
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
          <span>Project association</span>
          <strong>
            {property.projectName ??
              "Not supplied in this preview"}
          </strong>
        </div>
      </div>
    </section>
  );
}
