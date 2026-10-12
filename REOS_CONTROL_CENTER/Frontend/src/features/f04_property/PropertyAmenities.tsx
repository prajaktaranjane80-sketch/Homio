import type { PropertyRecord } from "./property.types";
import styles from "./PropertyAmenities.module.css";

type PropertyAmenitiesProps = Readonly<{
  property: PropertyRecord;
}>;

function isPlaceholder(value: string): boolean {
  return /preview information|not supplied|not connected|unavailable/i.test(
    value.trim(),
  );
}

export default function PropertyAmenities({
  property,
}: PropertyAmenitiesProps) {
  const amenities = property.amenities.filter((amenity) => {
    const label = amenity.label.trim();
    const value = amenity.value.trim();

    return (
      label.toLowerCase() !== "amenities" &&
      !isPlaceholder(label) &&
      !isPlaceholder(value)
    );
  });

  return (
    <section
      className={styles.section}
      aria-labelledby="property-amenities-heading"
    >
      <span className={styles.eyebrow}>
        FEATURES & AMENITIES
      </span>

      <h2 id="property-amenities-heading">
        Designed for everyday living.
      </h2>

      {amenities.length > 0 ? (
        <div className={styles.grid}>
          {amenities.map((amenity) => (
            <div
              key={`${amenity.label}:${amenity.value}`}
              className={styles.card}
            >
              <span className={styles.icon} aria-hidden="true">
                •
              </span>

              <div>
                <strong>{amenity.label}</strong>
                <span>{amenity.value}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className={styles.card} role="note">
          <span className={styles.icon} aria-hidden="true">
            i
          </span>

          <div>
            <strong>Amenity information not supplied</strong>
            <span>
              This preview does not contain usable amenity details.
              HOMIO will not invent facilities to fill this section.
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
