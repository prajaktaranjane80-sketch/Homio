"use client";

import { useState } from "react";
import type { PropertyMedia } from "./property.types";
import styles from "./PropertyGallery.module.css";

type PropertyGalleryProps = Readonly<{
  media: PropertyMedia[];
}>;

export default function PropertyGallery({
  media,
}: PropertyGalleryProps) {
  const [active, setActive] = useState(0);

  const current = media[active];

  if (!current) {
    return null;
  }

  return (
    <section
      className={styles.section}
      aria-labelledby="property-gallery-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>PROPERTY MEDIA</span>
          <h2 id="property-gallery-title">See the property clearly.</h2>
        </div>

        <span className={styles.counter}>
          {active + 1} / {media.length}
        </span>
      </div>

      <div className={styles.viewer}>
        <div className={`${styles.mainMedia} ${styles[current.type]}`}>
          <div className={styles.mediaGlow} />
          <span className={styles.mediaType}>
            {current.type === "floor-plan"
              ? "Floor plan"
              : current.type === "video"
                ? "Video"
                : current.type === "virtual"
                  ? "Virtual experience"
                  : "Property view"}
          </span>
          <strong>{current.label}</strong>
        </div>
      </div>

      <div className={styles.thumbs}>
        {media.map((item, index) => (
          <button
            key={item.id}
            type="button"
            className={`${styles.thumb} ${
              index === active ? styles.thumbActive : ""
            }`}
            onClick={() => setActive(index)}
            aria-label={`Open ${item.label}`}
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
