import Link from "next/link";
import styles from "./SearchResultCard.module.css";

export type SearchResultCardData = {
  id: string;
  title: string;
  location: string;
  propertyType: string;
  price: string;
  area: string;
  bedrooms?: number;
  bathrooms?: number;
  image: string;
  verified?: boolean;
  projectName?: string;
  status?: string;
  href: string;
};

type SearchResultCardProps = Readonly<{
  property: SearchResultCardData;
  onSave?: (property: SearchResultCardData) => void;
  onCompare?: (property: SearchResultCardData) => void;
  saved?: boolean;
  compared?: boolean;
}>;

export default function SearchResultCard({
  property,
  onSave,
  onCompare,
  saved = false,
  compared = false,
}: SearchResultCardProps) {
  return (
    <article className={styles.card}>
      <div className={styles.media}>
        <Link href={property.href} className={styles.imageLink}>
          <img
            src={property.image}
            alt={property.title}
            className={styles.image}
            loading="lazy"
          />
        </Link>

        <div className={styles.badges}>
          {property.verified ? (
            <span className={styles.verified}>HOMIO Verified</span>
          ) : null}

          {property.status ? (
            <span className={styles.status}>{property.status}</span>
          ) : null}
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.topRow}>
          <span className={styles.type}>{property.propertyType}</span>

          <div className={styles.quickActions}>
            {onSave ? (
              <button
                type="button"
                className={`${styles.iconButton} ${
                  saved ? styles.active : ""
                }`}
                aria-label={saved ? "Remove from saved" : "Save property"}
                aria-pressed={saved}
                onClick={() => onSave(property)}
              >
                {saved ? "♥" : "♡"}
              </button>
            ) : null}

            {onCompare ? (
              <button
                type="button"
                className={`${styles.iconButton} ${
                  compared ? styles.active : ""
                }`}
                aria-label={
                  compared
                    ? "Remove property from compare"
                    : "Add property to compare"
                }
                aria-pressed={compared}
                onClick={() => onCompare(property)}
              >
                ⇄
              </button>
            ) : null}
          </div>
        </div>

        <Link href={property.href} className={styles.title}>
          {property.title}
        </Link>

        <p className={styles.location}>{property.location}</p>

        {property.projectName ? (
          <p className={styles.project}>{property.projectName}</p>
        ) : null}

        <div className={styles.specs}>
          {property.bedrooms !== undefined ? (
            <span>{property.bedrooms} Bed</span>
          ) : null}

          {property.bathrooms !== undefined ? (
            <span>{property.bathrooms} Bath</span>
          ) : null}

          <span>{property.area}</span>
        </div>

        <div className={styles.bottomRow}>
          <div>
            <strong className={styles.price}>{property.price}</strong>

            <span className={styles.context}>
              HOMIO property discovery
            </span>
          </div>

          <Link href={property.href} className={styles.view}>
            View property
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </article>
  );
}
