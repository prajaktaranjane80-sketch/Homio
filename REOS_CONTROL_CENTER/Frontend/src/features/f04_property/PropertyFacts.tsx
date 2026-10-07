import type { PropertyRecord } from "./property.types";
import styles from "./PropertyFacts.module.css";

type PropertyFactsProps = Readonly<{
  property: PropertyRecord;
}>;

const getFacts = (property: PropertyRecord) => [
  ["Property type", property.propertyType],
  ["Bedrooms", `${property.bedrooms} BHK`],
  ["Bathrooms", `${property.bathrooms}`],
  ["Built-up area", property.area],
  ["Parking", property.parking],
  ["Furnishing", property.furnishing],
  ["Possession", property.possession],
  ["Status", property.status],
];

export default function PropertyFacts({
  property,
}: PropertyFactsProps) {
  return (
    <section className={styles.section}>
      <span className={styles.eyebrow}>PROPERTY FACTS</span>

      <h2>At-a-glance specifications.</h2>

      <div className={styles.grid}>
        {getFacts(property).map(([label, value]) => (
          <div key={label} className={styles.fact}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
