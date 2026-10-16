"use client";

import styles from "./PostProperty.module.css";
import type { PropertyListingIntent } from "./post-property.types";

type Props = Readonly<{
  value: PropertyListingIntent | "";
  onChange: (value: PropertyListingIntent) => void;
  disabled?: boolean;
}>;

const OPTIONS: readonly Readonly<{
  value: PropertyListingIntent;
  title: string;
  description: string;
}>[] = [
  { value: "sale", title: "For sale", description: "Property offered for purchase." },
  { value: "rent", title: "For rent", description: "Property offered for rental." },
  { value: "commercial", title: "Commercial", description: "Office, retail or other business property." },
];

export default function PostPropertyType({ value, onChange, disabled = false }: Props) {
  return (
    <section className={styles.postPanel}>
      <header className={styles.postPanelHeader}>
        <h2 className={styles.postPanelTitle}>What are you listing?</h2>
        <p className={styles.postPanelDescription}>Choose the primary listing intent. This does not publish or activate the listing.</p>
      </header>
      <div className={styles.postChoiceGrid}>
        {OPTIONS.map((option) => (
          <label className={styles.postChoice} key={option.value}>
            <input
              type="radio"
              name="post-property-intent"
              value={option.value}
              checked={value === option.value}
              disabled={disabled}
              onChange={() => onChange(option.value)}
            />
            <span className={styles.postChoiceText}>
              <span className={styles.postChoiceTitle}>{option.title}</span>
              <span className={styles.postChoiceDescription}>{option.description}</span>
            </span>
          </label>
        ))}
      </div>
    </section>
  );
}
