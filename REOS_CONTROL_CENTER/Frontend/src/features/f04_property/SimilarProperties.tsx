import Link from "next/link";

import { getAllPropertyPreviews } from "./property-preview-catalog";
import type { PropertyRecord } from "./property.types";
import styles from "./SimilarProperties.module.css";

type SimilarPropertiesProps = Readonly<{
  property: PropertyRecord;
}>;

function normalize(value: string): string {
  return value.trim().toLocaleLowerCase();
}

export default function SimilarProperties({
  property,
}: SimilarPropertiesProps) {
  const currentCity = normalize(property.city);
  const currentCountry = normalize(property.country);
  const currentLocality = normalize(property.locality);

  const candidates =
    currentCity && currentCountry
      ? getAllPropertyPreviews()
          .filter(
            (item) =>
              item.id !== property.id &&
              normalize(item.city) === currentCity &&
              normalize(item.country) === currentCountry,
          )
          .map((item, order) => {
            const sameLocality =
              currentLocality.length > 0 &&
              normalize(item.locality) === currentLocality;

            const sameType =
              normalize(item.propertyType) ===
              normalize(property.propertyType);

            return {
              item,
              order,
              sameLocality,
              score:
                (sameLocality ? 4 : 0) +
                (sameType ? 2 : 0),
            };
          })
          .sort(
            (left, right) =>
              right.score - left.score ||
              left.order - right.order,
          )
      : [];

  const similar = candidates
    .slice(0, 3)
    .map((candidate) => candidate.item);

  const hasLocalityMatch = similar.some(
    (item) =>
      currentLocality.length > 0 &&
      normalize(item.locality) === currentLocality,
  );

  const contextLabel = hasLocalityMatch
    ? `Around ${property.locality}`
    : `Other previews in ${property.city}`;

  return (
    <section
      className={styles.section}
      aria-labelledby="similar-properties-heading"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            SIMILAR DISCOVERY
          </span>

          <h2 id="similar-properties-heading">
            More properties worth exploring.
          </h2>
        </div>

        <span className={styles.context}>
          {contextLabel}
        </span>
      </div>

      {similar.length > 0 ? (
        <div className={styles.grid}>
          {similar.map((item) => (
            <article key={item.id} className={styles.card}>
              <div className={styles.media}>
                <span>
                  PROPERTY EXPERIENCE PREVIEW
                </span>
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

                <Link
                  href={`/property/${encodeURIComponent(item.id)}`}
                  className={styles.view}
                  aria-label={`View ${item.title} property preview`}
                >
                  View property
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className={styles.emptyState} role="note">
          No other same-city property previews are currently available.
          HOMIO has not substituted unrelated locations to fill this
          section.
        </p>
      )}
    </section>
  );
}
