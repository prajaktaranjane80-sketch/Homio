import Link from "next/link";

import { getAllPropertyPreviews } from "./property-preview-catalog";
import type { PropertyRecord } from "./property.types";
import styles from "./SimilarProperties.module.css";

type SimilarPropertiesProps = Readonly<{
  property: PropertyRecord;
}>;

export default function SimilarProperties({
  property,
}: SimilarPropertiesProps) {
  const similar = getAllPropertyPreviews()
    .filter(
      (item) =>
        item.id !== property.id &&
        item.city.trim().toLowerCase() ===
          property.city.trim().toLowerCase(),
    )
    .slice(0, 3);

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>SIMILAR DISCOVERY</span>
          <h2>More properties worth exploring.</h2>
        </div>

        <span className={styles.context}>
          Around {property.locality}
        </span>
      </div>

      {similar.length > 0 ? (
        <div className={styles.grid}>
          {similar.map((item) => (
            <article key={item.id} className={styles.card}>
              <div className={styles.media}>
                <span>PROPERTY EXPERIENCE PREVIEW</span>
              </div>

              <div className={styles.body}>
                <span className={styles.type}>
                  Preview · not verified
                </span>

                <h3>{item.title}</h3>
                <p>{item.location}</p>

                <div className={styles.meta}>
                  <strong>{item.price}</strong>
                  <span>{item.area}</span>
                </div>

                <Link href={`/property/${encodeURIComponent(item.id)}`}>
                  View property →
                </Link>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p
          style={{
            padding: 18,
            border: "1px solid #e5e9ee",
            borderRadius: 12,
            color: "#667085",
            fontSize: 13,
            lineHeight: 1.6,
          }}
        >
          No other same-city property previews are currently available.
          HOMIO has not substituted unrelated locations to fill this section.
        </p>
      )}
    </section>
  );
}
