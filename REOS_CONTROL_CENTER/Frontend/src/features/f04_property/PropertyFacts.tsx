import type { PropertyRecord } from "./property.types";
import styles from "./PropertyFacts.module.css";

type PropertyFactsProps = Readonly<{
  property: PropertyRecord;
}>;

type PropertyFact = Readonly<{
  label: string;
  value: string;
}>;

function getFacts(property: PropertyRecord): PropertyFact[] {
  return [
    {
      label: "Property type",
      value: property.propertyType,
    },
    {
      label: "Bedrooms",
      value: String(property.bedrooms),
    },
    {
      label: "Bathrooms",
      value: String(property.bathrooms),
    },
    {
      label: "Area",
      value: property.area,
    },
    {
      label: "Parking",
      value: property.parking,
    },
    {
      label: "Furnishing",
      value: property.furnishing,
    },
    {
      label: "Possession",
      value: property.possession,
    },
    {
      label: "Status",
      value: property.status,
    },
  ];
}

export default function PropertyFacts({
  property,
}: PropertyFactsProps) {
  return (
    <section
      className={styles.section}
      aria-labelledby="property-facts-heading"
    >
      <span className={styles.eyebrow}>PROPERTY FACTS</span>

      <h2 id="property-facts-heading">
        At-a-glance specifications.
      </h2>

      <div className={styles.grid}>
        {getFacts(property).map(({ label, value }) => (
          <div key={label} className={styles.fact}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
