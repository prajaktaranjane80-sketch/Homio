import type { TransactionProperty } from "./transaction.types";
import styles from "./TransactionWorkspace.module.css";

type Props = Readonly<{
  property: TransactionProperty;
}>;

export default function DealProperty({ property }: Props) {
  const facts = [
    property.bedrooms !== undefined
      ? `${property.bedrooms} bedrooms`
      : undefined,
    property.bathrooms !== undefined
      ? `${property.bathrooms} bathrooms`
      : undefined,
    property.areaValue !== undefined
      ? `${property.areaValue.toLocaleString("en")} ${property.areaUnit || ""}`.trim()
      : undefined,
  ].filter((item): item is string => Boolean(item));

  return (
    <section className={styles.panel} aria-labelledby="f10-property-title">
      <div className={styles.panelHeader}>
        <div>
          <p className={styles.eyebrow}>PROPERTY CONTEXT</p>
          <h2 className={styles.panelTitle} id="f10-property-title">
            Property
          </h2>
        </div>
        <span className={styles.sectionGlyph} aria-hidden="true">
          ⌂
        </span>
      </div>

      <div className={styles.propertyCard}>
        <div
          className={`${styles.propertyImage} ${
            property.imageUrl ? styles.propertyImageHasPhoto : ""
          }`}
          role={property.imageUrl ? "img" : undefined}
          aria-label={property.imageUrl ? property.title : undefined}
          style={
            property.imageUrl
              ? {
                  backgroundImage: `linear-gradient(180deg, transparent 40%, rgba(8, 17, 33, .58)), url("${property.imageUrl.replace(/"/g, "%22")}")`,
                }
              : undefined
          }
        >
          {!property.imageUrl ? (
            <span className={styles.propertyImagePlaceholder} aria-hidden="true">
              <svg viewBox="0 0 48 48" fill="none">
                <path
                  d="M7 22L24 8L41 22V40H29V29H19V40H7V22Z"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinejoin="round"
                />
              </svg>
              <span>Property image not supplied</span>
            </span>
          ) : null}

          {property.propertyType ? (
            <span className={styles.propertyTypeTag}>
              {property.propertyType}
            </span>
          ) : null}
        </div>

        <div className={styles.propertyBody}>
          <h3 className={styles.propertyTitle}>{property.title}</h3>
          <p className={styles.propertyLocation}>
            <span aria-hidden="true">⌖</span>
            {property.location}
          </p>

          {property.displayPrice ? (
            <p className={styles.propertyPrice}>{property.displayPrice}</p>
          ) : null}

          {facts.length > 0 ? (
            <ul className={styles.propertyFacts} aria-label="Property details">
              {facts.map((fact) => (
                <li className={styles.factPill} key={fact}>
                  {fact}
                </li>
              ))}
            </ul>
          ) : null}

          <p className={styles.helperText}>
            Property details are shown from the supplied transaction record.
          </p>
        </div>
      </div>
    </section>
  );
}
