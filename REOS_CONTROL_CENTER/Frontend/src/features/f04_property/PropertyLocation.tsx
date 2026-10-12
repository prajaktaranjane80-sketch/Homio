import type { PropertyRecord } from "./property.types";
import styles from "./PropertyLocation.module.css";

type PropertyLocationProps = Readonly<{
  property: PropertyRecord;
}>;

function isPlaceholder(value: string): boolean {
  return /preview information|not supplied|not connected|unavailable/i.test(
    value.trim(),
  );
}

export default function PropertyLocation({
  property,
}: PropertyLocationProps) {
  const nearby = property.nearby.filter((item) => {
    const label = item.label.trim();
    const value = item.value.trim();

    return (
      label.toLowerCase() !== "location context" &&
      !isPlaceholder(label) &&
      !isPlaceholder(value)
    );
  });

  return (
    <section
      className={styles.section}
      aria-labelledby="property-location-heading"
    >
      <div>
        <span className={styles.eyebrow}>
          LOCATION PREVIEW
        </span>

        <h2 id="property-location-heading">
          {property.location}
        </h2>

        <p>
          This section displays the location text available in the
          current experience preview. It does not establish exact
          coordinates, confirm a physical address or calculate travel
          distances.
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

      <p className={styles.mapDisclosure}>
        A live map and distance calculations require authoritative
        coordinates. Coordinates are not inferred from a locality name.
      </p>

      {nearby.length > 0 ? (
        <div className={styles.nearby}>
          {nearby.map((item) => (
            <div key={`${item.label}:${item.value}`}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
      ) : (
        <p className={styles.nearbyEmpty} role="note">
          Nearby places and travel distances are not supplied in this
          preview. No proximity estimates have been invented.
        </p>
      )}
    </section>
  );
}
