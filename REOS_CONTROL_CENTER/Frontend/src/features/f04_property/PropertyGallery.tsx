"use client";

import { useState } from "react";

import type { PropertyMedia } from "./property.types";
import styles from "./PropertyGallery.module.css";

type PropertyGalleryProps = Readonly<{
  media: PropertyMedia[];
}>;

function mediaTypeLabel(type: PropertyMedia["type"]): string {
  switch (type) {
    case "floor-plan":
      return "Floor plan placeholder";
    case "video":
      return "Video placeholder";
    case "virtual":
      return "Virtual experience placeholder";
    default:
      return "Illustrative media placeholder";
  }
}

export default function PropertyGallery({
  media,
}: PropertyGalleryProps) {
  const [active, setActive] = useState(0);
  const current = media[active];

  if (!current) {
    return (
      <section
        className={styles.section}
        aria-label="Property media"
      >
        <p>
          Property media has not been supplied for this preview.
        </p>
      </section>
    );
  }

  return (
    <section
      className={styles.section}
      aria-labelledby="property-gallery-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>PROPERTY MEDIA PREVIEW</span>
          <h2 id="property-gallery-title">Property media overview.</h2>
        </div>

        <span className={styles.counter}>
          {active + 1} / {media.length}
        </span>
      </div>

      <div className={styles.viewer}>
        <div className={`${styles.mainMedia} ${styles[current.type]}`}>
          <div className={styles.mediaGlow} />

          <span className={styles.mediaType}>
            {mediaTypeLabel(current.type)}
          </span>

          <strong>{current.label}</strong>
        </div>
      </div>

      <p
        style={{
          margin: "10px 2px 0",
          color: "#667085",
          fontSize: 11,
          lineHeight: 1.6,
        }}
      >
        Preview placeholders only. Actual property media is not supplied
        by the current property data. The current record contains labels,
        not actual property photography, verified floor plans, video or
        virtual-tour URLs.
      </p>

      <div className={styles.thumbs}>
        {media.map((item, index) => (
          <button
            key={item.id}
            type="button"
            className={`${styles.thumb} ${
              index === active ? styles.thumbActive : ""
            }`}
            onClick={() => setActive(index)}
            aria-label={`Select ${mediaTypeLabel(item.type)}: ${item.label}`}
            aria-pressed={index === active}
          >
            <span>{index + 1}</span>
            <strong>{item.label}</strong>
          </button>
        ))}
      </div>
    </section>
  );
}
