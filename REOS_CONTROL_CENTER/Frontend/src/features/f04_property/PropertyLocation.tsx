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
        <span className={styles.eyebrow}>LOCATION PREVIEW</span>

        <h2>{property.location}</h2>

        <p>
          This section displays the location text available in the
          current preview record. It does not establish property
          coordinates or confirm a physical address.
        </p>
      </div>

      <div
        className={styles.map}
        role="img"
        aria-label={`Illustrative location placeholder for ${property.locality}; not a live geographic map`}
      >
        <div className={styles.marker}>
          <span>HOMIO PREVIEW</span>
          <strong>{property.locality}</strong>
          <small>Location placeholder · not a live map</small>
        </div>
      </div>

      <p
        style={{
          margin: 0,
          color: "#667085",
          fontSize: 11,
          lineHeight: 1.6,
        }}
      >
        A live map and distance calculations require authoritative
        coordinates. They are not inferred from the locality name.
      </p>

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
