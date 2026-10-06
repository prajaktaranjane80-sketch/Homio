import type { PropertyRecord } from "./property.types";
import styles from "./PropertyAmenities.module.css";

type PropertyAmenitiesProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyAmenities({
  property,
}: PropertyAmenitiesProps) {
  return (
    <section className={styles.section}>
      <span className={styles.eyebrow}>FEATURES & AMENITIES</span>
      <h2>Designed for everyday living.</h2>

      <div className={styles.grid}>
        {property.amenities.map((amenity) => (
          <div key={amenity.label} className={styles.card}>
            <span className={styles.icon}>•</span>
            <div>
              <strong>{amenity.label}</strong>
              <span>{amenity.value}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
