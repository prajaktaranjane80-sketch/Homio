import type { PropertyRecord } from "./property.types";
import styles from "./PropertySummary.module.css";

type PropertySummaryProps = Readonly<{
  property: PropertyRecord;
}>;

export default function PropertySummary({
  property,
}: PropertySummaryProps) {
  return (
    <section className={styles.section}>
      <div className={styles.topline}>
        <span className={styles.type}>{property.propertyType}</span>

        {property.verified ? (
          <span className={styles.verified}>
            {property.verificationLabel}
          </span>
        ) : null}
      </div>

      <h1>{property.title}</h1>

      <p className={styles.location}>
        {property.location} · {property.city}, {property.country}
      </p>

      <div className={styles.priceBlock}>
        <strong>{property.price}</strong>
        <span>{property.priceContext}</span>
      </div>

      <div className={styles.facts}>
        <div>
          <strong>{property.bedrooms}</strong>
          <span>Beds</span>
        </div>

        <div>
          <strong>{property.bathrooms}</strong>
          <span>Baths</span>
        </div>

        <div>
          <strong>{property.area}</strong>
          <span>Area</span>
        </div>

        <div>
          <strong>{property.parking}</strong>
          <span>Parking</span>
        </div>
      </div>
    </section>
  );
}
