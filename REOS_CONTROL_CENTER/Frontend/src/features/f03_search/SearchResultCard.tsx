import Image from "next/image";
import Link from "next/link";

import type {
  SearchCurrency,
  SearchEntityType,
  SearchIntent,
} from "./search.types";
import styles from "./SearchResultCard.module.css";

export type SearchResultCardData = {
  id: string;
  entityType: SearchEntityType;
  intent: SearchIntent;

  title: string;
  location: string;
  locality?: string;
  city?: string;
  country?: string;

  propertyType: string;
  price: string;
  priceValue?: number;
  currency?: SearchCurrency;
  pricePeriod: "total" | "monthly";

  area: string;
  areaValue?: number;
  bedrooms?: number;
  bathrooms?: number;

  image?: string;
  imageLabel?: string;
  verified?: boolean;

  projectName?: string;
  projectId?: string;
  builderName?: string;

  status?: string;
  statusFacet?: string;
  furnishingFacet?: string;
  possessionFacet?: string;
  amenities?: string[];

  href: string;
};

type SearchResultCardProps = Readonly<{
  property: SearchResultCardData;
  onSave?: (property: SearchResultCardData) => void;
  onCompare?: (property: SearchResultCardData) => void;
  saved?: boolean;
  compared?: boolean;
}>;

const placeholderImageStyle = {
  display: "grid",
  placeItems: "center",
  alignContent: "center",
  gap: 8,
  boxSizing: "border-box" as const,
  padding: 24,
  background: "linear-gradient(135deg, #eef1f4, #d7dee5)",
  color: "#34414d",
  textAlign: "center" as const,
};

const imageDisclosureStyle = {
  position: "absolute" as const,
  right: 8,
  bottom: 8,
  left: 8,
  width: "fit-content",
  maxWidth: "calc(100% - 16px)",
  padding: "5px 8px",
  borderRadius: 6,
  background: "rgba(255,255,255,0.94)",
  color: "#34414d",
  fontSize: 9,
  fontWeight: 700,
};

export default function SearchResultCard({
  property,
  onSave,
  onCompare,
  saved = false,
  compared = false,
}: SearchResultCardProps) {
  const isProperty = property.entityType === "property";

  return (
    <article className={styles.card}>
      <div className={styles.media}>
        <Link
          href={property.href}
          className={styles.imageLink}
          aria-label={`Open ${property.title}`}
        >
          {property.image ? (
            <Image
              src={property.image}
              width={1400}
              height={875}
              sizes="(max-width: 640px) 100vw, (max-width: 1000px) 50vw, 36vw"
              alt={`${property.imageLabel ?? "Illustrative preview image"} for ${property.title}; not verified property photography`}
              className={styles.image}
              loading="lazy"
            />
          ) : (
            <div
              className={styles.image}
              role="img"
              aria-label={`Media is not connected for ${property.title}`}
              style={placeholderImageStyle}
            >
              <strong>
                {property.entityType === "project"
                  ? "PROJECT PREVIEW"
                  : "HOMIO PREVIEW"}
              </strong>

              <span style={{ fontSize: 11 }}>
                Media not connected
              </span>
            </div>
          )}
        </Link>

        {property.image ? (
          <span style={imageDisclosureStyle}>
            Illustrative image — not actual verified property photography
          </span>
        ) : null}

        <div className={styles.badges}>
          {property.verified ? (
            <span className={styles.verified}>
              HOMIO Verified
            </span>
          ) : null}

          {property.status ? (
            <span className={styles.status}>
              {property.status}
            </span>
          ) : null}
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.topRow}>
          <span className={styles.type}>
            {property.propertyType}
          </span>

          {(onSave || onCompare) ? (
            <div
              className={styles.quickActions}
              aria-label={`${isProperty ? "Property" : "Project"} actions`}
            >
              {onSave ? (
                <button
                  type="button"
                  className={`${styles.iconButton} ${
                    saved ? styles.active : ""
                  }`}
                  aria-label={
                    saved
                      ? "Remove from saved items"
                      : `Save ${isProperty ? "property" : "project"} for this session`
                  }
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
                      ? "Remove from comparison"
                      : `Compare ${isProperty ? "property" : "project"}`
                  }
                  aria-pressed={compared}
                  onClick={() => onCompare(property)}
                >
                  ⇄
                </button>
              ) : null}
            </div>
          ) : null}
        </div>

        <Link href={property.href} className={styles.title}>
          {property.title}
        </Link>

        <p className={styles.location}>
          {property.location}
        </p>

        {property.projectName ? (
          <p className={styles.project}>
            {property.projectName}
          </p>
        ) : null}

        <div className={styles.specs}>
          {property.bedrooms !== undefined ? (
            <span>{property.bedrooms} Bed</span>
          ) : null}

          {property.bathrooms !== undefined ? (
            <span>{property.bathrooms} Bath</span>
          ) : null}

          <span>
            {property.area &&
            !/preview information|not supplied/i.test(property.area)
              ? property.area
              : "Area not supplied"}
          </span>
        </div>

        <div className={styles.bottomRow}>
          <div>
            <strong className={styles.price}>
              {property.price || "Price not supplied"}
            </strong>

            <span className={styles.context}>
              {property.verified
                ? "Verified status supplied by the data source"
                : "Experience preview · not verified inventory"}
            </span>
          </div>

          <Link href={property.href} className={styles.view}>
            {isProperty ? "View property" : "View project"}
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </article>
  );
}
