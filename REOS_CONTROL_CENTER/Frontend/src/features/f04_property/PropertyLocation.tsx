import type { PropertyRecord } from "./property.types";
import styles from "./PropertyLocation.module.css";

type PropertyLocationProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertyLocation({
  property,
}: PropertyLocationProps) {
  return (
    <section className={styles.section}>
      <div>
        <span className={styles.eyebrow}>LOCATION</span>
        <h2>{property.location}</h2>
        <p>
          Understand the surrounding area and the property's wider
          city context before taking the next step.
        </p>
      </div>

      <div className={styles.map}>
        <div className={styles.marker}>
          <span>HOMIO</span>
          <strong>{property.locality}</strong>
        </div>
      </div>

      <div className={styles.nearby}>
        {property.nearby.map((item) => (
          <div key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
